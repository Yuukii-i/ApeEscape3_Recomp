#!/usr/bin/env python3
"""direct_calls.py - PERF-CG2 post-processor for static JAL direct calls.

Rewrites the exact 3-line DirectCall + "JAL" + `{ return; }` pattern in
recomp_source/*.cpp to `PS2_DCALL(target, fallthrough)` when `target` is a
known function start (`sub_<TARGET>_0x*.cpp` exists in the directory) and is
not in the runtime's special-cased skip list.

Usage: direct_calls.py [--dry-run] [--log PATH] [<dir>]
Default <dir> is `recomp_source`.
"""

import argparse
import os
import re
from collections import Counter

SUB_FILE_RE = re.compile(r"^sub_([0-9A-Fa-f]+)_0x[0-9A-Fa-f]+\.cpp$")

DCALL_LINE_RE = re.compile(
    r"^(\s*)if\s*\(!runtime->dispatchGuestBranch\(\s*rdram\s*,\s*ctx\s*,\s*"
    r"(0x[0-9A-Fa-f]+u)\s*,\s*(0x[0-9A-Fa-f]+u)\s*,\s*(0x[0-9A-Fa-f]+u)\s*,\s*"
    r'PS2Runtime::GuestBranchKind::DirectCall\s*,\s*"JAL"\s*\)\)\s*\{\s*$'
)
ANY_DIRECTCALL_JAL_RE = re.compile(
    r'dispatchGuestBranch\(.*PS2Runtime::GuestBranchKind::DirectCall,\s*"JAL"'
)
RETURN_RE = re.compile(r"^\s*return;\s*$")
RBRACE_RE = re.compile(r"^\s*\}\s*$")
PS2_DCALL_RE = re.compile(r"\bPS2_DCALL\(")
INCLUDE_DCALL_RE = re.compile(r'^\s*#\s*include\s+"ps2_dcall\.h"')
INCLUDE_RUNTIME_RE = re.compile(r'^\s*#\s*include\s+"ps2_runtime\.h"')
ANY_INCLUDE_RE = re.compile(r"^\s*#\s*include\b")

SKIP_EXACT = {0x001037E8, 0x0031A1B4, 0x0031A240}
SKIP_RANGE_LO = 0x00408000
SKIP_RANGE_HI = 0x00413000


def is_skipped_target(target: int) -> bool:
    if target in SKIP_EXACT:
        return True
    if SKIP_RANGE_LO <= target <= SKIP_RANGE_HI:
        return True
    return False


def collect_known_targets(root_dir: str) -> tuple[list[str], set[int]]:
    files: list[str] = []
    targets: set[int] = set()
    for name in sorted(os.listdir(root_dir)):
        if not name.endswith(".cpp"):
            continue
        files.append(name)
        m = SUB_FILE_RE.match(name)
        if m:
            targets.add(int(m.group(1), 16))
    return files, targets


def insert_include(lines: list[str]) -> list[str]:
    if any(INCLUDE_DCALL_RE.match(ln) for ln in lines):
        return lines

    insert_idx = None
    last_inc_idx = None
    for idx, ln in enumerate(lines):
        if INCLUDE_RUNTIME_RE.match(ln):
            insert_idx = idx + 1
            break
        if ANY_INCLUDE_RE.match(ln):
            last_inc_idx = idx + 1

    if insert_idx is None:
        insert_idx = last_inc_idx if last_inc_idx is not None else 0

    return lines[:insert_idx] + ['#include "ps2_dcall.h" // PERF-CG2'] + lines[insert_idx:]


