"""PERF-XG: let VU1 hot blocks run while an XGKICK transfer is active, plus per-cause slow-pair counters.
Patches the generated vu1_hot_blocks.cpp / vu1_native_dispatch.cpp / vu0_native_dispatch.cpp in place (idempotent). The generators
(gen_vu1_hot.py, gen_vu1_native.py) carry the same change so a regeneration keeps it. Usage: python tools/vu1gen/patch_xg_hot.py"""
import pathlib
import re

GEN = pathlib.Path(__file__).resolve().parent.parent.parent / "PS2Recomp/ps2xRuntime/src/lib/vu/generated"
TAG = "PERF-XG"
NL = chr(92) + "n"  # a backslash-n inside a C string literal

# ---------------------------------------------------------------- hot blocks
p = GEN / "vu1_hot_blocks.cpp"
t = p.read_text(encoding="utf-8", errors="surrogateescape")
if TAG not in t:
    old1 = "    ++vu.m_cycle; st.cycles = vu.m_cycle;\n"
    n1 = t.count(old1)
    t = t.replace(old1, "    ++vu.m_cycle; st.cycles = vu.m_cycle; if (vu.m_xgkick.active) op.xgProgress(vu); // PERF-XG\n")
    t, n2 = re.subn(r"    vu\.m_cycle = S \+ (\d+)u; st\.cycles = vu\.m_cycle;\n", r"    vuhot::setCycleXg(vu, op, S + \1u); // PERF-XG\n", t)
    # blocks that contain an XGKICK pair were recorded without a running transfer: decline while one is active
    parts = re.split(r"(?=^static int vuH_\d+\()", t, flags=re.M)
    nxg = 0
    for i, part in enumerate(parts):
        if not part.startswith("static int vuH_"):
            continue
        has_xg = False
        for m in re.finditer(r"execLower\(vu, 0x([0-9a-f]+)u", part):
            w = int(m.group(1), 16)
            if (w >> 25) == 0x40 and (w & 0x7FF) == 0x6FC:
                has_xg = True
        if has_xg:
            parts[i] = part.replace("    c.instrs += ", "    if (vu.m_xgkick.active) return -1; // PERF-XG: timing recorded without a running transfer\n    c.instrs += ", 1)
            nxg += 1
    t = "".join(parts)
    p.write_text(t, encoding="utf-8", errors="surrogateescape")
    print("hot blocks: progress calls", n1, "stall rewrites", n2, "xgkick blocks declining", nxg)
else:
    print("hot blocks already patched")

