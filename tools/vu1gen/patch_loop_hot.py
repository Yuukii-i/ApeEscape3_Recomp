"""PERF-LOOP: fuse self-looping VU1 hot blocks into one function that iterates internally (idempotent; run after patch_lean_hot.py).
A hot block whose recorded exit timing signature equals its entry signature and whose next pc is its own start pc is a loop body
that can run again with exactly the same static timing. The fused function repeats the body while the branch re-enters it,
which removes the per-iteration dispatcher round trip (hash lookup, call, hotshare bookkeeping) and the pending-store machinery:
  - the only pending state a loop block can create is (a) stores, which land at the end of their own pair (readyCycle = issue + 1, committed by the
    advance after that pair), so they are written directly at issue; (b) the Q-pipeline result of DIV/SQRT/RSQRT, landed by an inline copy of
    commitReadyPipelines' m_fdiv branch at every pair that previously called advance1.
  - blocks with XGKICK, E bits, execUpper, advanceTo, or any generic lower op other than DIV/SQRT/RSQRT/WAITQ stay as they are.
Usage: python tools/vu1gen/patch_loop_hot.py <vublk2_u1_<image>.txt>"""
import pathlib
import re
import sys

GEN = pathlib.Path(__file__).resolve().parent.parent.parent / "PS2Recomp/ps2xRuntime/src/lib/vu/generated"
TAG = "PERF-LOOP"
UNIT = 0 if "--vu0" in sys.argv else 1  # --vu0: patch generated/vu0_hot_blocks.cpp (EE-thread VU0 microprograms) instead of the VU1 file
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
PFX = "vu0H_" if UNIT == 0 else "vuH_"
IMAGE = "d985722524327b89" if UNIT == 0 else "86503d3905e35276"
blk_path = ARGS[0] if ARGS else str(pathlib.Path(__file__).resolve().parent.parent.parent / ("logs/vublk2_u%d_%s.txt" % (UNIT, IMAGE)))

# (pc, sig) -> next pc, from the block recorder's output
nexts = {}
for ln in open(blk_path, encoding="utf-8", errors="replace"):
    m = re.match(r"B pc=([0-9A-F]+) sig=([0-9a-f]+) exitsig=([0-9a-f]+) n=(\d+) xg=(\d) next=([0-9A-F]+)", ln)
    if m:
        nexts[(int(m.group(1), 16), int(m.group(2), 16))] = (int(m.group(3), 16), int(m.group(6), 16))

HDR = re.compile(r"^static int (vu0?H_\d+)\(.*// pc=([0-9A-F]+) entry=([0-9a-f]+) exit=([0-9a-f]+) n=(\d+)")
QS_OLD = "    auto qs = [&](uint32_t a, const uint32_t *w, uint8_t l) { vuhot::storeFast(vu, c, a, w, l); };"
QS_NEW = ("    // PERF-LOOP: a store lands at the end of its own pair, so write it at issue\n"
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
OK_LOWER = (0x38, 0x39, 0x3A, 0x3B)  # DIV, SQRT, RSQRT, WAITQ: only touch Q / status through m_fdiv


def lower_ok(w):
    if ((w >> 25) & 0x7F) != 0x40 or (w & 0x3F) < 0x3C:
        return False
    return ((w & 3) | ((w >> 4) & 0x7C)) in OK_LOWER


def fuse(name, pc0, sig, n, lines):
    txt = "\n".join(lines)
    ex = nexts.get((pc0, sig))
    if ex is None or ex[0] != sig or ex[1] != pc0:
        return None, "not a recorded self-loop"
    for bad in ("return -1", "st.ebit", "op.advanceTo", "op.execUpper", "op.qV", "op.qA", "op.commit"):
        if bad in txt:
            return None, bad
    for m in re.finditer(r"op\.execLower\(vu, 0x([0-9a-f]+)u", txt):
        if not lower_ok(int(m.group(1), 16)):
            return None, "generic lower op %s" % m.group(1)
    out = []
    tail_done = False
    for ln in lines:
        if ln == QS_OLD:
            out.extend(QS_NEW.split("\n"))
            continue
        if ln.startswith("    const uint64_t S = vu.m_cycle;"):
            out.append("    uint64_t S = vu.m_cycle;")
            out.append("    uint64_t iters = 0;")
            continue
        if re.match(r"    c\.instrs \+= \d+u;", ln):
            continue
        if ln.strip() == "(void)qs; (void)op;":
            out.append(ln)
            out.append("    do { // %s: loop body, repeated while the branch re-enters it" % TAG)
            out.append("    S = vu.m_cycle;")
            continue
        if ln.strip() == "op.advance1(vu);":
            out.extend(QLAND.split("\n"))
            continue
        ln = ln.replace(" if (vu.m_xgkick.active) op.xgProgress(vu); // PERF-XG", "")
        if ln.startswith("    st.cycles = vu.m_cycle; // PERF-LEAN") and not tail_done:
            tail_done = True
            out.append("    ++iters;")
            out.append("    } while (st.pc == 0x%04Xu && !st.branchPending && !st.ebit && !vu.m_stopRequested && c.budgetEnd - vu.m_cycle > 160u);" % pc0)
            out.append("    c.instrs += %du * static_cast<uint32_t>(iters); // %s" % (n, TAG))
            out.append("    *c.nextReadyW = 0u; // %s: pending-Q landing / pushes may have changed the next-ready cache" % TAG)
            out.append("    s_loopIters += iters; if ((s_loopIters & 0xFFFFFull) < iters) std::printf(\"[probe] vu1 loop %04X iters=%%llu@NL@\", (unsigned long long)s_loopIters);" % pc0)
        out.append(ln)
    if not tail_done:
        return None, "no PERF-LEAN tail (run patch_lean_hot.py first)"
    return out, None


p = GEN / ("vu%d_hot_blocks.cpp" % UNIT)
t = p.read_text(encoding="utf-8", errors="surrogateescape")
if TAG in t:
    print("already patched")
    sys.exit(0)
lines = t.split("\n")
res = []
i = 0
nfused = 0
skipped = {}
while i < len(lines):
    m = HDR.match(lines[i])
    if m:
        j = i
        while lines[j] != "}":
            j += 1
        blk = lines[i:j + 1]
        new, why = fuse(m.group(1), int(m.group(2), 16), int(m.group(3), 16), int(m.group(5)), blk)
        if new is None:
            skipped[m.group(1)] = (m.group(2), why)
            res.extend(blk)
        else:
            res.extend(new)
            nfused += 1
            print("fused", m.group(1), "pc", m.group(2), "n", m.group(5))
        i = j + 1
        continue
    res.append(lines[i])
    i += 1
out = "\n".join(res)
out = out.replace("@NL@", chr(92) + "n")
# counters + includes before the first block
out = out.replace("static int %s0(" % PFX, "static uint64_t s_loopIters = 0; // PERF-LOOP\n\nstatic int %s0(" % PFX, 1)
if "#include <cstdio>" not in out:
    out = out.replace("#include <cstring>\n", "#include <cstdio>\n#include <cstring>\n", 1)
p.write_text(out, encoding="utf-8", errors="surrogateescape")
print("fused blocks:", nfused, "skipped:", len(skipped))
for k, v in list(skipped.items())[:12]:
    print("  skip", k, v)