def process_file(
    lines: list[str], known_targets: set[int], stats: Counter
) -> tuple[list[str], list[tuple[int, str, str]]]:
    out: list[str] = []
    changes: list[tuple[int, str, str]] = []
    n = len(lines)
    i = 0
    while i < n:
        ln = lines[i]
        if PS2_DCALL_RE.search(ln):
            stats["already_dcall"] += 1
            out.append(ln)
            i += 1
            continue

        m = DCALL_LINE_RE.match(ln)
        if not m:
            if ANY_DIRECTCALL_JAL_RE.search(ln):
                stats["skip_pattern_mismatch"] += 1
            out.append(ln)
            i += 1
            continue

        if i + 2 >= n or not RETURN_RE.match(lines[i + 1]) or not RBRACE_RE.match(lines[i + 2]):
            stats["skip_body_mismatch"] += 1
            out.append(ln)
            i += 1
            continue

        indent, target_lit, source_lit, fallthrough_lit = (
            m.group(1),
            m.group(2),
            m.group(3),
            m.group(4),
        )
        target = int(target_lit[:-1], 16)
        source = int(source_lit[:-1], 16)
        fallthrough = int(fallthrough_lit[:-1], 16)

        if fallthrough - 8 != source:
            stats["skip_source_mismatch"] += 1
            out.append(ln)
            i += 1
            continue

        if is_skipped_target(target):
            stats["skip_special_cased"] += 1
            out.append(ln)
            i += 1
            continue

        if target not in known_targets:
            stats["skip_unknown_target"] += 1
            out.append(ln)
            i += 1
            continue

        out.append(f"{indent}if (!PS2_DCALL({target_lit}, {fallthrough_lit})) {{")
        out.append(lines[i + 1])
        out.append(lines[i + 2])
        changes.append((i + 1, target_lit, fallthrough_lit))
        stats["rewritten_sites"] += 1
        i += 3

    if changes:
        out = insert_include(out)

    return out, changes


def main() -> int:
    parser = argparse.ArgumentParser(description="Rewrite static JAL DirectCall sites to PS2_DCALL.")
    parser.add_argument("dir", nargs="?", default="recomp_source", help="Directory containing *.cpp files")
    parser.add_argument("--dry-run", action="store_true", help="Report counts without modifying files")
    parser.add_argument(
        "--log",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "direct_calls.log"),
        help="Path to write change log when applying",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.dir):
        print(f"error: directory not found: {args.dir}")
        return 2

    files, known_targets = collect_known_targets(args.dir)
    stats = Counter()
    log_entries: list[str] = []

    for name in files:
        path = os.path.join(args.dir, name)
        with open(path, "rb") as f:
            raw = f.read()
        stats["files_scanned"] += 1

        eol = "\r\n" if b"\r\n" in raw else "\n"
        text = raw.decode("utf-8", errors="replace")
        trailing_eol = text.endswith(("\n", "\r"))
        lines = text.splitlines()

        new_lines, changes = process_file(lines, known_targets, stats)
        if not changes:
            continue

        stats["files_modified"] += 1
        for line_no, target_lit, fallthrough_lit in changes:
            log_entries.append(f"{name}:{line_no} target={target_lit} fallthrough={fallthrough_lit}")

        if not args.dry_run:
            new_text = eol.join(new_lines) + (eol if trailing_eol else "")
            with open(path, "wb") as f:
                f.write(new_text.encode("utf-8"))

    mode = "DRY-RUN" if args.dry_run else "APPLIED"
    print(f"[{mode}] files_scanned={stats['files_scanned']} known_targets={len(known_targets)}")
    print(f"[{mode}] files_modified={stats['files_modified']} rewritten_sites={stats['rewritten_sites']}")
    skipped_keys = sorted(k for k in stats if k.startswith("skip_") or k == "already_dcall")
    for k in skipped_keys:
        print(f"[{mode}] {k}={stats[k]}")

    if not args.dry_run:
        with open(args.log, "w", encoding="utf-8") as lf:
            lf.write(
                f"files_scanned={stats['files_scanned']} files_modified={stats['files_modified']} "
                f"rewritten_sites={stats['rewritten_sites']}\n"
            )
            for k in skipped_keys:
                lf.write(f"{k}={stats[k]}\n")
            for entry in log_entries:
                lf.write(entry + "\n")
        print(f"[{mode}] log={args.log}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
