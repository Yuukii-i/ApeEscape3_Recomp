#!/usr/bin/env python3
"""restrict_ctx.py - PERF-CG4 post-processor for __restrict locals.

For each generated function definition with parameter list
`(uint8_t* rdram, R5900Context* ctx, PS2Runtime *runtime)`, renames the
parameters to `rdram_in` / `ctx_in` and inserts `__restrict`-qualified locals
as the first statements of the body:
    uint8_t* __restrict rdram = rdram_in; R5900Context* __restrict ctx = ctx_in; // PERF-CG4

Usage: restrict_ctx.py [<recomp_source dir>] [--dry-run] [--log PATH]
"""

import argparse
import os
import re
from collections import Counter

MARKER = "// PERF-CG4"

# Matches function definitions with the exact (rdram, ctx, runtime) parameter list.
# Captures:
#   1: prefix up to '(' + whitespace
#   2: 'uint8_t* ' (pointer + spaces before rdram)
#   3: ', R5900Context* ' (between rdram and ctx)
#   4: ', PS2Runtime *runtime) {' (from after ctx through opening '{')
SIG_RE = re.compile(
    r"^([ \t]*(?:(?:static|inline)\s+)*void\s+(\w+)\s*\(\s*)"
    r"(uint8_t\s*\*\s*)rdram(\s*,\s*R5900Context\s*\*\s*)ctx"
    r"(\s*,\s*PS2Runtime\s*\*\s*runtime\s*\)\s*\{)",
    re.M,
)

# Matches already-transformed definitions for idempotency accounting.
ALREADY_SIG_RE = re.compile(
    r"^[ \t]*(?:(?:static|inline)\s+)*void\s+\w+\s*\(\s*"
    r"uint8_t\s*\*\s*rdram_in\s*,\s*R5900Context\s*\*\s*ctx_in\s*,\s*"
    r"PS2Runtime\s*\*\s*runtime\s*\)\s*\{",
    re.M,
)

# Unsafe-use patterns on a comment/string-stripped function body.
CTX_ASSIGN_RE = re.compile(
    r"(?<![A-Za-z0-9_>.])ctx\s*(?:[+\-*/%&|^]?=(?!=)|\+\+|--)|(?:--|\+\+)\s*ctx\b"
)
RDRAM_ASSIGN_RE = re.compile(
    r"(?<![A-Za-z0-9_>.])rdram\s*(?:[+\-*/%&|^]?=(?!=)|\+\+|--)|(?:--|\+\+)\s*rdram\b"
)
CTX_ADDR_RE = re.compile(r"(?<![A-Za-z0-9_])&\s*ctx\b(?!\s*(?:->|\[|\.))")
RDRAM_ADDR_RE = re.compile(r"(?<![A-Za-z0-9_])&\s*rdram\b(?!\s*(?:->|\[|\.))")

COMMENT_OR_STR_RE = re.compile(
    r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
)
BRACE_OR_SKIP_RE = re.compile(
    r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|([{}])',
)


def find_matching_brace(text: str, open_idx: int) -> int:
    """Return index of '}' matching '{' at open_idx, or -1 if unclosed."""
    depth = 1
    for m in BRACE_OR_SKIP_RE.finditer(text, open_idx + 1):
        brace = m.group(1)
        if brace == "{":
            depth += 1
        elif brace == "}":
            depth -= 1
            if depth == 0:
                return m.start()
    return -1


def strip_comments_and_strings(body: str) -> str:
    """Replace comments and string/char literals with spaces for safe grepping."""
    return COMMENT_OR_STR_RE.sub(" ", body)


def check_body_unsafe(body: str) -> str | None:
    """Return skip reason if body assigns to or takes address of ctx/rdram."""
    # Fast path: if none of the patterns appear even in raw text, body is safe.
    if not (
        CTX_ASSIGN_RE.search(body)
        or RDRAM_ASSIGN_RE.search(body)
        or CTX_ADDR_RE.search(body)
        or RDRAM_ADDR_RE.search(body)
    ):
        return None
    cleaned = strip_comments_and_strings(body)
    if CTX_ASSIGN_RE.search(cleaned):
        return "skip_ctx_assign"
    if RDRAM_ASSIGN_RE.search(cleaned):
        return "skip_rdram_assign"
    if CTX_ADDR_RE.search(cleaned):
        return "skip_ctx_addr"
    if RDRAM_ADDR_RE.search(cleaned):
        return "skip_rdram_addr"
    return None


def detect_body_indent(body_after_brace: str) -> str:
    """Infer indentation of the first non-empty, non-preprocessor line in body."""
    for line in body_after_brace.splitlines():
        stripped = line.lstrip(" \t")
        if not stripped or stripped.startswith("#"):
            continue
        return line[: len(line) - len(stripped)]
    return "    "


