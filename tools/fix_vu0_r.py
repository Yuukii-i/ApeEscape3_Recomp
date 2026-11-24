"""C320: VU0 macro R register (vrinit/vrnext/vrget/vrxor) -> hardware LFSR helpers in ps2_runtime.cpp.
The old code was invented: vrnext never wrote its vf dest, so every game random number (e.g. random-direction
function 0x359D08) was garbage. Patches recomp_source in place; idempotent. Usage: python tools/fix_vu0_r.py [--dry]"""
import pathlib, re, sys

SRC = pathlib.Path(__file__).resolve().parent.parent / "recomp_source"
DRY = "--dry" in sys.argv
DECL = ('extern "C" void ps2x_vu0_rinit(R5900Context *ctx, float fs); extern "C" void ps2x_vu0_rxor(R5900Context *ctx, float fs); '
        'extern "C" float ps2x_vu0_rget(R5900Context *ctx); extern "C" float ps2x_vu0_rnext(R5900Context *ctx); // C320')

RE_NEXT = re.compile(
    r"(// 0x[0-9a-f]+: 0x[0-9a-f]+\s+vrnext\.(\w+)\s+\$vf(\d+), \$R\n\s*ctx->pc = [^\n]+\n)"
    r"\s*\{\n    uint32_t r_vals\[4\];.*?ctx->vu0_r = _mm_castsi128_ps\(_mm_loadu_si128\(\(__m128i\*\)r_vals\)\);\n\}",
    re.S)
RE_INIT = re.compile(r"    // PS2 uses a specific LFSR initialization pattern\n.*?ctx->vu0_r = _mm_castsi128_ps\(_mm_set_epi32\(r3, r2, r1, r0\)\);", re.S)
RE_XOR = re.compile(r"    __m128i r_current = _mm_castps_si128\(ctx->vu0_r\);\n.*?ctx->vu0_r = _mm_castsi128_ps\(mixed\);", re.S)


def lanes(dest):
    # x=lane0 .. w=lane3; the blend immediate has bit i set for lane i
    return sum(1 << "xyzw".index(c) for c in dest)


def repl_next(m):
    vf = int(m.group(3))
    imm = lanes(m.group(2))
    return (m.group(1) + "    { ctx->vu0_vf[%d] = _mm_blend_ps(ctx->vu0_vf[%d], _mm_set1_ps(ps2x_vu0_rnext(ctx)), %d); } // C320\n"
            % (vf, vf, imm)).rstrip("\n")


files = sites = 0
for f in sorted(SRC.glob("sub_*.cpp")):
    txt = f.read_text(encoding="utf-8", errors="surrogateescape")
    if "vu0_r" not in txt or "ps2x_vu0_rnext" in txt:
        continue
    n = 0
    txt, c = RE_NEXT.subn(repl_next, txt); n += c
    txt, c = RE_INIT.subn("    ps2x_vu0_rinit(ctx, src); // C320", txt); n += c
    txt, c = RE_XOR.subn("    ps2x_vu0_rxor(ctx, src); // C320", txt); n += c
    c = txt.count("__m128 res = ctx->vu0_r;")
    txt = txt.replace("__m128 res = ctx->vu0_r;", "__m128 res = _mm_set1_ps(ps2x_vu0_rget(ctx));"); n += c
    if not n:
        continue
    lines = txt.split("\n")
    idx = next((i for i, l in enumerate(lines) if l.startswith('#include "ps2_stubs.h"')), -1)
    lines.insert(idx + 1, DECL)
    files += 1
    sites += n
    left = "r_vals" in txt or "ctx->vu0_r = " in txt
    print(f.name, "sites", n, "LEFTOVER" if left else "ok")
    if not DRY:
        f.write_text("\n".join(lines), encoding="utf-8", errors="surrogateescape")
print(f"files={files} sites={sites} dry={DRY}")
