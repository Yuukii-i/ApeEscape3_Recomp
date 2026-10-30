"""C311: make VU0 macro-mode FMAC ops update MAC/Status (calls ps2x_vu0_flags after the op).
Only touches recomp_source files that contain 'cfc2' (they are the only ones that can observe the flags).
Idempotent. Usage: python tools/fix_vu0_flags.py [--dry]"""
import re, sys, pathlib

SRC = pathlib.Path(__file__).resolve().parent.parent / "recomp_source"
DRY = "--dry" in sys.argv
# mnemonics that update MAC/Status on VU (ABS/MOVE/MR32/FTOI/ITOF/DIV/SQRT/RSQRT do not)
FLAG_OP = re.compile(r"#\s+v(add|sub|mul|madd|msub|max|mini|opmsub|opmula)[a-z0-9]*(\.[xyzw]+)?\s", re.I)
FLAG_OPA = re.compile(r"#\s+v(adda|suba|mula|madda|msuba)[a-z0-9]*(\.[xyzw]+)?\s", re.I)
# the comment line looks like: // 0x3c1e9c: 0x4bc0500f  vmsubw.xyz  $vf0, ...
CMT = re.compile(r"^\s*//\s*0x[0-9a-f]+:\s*0x[0-9a-f]+\s+(v\w+)", re.I)
MN_OK = re.compile(r"^v(add|sub|mul|madd|msub|max|mini|opmsub|opmula)", re.I)
MN_OK2 = re.compile(r"^v(adda|suba|mula|madda|msuba)", re.I)
SETEPI = re.compile(r"_mm_set_epi32\(\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+)\s*\)")
DECL = 'extern "C" void ps2x_vu0_flags(R5900Context *ctx, __m128 res, int laneMask); // C311\n'

total_files = total_ops = 0
for f in sorted(SRC.glob("sub_*.cpp")):
    txt = f.read_text(encoding="utf-8", errors="surrogateescape")
    if "cfc2" not in txt or "ps2x_vu0_flags" in txt:
        continue
    lines = txt.split("\n")
    out = []
    pending = False
    nops = 0
    for ln in lines:
        m = CMT.match(ln)
        if m:
            mn = m.group(1)
            pending = bool(MN_OK.match(mn) or MN_OK2.match(mn))
            out.append(ln)
            continue
        if pending and "_mm_blendv_ps" in ln and "res" in ln and ln.rstrip().endswith(("}", "// FIX-VUMAC")):
            # lane mask: the _mm_set_epi32 that feeds the blend (last one on the line)
            sets = SETEPI.findall(ln)
            if sets:
                w, z, y, x = (int(v) != 0 for v in sets[-1])
                mask = (1 if x else 0) | (2 if y else 0) | (4 if z else 0) | (8 if w else 0)
                call = f" ps2x_vu0_flags(ctx, res, {mask});"
                if ln.rstrip().endswith("// FIX-VUMAC"):
                    base = ln.rstrip()[: -len("// FIX-VUMAC")].rstrip()
                    ln = base[:-1].rstrip() + call + " } // FIX-VUMAC C311"
                else:
                    s = ln.rstrip()
                    ln = s[:-1].rstrip() + call + " } // C311"
                nops += 1
                pending = False
        out.append(ln)
    if nops:
        total_files += 1
        total_ops += nops
        print(f"{f.name}: {nops} ops")
        if not DRY:
            # declaration after the unconditional #include "ps2_stubs.h" (later includes sit in #ifdef blocks)
            idx = next((i for i, l in enumerate(out) if l.startswith('#include "ps2_stubs.h"')), -1)
            out.insert(idx + 1, DECL.rstrip("\n"))
            f.write_text("\n".join(out), encoding="utf-8", errors="surrogateescape")
print(f"files={total_files} ops={total_ops} dry={DRY}")
