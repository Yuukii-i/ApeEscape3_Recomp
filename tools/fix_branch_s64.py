"""FIX-B64 (AU3G): upgrade 64-bit sign-test branches in recomp_source from GPR_S32 to GPR_S64.
R5900 BLTZ/BGEZ/BLEZ/BGTZ (+L/AL/ALL) test the full 64-bit register.
Usage: python tools/fix_branch_s64.py [--dry-run | --apply]"""
import argparse
import difflib
import pathlib
import re
import sys

SRC = pathlib.Path(__file__).resolve().parent.parent / "recomp_source"
PATTERN = re.compile(
    rb"(branch_taken_0x[0-9a-fA-F]+ = \(GPR_)S32(\(ctx, \d+\) (?:<=|<|>=|>) 0\))"
)
REPL = rb"\1S64\2"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replace 32-bit sign-test branches (GPR_S32) with 64-bit (GPR_S64)."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--dry-run", action="store_true", help="Print counts and first 5 diffs (default)"
    )
    group.add_argument(
        "--apply", action="store_true", help="Rewrite modified files in place"
    )
    args = parser.parse_args()
    apply = args.apply

    total_files = 0
    total_repls = 0
    diffs_shown = 0

    for path in sorted(SRC.glob("*.cpp")):
        raw = path.read_bytes()
        if b"GPR_S32" not in raw:
            continue
        new_raw, count = PATTERN.subn(REPL, raw)
        if not count:
            continue

        total_files += 1
        total_repls += count

        if apply:
            path.write_bytes(new_raw)
        else:
            print(f"{path.name}: {count}")
            if diffs_shown < 5:
                old_lines = raw.decode("utf-8", errors="surrogateescape").splitlines(
                    keepends=True
                )
                new_lines = new_raw.decode("utf-8", errors="surrogateescape").splitlines(
                    keepends=True
                )
                diff = difflib.unified_diff(
                    old_lines,
                    new_lines,
                    fromfile=f"a/{path.name}",
                    tofile=f"b/{path.name}",
                    n=1,
                )
                sys.stdout.writelines(diff)
                diffs_shown += 1

    mode = "apply" if apply else "dry-run"
    print(f"Total: {total_repls} replacements in {total_files} files ({mode})")


if __name__ == "__main__":
    main()
