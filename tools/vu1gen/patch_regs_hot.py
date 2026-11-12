"""PERF-RG: register-resident STATUS, constant cycle offsets and dead Q-landing checks for the "pure" VU hot blocks (idempotent; run after
patch_adv_hot.py). A pure block has no generic `op.` call, so nothing outside the block code observes st.status / vu.m_cycle until it returns.
 1. `uint32_t stat = st.status;` after the xgkick guard; fmac -> fmacR(vu, stat, ...); the Q-landing status update uses `stat`; `st.status = stat;`
    before the final return. Removes the and/or read-modify-write chain through memory that serialised consecutive FMACs.
 2. `++vu.m_cycle;` -> `vu.m_cycle = S + k;` (S is the block/iteration entry cycle): same stored values, no load->add->store dependency chain.
 3. Blocks whose recorded entry state has no pending Q ('q' token <=> m_fdiv.valid, which is part of the entry hash) and that issue no DIV/SQRT/RSQRT
    lose the per-pair Q-landing check entirely.
Usage: python tools/vu1gen/patch_regs_hot.py [--vu0] [<vublk2_u<unit>_<image>.txt>]"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
GEN = ROOT / "PS2Recomp/ps2xRuntime/src/lib/vu/generated"
TAG = "PERF-RG"
UNIT = 0 if "--vu0" in sys.argv else 1
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

HDR = re.compile(r"^static int (vu0?H_\d+)\(.*// pc=([0-9A-F]+) entry=([0-9a-f]+) exit=([0-9a-f]+) n=(\d+) cycles=(\d+)")
GUARD_RE = re.compile(r"^    if \(vu\.m_xgkick\.active\) return -1;")
QIF = "    if (vu.m_fdiv.valid && vu.m_fdiv.readyCycle <= vu.m_cycle)"
QSHAPE = ["    {",
          "        st.q = vu.m_fdiv.value;",
          "        const uint32_t currentDi = vu.m_fdiv.statusDi & 0x30u;",
          "        st.status = (st.status & 0xFCFu) | currentDi | (currentDi << 6);",
          "        vu.m_fdiv = {};",
          "    }"]
QSHAPE_NEW = [s.replace("st.status = (st.status &", "stat = (stat &") for s in QSHAPE]
FMAC_RE = re.compile(r"vuhot::fmac<([^>]*)>\(vu, ")
OP_RE = re.compile(r"\bop\.")
RET_RE = re.compile(r"^    return -?\d+;$")
SETCYC_RE = re.compile(r"vuhot::setCycleXg\(vu, op, S \+ (\d+)u\)")


def convert(name, pc0, sig, cyc, lines):
    txt = "\n".join(lines)
    if TAG in txt:
        return None, "already"
    for ln in lines:
        if OP_RE.search(ln) and ln.strip() != "const VuNativeOps &op = *c.ops;":
            return None, "generic op"
    if "st.status" in txt.replace("st.status = (st.status & 0xFCFu)", ""):
        return None, "other status use"
    gi = [i for i, ln in enumerate(lines) if GUARD_RE.match(ln)]
    ri = [i for i, ln in enumerate(lines) if RET_RE.match(ln)]
    if len(gi) != 1 or len(ri) != 1:
        return None, "guard/return shape"
    toks = entry.get((pc0, sig))
    noQ = toks is not None and not any(t[0] == "q" for t in toks) and not re.search(r"vuhot::(divQ|sqrtQ|rsqrtQ)", txt)
    out = []
    k = 0
    i = 0
    nfmac = 0
    nq = 0
    ncyc = 0
    while i < len(lines):
        ln = lines[i]
        if i == ri[0]:
            if k != cyc:
                return None, "cycle count %d != header %d" % (k, cyc)
            out.append("    st.status = stat; // " + TAG)
            out.append(ln)
            i += 1
            continue
        if ln.startswith("    uint64_t S = vu.m_cycle;") or ln.strip() == "S = vu.m_cycle;":
            k = 0
            out.append(ln)
        elif ln.strip() == "++vu.m_cycle;" and not ln.startswith("    ++vu.m_cycle; ++"):
            k += 1
            ncyc += 1
            out.append(ln.replace("++vu.m_cycle;", "vu.m_cycle = S + %du; // %s" % (k, TAG)))
        elif ln == QIF:
            if lines[i + 1:i + 7] != QSHAPE:
                return None, "Q landing shape"
            nq += 1
            if noQ:
                i += 7
                continue
            out.append(ln)
            out.extend(QSHAPE_NEW)
            i += 7
            continue
        elif "vuhot::setCycleXg(" in ln:
            mm = SETCYC_RE.search(ln)
            if not mm:
                return None, "setCycleXg shape"
            k = int(mm.group(1))  # pure block: no transfer can be running, so this is m_cycle = S + N
            out.append(ln)
        elif "vuhot::fmac<" in ln:
            new, n = FMAC_RE.subn(lambda m: "vuhot::fmacR<%s>(vu, stat, " % m.group(1), ln)
            if n != 1 or "vuhot::fmac<" in new:
                return None, "fmac shape"
            nfmac += n
            out.append(new)
        else:
            out.append(ln)
        if i == gi[0]:
            out.append("    uint32_t stat = st.status; // " + TAG)
        i += 1
    # the guard line index shifts if lines were dropped above it; the guard precedes every transformed line, so the insert above is exact
    if nfmac != txt.count("vuhot::fmac<"):
        return None, "fmac count"
    return out, None


p = GEN / ("vu%d_hot_blocks.cpp" % UNIT)
t = p.read_text(encoding="utf-8", errors="surrogateescape")
if TAG in t:
    print("already patched")
    sys.exit(0)
lines = t.split("\n")
res = []
i = 0
nconv = 0
skipped = {}
while i < len(lines):
    m = HDR.match(lines[i])
    if m:
        j = i
        while lines[j] != "}":
            j += 1
        blk = lines[i:j + 1]
        new, why = convert(m.group(1), int(m.group(2), 16), int(m.group(3), 16), int(m.group(6)), blk)
        if new is None:
            skipped[m.group(1)] = (m.group(2), why)
            res.extend(blk)
        else:
            nconv += 1
            res.extend(new)
        i = j + 1
        continue
    res.append(lines[i])
    i += 1
out = "\n".join(res)
out = out.replace("static int %s0(" % PFX, "// " + TAG + ": register-resident STATUS, constant cycle offsets, dead Q-landing checks (tools/vu1gen/patch_regs_hot.py)\nstatic int %s0(" % PFX, 1)
p.write_text(out, encoding="utf-8", errors="surrogateescape")
print("converted blocks:", nconv, "skipped:", len(skipped))
why = {}
for k_, v in skipped.items():
    why.setdefault(v[1], []).append(k_)
for w_, ks in sorted(why.items(), key=lambda kv: -len(kv[1])):
    print("  %3d  %s" % (len(ks), w_))
