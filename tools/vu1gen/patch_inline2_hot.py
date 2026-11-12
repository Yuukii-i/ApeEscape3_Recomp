"""PERF-INL2: second set of inlined generic lower ops in VU1 hot blocks (idempotent; run after patch_inline_hot.py).
FCAND / FCOR / FMAND / FCGET (with the flgSyncReader step of the op.execLower wrapper), MTIR, MFIR, XTOP, XITOP: exact restatements of
VU1Interpreter::execLower. XGKICK and the E-unit ops stay generic (they start pipelines). Usage: python tools/vu1gen/patch_inline2_hot.py"""
import pathlib
import re
import sys

GEN = pathlib.Path(__file__).resolve().parent.parent.parent / "PS2Recomp/ps2xRuntime/src/lib/vu/generated"
TAG = "PERF-INL2"
UNIT = 0 if "--vu0" in sys.argv else 1  # --vu0: patch generated/vu0_hot_blocks.cpp (EE-thread VU0 microprograms) instead of the VU1 file
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
PFX = "vu0H_" if UNIT == 0 else "vuH_"
IMAGE = "d985722524327b89" if UNIT == 0 else "86503d3905e35276"
LOWER = re.compile(r"^(\s*)op\.execLower\(vu, 0x([0-9a-f]+)u, c\.vuData, c\.dataSize, \*c\.gs, c\.memory, 0x([0-9a-f]+)u\);\s*$")


def inline_lower(w):
    op7 = (w >> 25) & 0x7F
    vis, vit = (w >> 11) & 0x1F, (w >> 16) & 0x1F
    imm24 = w & 0xFFFFFF
    sync_clip = "st.clip = vuflags::flgVisible(vuflags::s_flgClip[%d], vu.m_cycle);" % UNIT
    sync_mac = "st.mac = vuflags::flgVisible(vuflags::s_flgMac[%d], vu.m_cycle);" % UNIT
    if op7 == 0x12:
        return [sync_clip, "st.vi[1] = ((st.clip & 0x%06Xu) != 0u) ? 1 : 0;" % imm24]
    if op7 == 0x13:
        return [sync_clip, "st.vi[1] = ((st.clip | 0x%06Xu) == 0xFFFFFFu) ? 1 : 0;" % imm24]
    if op7 == 0x1A:
        out = [sync_mac]
        if vit:
            out.append("st.vi[%d] = static_cast<int32_t>(st.mac & static_cast<uint32_t>(static_cast<uint16_t>(st.vi[%d])));" % (vit, vis))
        return out
    if op7 == 0x1C:
        out = [sync_clip]
        if vit:
            out.append("st.vi[%d] = static_cast<int32_t>(st.clip & 0x0FFFu);" % vit)
        return out
    if op7 == 0x40 and (w & 0x3F) >= 0x3C:
        f2 = (w & 3) | ((w >> 4) & 0x7C)
        dest = (w >> 21) & 0xF
        if f2 == 0x3C:  # MTIR
            comp = (w >> 21) & 3
            out = ["uint32_t fval; std::memcpy(&fval, &st.vf[%d][%d], 4);" % (vis, comp)]
            if vit:
                out.append("st.vi[%d] = static_cast<int32_t>(static_cast<int16_t>(fval & 0xFFFFu));" % vit)
            return ["{"] + ["    " + s for s in out] + ["}"]
        if f2 == 0x3D:  # MFIR
            return ["{", "    float res[4];", "    const int32_t val = static_cast<int32_t>(static_cast<int16_t>(st.vi[%d] & 0xFFFF));" % vis,
                    "    std::memcpy(&res[0], &val, 4); res[1] = res[0]; res[2] = res[0]; res[3] = res[0];",
                    "    vuhot::applyDest(st.vf[%d], res, %d);" % (vit, dest), "}"]
        if f2 == 0x68:  # XTOP
            return ["st.vi[%d] = static_cast<int32_t>(st.top & 0x3FFu);" % vit] if vit else ["// XTOP to vi0"]
        if f2 == 0x69:  # XITOP
            return ["st.vi[%d] = static_cast<int32_t>(st.itop & 0x3FFu);" % vit] if vit else ["// XITOP to vi0"]
    return None


p = GEN / ("vu%d_hot_blocks.cpp" % UNIT)
t = p.read_text(encoding="utf-8", errors="surrogateescape")
if TAG in t:
    print("already patched")
    raise SystemExit
out = []
n = 0
for ln in t.split("\n"):
    m = LOWER.match(ln)
    if m:
        rep = inline_lower(int(m.group(2), 16))
        if rep is not None:
            ind = m.group(1)
            out.extend(ind + r + (" // " + TAG if k == 0 else "") for k, r in enumerate(rep))
            n += 1
            continue
    out.append(ln)
p.write_text("\n".join(out), encoding="utf-8", errors="surrogateescape")
print("lower ops inlined:", n)
