"""C315: EE SQRT.S fd, ft takes sqrt of FT; the generated code used FS (always f0). Patches recomp_source in place.
Idempotent. Usage: python tools/fix_sqrt_s.py [--dry]"""
import re, sys, pathlib

SRC = pathlib.Path(__file__).resolve().parent.parent / "recomp_source"
DRY = "--dry" in sys.argv
CMT = re.compile(r"//\s*0x[0-9a-f]+:\s*0x([0-9a-f]+)\s", re.I)
SQ = re.compile(r"(ctx->f\[(\d+)\]\s*=\s*FPU_SQRT_S\(ctx->f\[)(\d+)(\]\))")
files = sites = 0
for f in sorted(SRC.glob("sub_*.cpp")):
    txt = f.read_text(encoding="utf-8", errors="surrogateescape")
    if "FPU_SQRT_S(" not in txt:
        continue
    lines = txt.split("\n")
    last = None
    n = 0
    for i, ln in enumerate(lines):
        m = CMT.search(ln)
        if m:
            last = int(m.group(1), 16)
        if "FPU_SQRT_S(" in ln and last is not None:
            # must really be COP1.S SQRT (opcode 0x11, fmt 0x10, funct 4)
            if (last >> 26) != 0x11 or ((last >> 21) & 31) != 0x10 or (last & 0x3F) != 4:
                continue
            ft = (last >> 16) & 31
            m2 = SQ.search(ln)
            if m2 and int(m2.group(3)) != ft:
                lines[i] = ln[:m2.start(3)] + str(ft) + ln[m2.end(3):] + " // C315"
                n += 1
    if n:
        files += 1
        sites += n
        if not DRY:
            f.write_text("\n".join(lines), encoding="utf-8", errors="surrogateescape")
print(f"files={files} sites={sites} dry={DRY}")
