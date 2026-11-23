#!/usr/bin/env python3
"""Rewrite unwrapped _mm_cvttps_epi32(X) in recomp_source/*.cpp to saturate +overflow to 0x7FFFFFFF. // FIX-M2"""

from __future__ import annotations

import pathlib
import re
import sys

PATTERN = re.compile(r"_mm_cvttps_epi32\(([A-Za-z_][A-Za-z0-9_]*)\)")
MARKER = "// FIX-M2"
WRAPPED_PREFIX = "_mm_xor_si128(_mm_cvttps_epi32("


def rewrite_line(line: str) -> tuple[str, int]:
    if "_mm_cvttps_epi32(" not in line:
        return line, 0
    if MARKER in line or WRAPPED_PREFIX in line:
        return line, 0

    eol = ""
    if line.endswith("\r\n"):
        body, eol = line[:-2], "\r\n"
    elif line.endswith("\n"):
        body, eol = line[:-1], "\n"
    else:
        body = line

    matches = list(PATTERN.finditer(body))
    if not matches or len(matches) != body.count("_mm_cvttps_epi32("):
        raise ValueError(f"Unsupported _mm_cvttps_epi32 pattern: {body.strip()}")

    new_body, count = PATTERN.subn(
        r"_mm_xor_si128(_mm_cvttps_epi32(\1), _mm_castps_si128(_mm_cmpge_ps(\1, _mm_set1_ps(2147483648.0f))))",
        body,
    )
    return f"{new_body} {MARKER}{eol}", count


def main() -> int:
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    recomp_dir = repo_root / "recomp_source"
    if not recomp_dir.is_dir():
        print(f"Missing directory: {recomp_dir}", file=sys.stderr)
        return 1

    changed_files: list[str] = []
    total_replaced = 0

    for path in sorted(recomp_dir.glob("*.cpp")):
        raw = path.read_bytes()
        text = raw.decode("utf-8", errors="surrogateescape")
        lines = text.splitlines(keepends=True)

        file_replaced = 0
        new_lines: list[str] = []
        for idx, line in enumerate(lines, 1):
            try:
                new_line, count = rewrite_line(line)
            except ValueError as exc:
                print(f"{path}:{idx}: {exc}", file=sys.stderr)
                return 1
            new_lines.append(new_line)
            file_replaced += count

        if file_replaced > 0:
            path.write_bytes("".join(new_lines).encode("utf-8", errors="surrogateescape"))
            changed_files.append(str(path.relative_to(repo_root)))
            total_replaced += file_replaced

    print(f"Changed files ({len(changed_files)}):")
    for f in changed_files:
        print(f"  {f}")
    print(f"Total replaced: {total_replaced}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
