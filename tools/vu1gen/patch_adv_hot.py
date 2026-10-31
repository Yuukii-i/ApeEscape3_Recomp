"""PERF-ADV: remove the generic per-cycle commit (op.advance1) from every VU1 hot block that cannot have pending pipeline state (idempotent;
run after patch_loop_hot.py / patch_inline_hot.py / patch_inline2_hot.py). Generalises what patch_loop_hot.py did for self-loops.
A block qualifies when its recorded ENTRY signature has no pending store ('s'), E-unit result ('p'/'r') or running XGKICK ('x') and its code
contains no generic op that can create such state (XGKICK, E-unit ops, execUpper, advanceTo, commit, qV*/qA). Then the only things advance1
could ever land are (a) stores issued inside the block, which land at the end of their own pair (readyCycle = issue + 1), so they are written at
issue, and (b) the Q result of DIV/SQRT/RSQRT, landed by an inline copy of commitReadyPipelines' m_fdiv branch. Also adds `if (xgkick.active) return -1`
to every transformed block and to the fused loops (they no longer step a running transfer). Usage: python tools/vu1gen/patch_adv_hot.py <vublk2_u1_<image>.txt>"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
GEN = ROOT / "PS2Recomp/ps2xRuntime/src/lib/vu/generated"
TAG = "PERF-ADV"
UNIT = 0 if "--vu0" in sys.argv else 1  # --vu0: patch generated/vu0_hot_blocks.cpp (EE-thread VU0 microprograms) instead of the VU1 file
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
PFX = "vu0H_" if UNIT == 0 else "vuH_"
IMAGE = "d985722524327b89" if UNIT == 0 else "86503d3905e35276"
blk_path = ARGS[0] if ARGS else str(ROOT / ("logs/vublk2_u%d_%s.txt" % (UNIT, IMAGE)))

entry = {}
cur = None
for ln in open(blk_path, encoding="utf-8", errors="replace"):
    m = re.match(r"B pc=([0-9A-F]+) sig=([0-9a-f]+) ", ln)
    if m:
        cur = (int(m.group(1), 16), int(m.group(2), 16))
        continue
    if cur is not None and ln.startswith("  entry:"):
        entry[cur] = ln[len("  entry:"):].split()
        cur = None

HDR = re.compile(r"^static int (vu0?H_\d+)\(.*// pc=([0-9A-F]+) entry=([0-9a-f]+) exit=([0-9a-f]+) n=(\d+)")
QS_OLD = "    auto qs = [&](uint32_t a, const uint32_t *w, uint8_t l) { vuhot::storeFast(vu, c, a, w, l); };"
QS_NEW = ("    // PERF-ADV: a store lands at the end of its own pair, so write it at issue\n"
          "    auto qs = [&](uint32_t a, const uint32_t *w, uint8_t l)\n"
          "    {\n"
          "        for (uint32_t k = 0; k < 4u; ++k)\n"
          "            if (l & (8u >> k))\n"
          "                std::memcpy(c.vuData + a + k * 4u, w + k, 4u);\n"
          "    };")
QLAND = ("    ++vu.m_cycle;\n"
         "    if (vu.m_fdiv.valid && vu.m_fdiv.readyCycle <= vu.m_cycle)\n"
         "    {\n"
         "        st.q = vu.m_fdiv.value;\n"
         "        const uint32_t currentDi = vu.m_fdiv.statusDi & 0x30u;\n"
         "        st.status = (st.status & 0xFCFu) | currentDi | (currentDi << 6);\n"
         "        vu.m_fdiv = {};\n"
         "    }")
GUARD = "    if (vu.m_xgkick.active) return -1; // %s: this block no longer steps a running XGKICK transfer" % TAG
BAD = ("return -1", "op.advanceTo", "op.execUpper", "op.qV", "op.qA", "op.commit", "op.qStore", "storeFast(vu, c, a, w, l); };\n    (void)qs; (void)op;\n    do {")


def lower_ok(w):
    """generic lower ops that never create pending pipeline state"""
    op7 = (w >> 25) & 0x7F
    if 0x10 <= op7 <= 0x1C:
        return True
    if op7 == 0x40 and (w & 0x3F) >= 0x3C:
        return ((w & 3) | ((w >> 4) & 0x7C)) in (0x3C, 0x3D, 0x68, 0x69, 0x3B)
    return False


def convert(name, pc0, sig, lines):
    txt = "\n".join(lines)
    if "PERF-LOOP" in txt:  # fused loop: only the XGKICK guard
        if GUARD in txt:
            return None, "loop already guarded"
        out = []
        for ln in lines:
            out.append(ln)
            if ln.strip() == "(void)qs; (void)op;":
                out.append(GUARD)
        return out, None
    toks = entry.get((pc0, sig))
    if toks is None:
        return None, "no recorded entry state"
    for t in toks:
        if t[0] in "sprx":
            return None, "entry has pending state %s" % t
    for bad in BAD[:-1]:
        if bad in txt:
            return None, bad
    for m in re.finditer(r"op\.execLower\(vu, 0x([0-9a-f]+)u", txt):
        if not lower_ok(int(m.group(1), 16)):
            return None, "generic lower op %s" % m.group(1)
    if QS_OLD not in lines:
        return None, "unexpected prologue"
    out = []
    for ln in lines:
        if ln == QS_OLD:
            out.extend(QS_NEW.split("\n"))
            continue
        if ln.strip() == "(void)qs; (void)op;":
            out.append(ln)
            out.append(GUARD)
            continue
        if ln.strip() == "op.advance1(vu);":
            out.extend(QLAND.split("\n"))
            continue
        ln = ln.replace(" if (vu.m_xgkick.active) op.xgProgress(vu); // PERF-XG", "")
        out.append(ln)
    return out, None


p = GEN / ("vu%d_hot_blocks.cpp" % UNIT)
t = p.read_text(encoding="utf-8", errors="surrogateescape")
if TAG in t:
    print("already patched")
    sys.exit(0)
lines = t.split("\n")
res = []
i = 0
nconv = nloop = 0
skipped = {}
while i < len(lines):
    m = HDR.match(lines[i])
    if m:
        j = i
        while lines[j] != "}":
            j += 1
        blk = lines[i:j + 1]
        new, why = convert(m.group(1), int(m.group(2), 16), int(m.group(3), 16), blk)
        if new is None:
            skipped[m.group(1)] = (m.group(2), why)
            res.extend(blk)
        else:
            if "PERF-LOOP" in "\n".join(blk):
                nloop += 1
            else:
                nconv += 1
            res.extend(new)
        i = j + 1
        continue
    res.append(lines[i])
    i += 1
out = "\n".join(res)
out = out.replace("static int %s0(" % PFX, "// " + TAG + ": advance1 removed from qualifying blocks (tools/vu1gen/patch_adv_hot.py)\nstatic int %s0(" % PFX, 1)
p.write_text(out, encoding="utf-8", errors="surrogateescape")
print("converted blocks:", nconv, "fused loops guarded:", nloop, "skipped:", len(skipped))
why = {}
for k, v in skipped.items():
    why.setdefault(v[1], []).append(k)
for w_, ks in sorted(why.items(), key=lambda kv: -len(kv[1])):
    print("  %3d  %s" % (len(ks), w_))
