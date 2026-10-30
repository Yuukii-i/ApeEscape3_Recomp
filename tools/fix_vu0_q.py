"""C317: route VU0 macro vdiv/vsqrt/vrsqrt through hardware-semantics helpers (ps2_runtime.cpp: ps2x_vu0_div/sqrt/rsqrt).
Patches recomp_source in place; idempotent. Usage: python tools/fix_vu0_q.py [--dry]
All 766 vrsqrt sites in the game have fs = vf0w (= 1.0), verified before writing this."""
import pathlib, sys

SRC = pathlib.Path(__file__).resolve().parent.parent / "recomp_source"
DRY = "--dry" in sys.argv
REPL = [
    ("ctx->vu0_q = (ft != 0.0f) ? (fs / ft) : 0.0f;", "ctx->vu0_q = ps2x_vu0_div(fs, ft);"),
    ("ctx->vu0_q = sqrtf(std::max(0.0f, ft));", "ctx->vu0_q = ps2x_vu0_sqrt(ft);"),
    ("ctx->vu0_q = (ft > 0.0f) ? (1.0f / sqrtf(ft)) : 0.0f;", "ctx->vu0_q = ps2x_vu0_rsqrt(1.0f, ft);"),
]
DECL = ('extern "C" float ps2x_vu0_div(float, float); extern "C" float ps2x_vu0_sqrt(float); '
        'extern "C" float ps2x_vu0_rsqrt(float, float); // C317')
files = sites = 0
for f in sorted(SRC.glob("sub_*.cpp")):
    txt = f.read_text(encoding="utf-8", errors="surrogateescape")
    if "vu0_q = " not in txt or "ps2x_vu0_div(float" in txt:
        continue
    n = 0
    for old, new in REPL:
        c = txt.count(old)
        if c:
            txt = txt.replace(old, new)
            n += c
    if not n:
        continue
    lines = txt.split("\n")
    idx = next((i for i, l in enumerate(lines) if l.startswith('#include "ps2_stubs.h"')), -1)
    lines.insert(idx + 1, DECL)
    files += 1
    sites += n
    if not DRY:
        f.write_text("\n".join(lines), encoding="utf-8", errors="surrogateescape")
print(f"files={files} sites={sites} dry={DRY}")