def process_text(text: str, eol: str, stats: Counter) -> tuple[str, list[str]]:
    """Process all matching function definitions in a single .cpp file."""
    for m in ALREADY_SIG_RE.finditer(text):
        open_idx = m.end() - 1
        close_idx = find_matching_brace(text, open_idx)
        if close_idx != -1 and MARKER in text[open_idx:close_idx]:
            stats["functions_already_restricted"] += 1

    edits: list[tuple[int, int, str]] = []
    changed_fns: list[str] = []

    for m in SIG_RE.finditer(text):
        stats["functions_matched"] += 1
        fn_name = m.group(2)
        open_idx = m.end() - 1
        close_idx = find_matching_brace(text, open_idx)
        if close_idx == -1:
            stats["skip_unclosed_body"] += 1
            continue

        body = text[open_idx + 1 : close_idx]
        if MARKER in body:
            stats["functions_already_restricted"] += 1
            continue

        skip_reason = check_body_unsafe(body)
        if skip_reason is not None:
            stats[skip_reason] += 1
            changed_fns.append(f"SKIP({skip_reason}) {fn_name}")
            continue

        new_sig = (
            f"{m.group(1)}{m.group(3)}rdram_in{m.group(4)}ctx_in{m.group(5)}"
        )
        indent = detect_body_indent(body)
        restrict_stmt = (
            f"{eol}{indent}"
            f"uint8_t* __restrict rdram = rdram_in; "
            f"R5900Context* __restrict ctx = ctx_in; {MARKER}"
        )
        edits.append((m.start(), m.end(), new_sig + restrict_stmt))
        stats["functions_modified"] += 1
        changed_fns.append(fn_name)

    if not any(s for s in changed_fns if not s.startswith("SKIP(")):
        return text, changed_fns

    parts: list[str] = []
    cursor = 0
    for start, end, repl in edits:
        parts.append(text[cursor:start])
        parts.append(repl)
        cursor = end
    parts.append(text[cursor:])
    return "".join(parts), changed_fns


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Add __restrict locals for rdram and ctx in generated functions."
    )
    parser.add_argument(
        "dir",
        nargs="?",
        default="recomp_source",
        help="Directory containing *.cpp files (default: recomp_source)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report counts without modifying files or writing log",
    )
    parser.add_argument(
        "--log",
        default=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "restrict_ctx.log"
        ),
        help="Path to write log when applying",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.dir):
        print(f"error: directory not found: {args.dir}")
        return 2

    cpp_names = sorted(
        e.name for e in os.scandir(args.dir) if e.is_file() and e.name.endswith(".cpp")
    )

    stats = Counter()
    log_entries: list[str] = []

    for name in cpp_names:
        path = os.path.join(args.dir, name)
        with open(path, "rb") as f:
            raw = f.read()
        stats["files_scanned"] += 1

        eol = "\r\n" if b"\r\n" in raw else "\n"
        text = raw.decode("utf-8", errors="replace")
        new_text, fn_events = process_text(text, eol, stats)

        for ev in fn_events:
            if ev.startswith("SKIP("):
                log_entries.append(f"{name}: {ev}")

        if new_text == text:
            continue

        stats["files_modified"] += 1
        for ev in fn_events:
            if not ev.startswith("SKIP("):
                log_entries.append(f"{name}: {ev}")

        if not args.dry_run:
            with open(path, "wb") as f:
                f.write(new_text.encode("utf-8"))

    mode = "DRY-RUN" if args.dry_run else "APPLIED"
    print(
        f"[{mode}] files_scanned={stats['files_scanned']} "
        f"files_modified={stats['files_modified']}"
    )
    print(
        f"[{mode}] functions_matched={stats['functions_matched']} "
        f"functions_modified={stats['functions_modified']}"
    )
    skip_keys = sorted(
        k
        for k in stats
        if k.startswith("skip_") or k == "functions_already_restricted"
    )
    if skip_keys:
        for k in skip_keys:
            print(f"[{mode}] {k}={stats[k]}")
    else:
        print(f"[{mode}] skipped=0")

    if not args.dry_run:
        with open(args.log, "w", encoding="utf-8") as lf:
            lf.write(
                f"files_scanned={stats['files_scanned']} "
                f"files_modified={stats['files_modified']} "
                f"functions_matched={stats['functions_matched']} "
                f"functions_modified={stats['functions_modified']}\n"
            )
            for k in skip_keys:
                lf.write(f"{k}={stats[k]}\n")
            for entry in log_entries:
                lf.write(entry + "\n")
        print(f"[{mode}] log={args.log}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