# ---------------------------------------------------------------- native dispatch (vu1 + vu0)
NEW_TOP = """#include <cstdio>
#include <cstdlib>
#include <intrin.h>

namespace
{
uint64_t s_hotBlocks = 0, s_hotPairs = 0, s_slowPairs = 0;
// PERF-XG: slow-pair causes {0 no hot block starts at pc, 1 xgkick active (PS2X_VU1_XG_HOT off), 2 branch/ebit/halt/budget state,
// 3 hash miss, 4 hot block declined, 5 slow pair executed while a transfer was active} and an optional TSC split (PS2X_VU1_TSC=1)
uint64_t s_cause[6] = {};
uint64_t s_tsc[4] = {}; // hot ticks, slow ticks, hot blocks timed, slow pairs timed
const bool s_xgHot = []() { const char *e = std::getenv("PS2X_VU1_XG_HOT"); return e && e[0] == '1'; }();
const bool s_tscOn = []() { const char *e = std::getenv("PS2X_VU1_TSC"); return e && e[0] == '1'; }();
}

uint64_t *vu1NativeStats(uint32_t which) { return which == 0u ? s_cause : s_tsc; }

int vu1NativeRun(VU1Interpreter &vu, VuNativeCtx &c)
{
    c.hashValid = false; // the interpreter may have executed pairs since the last hot block
    while (vu.m_cycle < c.budgetEnd && !vu.m_stopRequested)
    {
        const uint32_t pc = vu.m_state.pc;
        if ((pc & 7u) != 0u || pc >= 0x4000u)
            return 2;
        // PERF-IE: hot blocks with static timing (generated/vu1_hot_blocks.cpp); any unknown state falls back to the pair executors
        if (kVu1HotStart[pc >> 3] && (s_xgHot || !vu.m_xgkick.active) && !vu.m_state.branchPending && !vu.m_state.ebit &&
            !vu.m_state.haltAfterDelaySlot && c.budgetEnd - vu.m_cycle > 160u)
        {
            if (!c.hashValid)
            {
                c.nextHash = c.ops->blkHash(vu);
                c.hashValid = true;
            }
            const VuHotFn hf = vu1HotLookup(pc, c.nextHash);
            if (hf)
            {
                const uint64_t i0 = c.instrs;
                const uint64_t tH0 = s_tscOn ? __rdtsc() : 0ull;
                const int hr = hf(vu, c);
                if (s_tscOn)
                {
                    s_tsc[0] += __rdtsc() - tH0;
                    ++s_tsc[2];
                }
                if (hr >= 0)
                {
                    s_hotPairs += c.instrs - i0;
                    ++s_hotBlocks;
                    if (c.check && c.ops->blkHash(vu) != c.nextHash)
                    {
                        ++c.checkFail;
                        if (c.checkFail <= 6)
                            std::printf("[probe] hot block exit-hash MISMATCH at pc=%04X (block entered at %04X)@NL@", vu.m_state.pc, pc);
                        c.hashValid = false;
                    }
                    if ((s_hotBlocks & 0x7FFFFFull) == 0u)
                        std::printf("[probe] hot blocks=%llu hotPairs=%llu slowPairs=%llu hotShare=%.1f%% checkFail=%llu@NL@", (unsigned long long)s_hotBlocks,
                                    (unsigned long long)s_hotPairs, (unsigned long long)s_slowPairs,
                                    100.0 * s_hotPairs / double(s_hotPairs + s_slowPairs + 1), (unsigned long long)c.checkFail);
                    if (hr != 0)
                        return hr;
                    continue;
                }
                ++s_cause[4]; // declined before executing anything
            }
            else
                ++s_cause[3];
        }
        else if (!kVu1HotStart[pc >> 3])
            ++s_cause[0];
        else if (vu.m_xgkick.active && !s_xgHot)
            ++s_cause[1];
        else
            ++s_cause[2];
        c.hashValid = false;
        const StepFn fn = kStep[pc >> 3];
        if (!fn)
            return 2;
        ++s_slowPairs;
        if (vu.m_xgkick.active)
            ++s_cause[5];
        const uint64_t tS0 = s_tscOn ? __rdtsc() : 0ull;
        const int r = fn(vu, c);
        if (s_tscOn)
        {
            s_tsc[1] += __rdtsc() - tS0;
            ++s_tsc[3];
        }
        if (r != 0)
            return r;
    }
    return 1;
}
""".replace("@NL@", NL)

for name, Name, hot in (("vu1", "Vu1", "hot"), ("vu0", "Vu0", "hot0")):
    f = GEN / ("%s_native_dispatch.cpp" % name)
    s = f.read_text(encoding="utf-8", errors="surrogateescape")
    if TAG in s:
        print(name, "dispatch already patched")
        continue
    k = s.index("#include <cstdio>\n\nnamespace\n{\nuint64_t s_hotBlocks")
    old = s[k:]
    new = NEW_TOP
    new = new.replace("vu1NativeRun", name + "NativeRun").replace("vu1NativeStats", name + "NativeStats")
    new = new.replace("kVu1HotStart", "k%sHotStart" % Name).replace("vu1HotLookup", name + "HotLookup")
    new = new.replace("[probe] hot blocks=", "[probe] %s blocks=" % hot)
    m = re.search(r"if \(\(pc & 7u\) != 0u \|\| pc >= (0x[0-9A-Fa-f]+u)\)", old)
    new = new.replace("pc >= 0x4000u", "pc >= " + m.group(1))
    f.write_text(s[:k] + new, encoding="utf-8", errors="surrogateescape")
    print(name, "dispatch patched")
