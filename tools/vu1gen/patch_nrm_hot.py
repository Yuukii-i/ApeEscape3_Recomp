"""PERF-NR: skip operand normalisation that is provably the identity (idempotent; run after patch_regs_hot.py, which introduces fmacR).
Normalisation (N4/N) is the identity on a lane that holds a normal float, +-0 or +-FLT_MAX. Every lane an FMAC or MAX/MINI writes is one of those
(fast path: exponent in [2,253]; slow path: clamped to +-0 / +-0x7F7FFFFF / an in-range normal; MAX/MINI return one of two normalised operands), so a
later FMAC/MAX/MINI that reads that lane in the same block can skip N4. This script walks each block's statements in execution order and keeps, per vf
register and for ACC, a 4-bit lane mask of "known normalised" lanes (bit c = lane c, the D4 convention of vu1_hot_ops.h):
  - set by fmacR / maxmini on their destination lanes; propagated by move; vf0 starts normalised and is re-set by the per-pair vf0 reset line;
  - cleared on the destination lanes of lq / lqi / ftoi / mr32 / applyDest / lane assignments, and for EVERYTHING on any statement it does not recognise
    (the upper/lower shadow-merge memcpy groups, any other touch of st.vf / st.acc);
  - every block (and every loop iteration) starts with nothing known (except vf0), so facts never cross a block entry.
The matching fmacR / maxmini call then gets NRM bits (1 = A operand, 2 = B operand, 4 = ACC) as a trailing template argument.
Usage: python tools/vu1gen/patch_nrm_hot.py [--vu0]"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
GEN = ROOT / "PS2Recomp/ps2xRuntime/src/lib/vu/generated"
TAG = "PERF-NR"
UNIT = 0 if "--vu0" in sys.argv else 1
HDR = re.compile(r"^static int (vu0?H_\d+)\(")


def rev4(b):
    return ((b & 1) << 3) | ((b & 2) << 1) | ((b & 4) >> 1) | ((b & 8) >> 3)


FMAC = re.compile(r"vuhot::fmacR<(\d+), (\d+), (\d+), (true|false), (\d+), (true|false)>\(vu, stat, (\w+), (\d+), (\d+), (\d+)\)")
MAXMINI = re.compile(r"vuhot::maxmini<(true|false), (\d+), (\d+), (\d+)>\(st, (\d+), (\d+), (\d+)\)")
FTOI = re.compile(r"vuhot::ftoi<(\d+), (\d+)>\(st, (\d+), (\d+)\)")
LQ = re.compile(r"vuhot::lq\(st, c\.vuData, c\.dataSize, (\d+), (\d+), (\d+), (-?\d+)\)")
LQI = re.compile(r"vuhot::lqi\(st, c\.vuData, c\.dataSize, (\d+), (\d+), (\d+)\)")
MOVE = re.compile(r"vuhot::move\(st, (\d+), (\d+), (\d+)\)")
MR32 = re.compile(r"vuhot::mr32\(st, (\d+), (\d+), (\d+)\)")
APPLY = re.compile(r"vuhot::applyDest\(st\.vf\[(\d+)\], res, (\d+)\)")
LANE = re.compile(r"st\.vf\[(\d+)\]\[(\d+)\]\s*=")
VF0RESET = "st.vf[0][0] = 0.0f; st.vf[0][1] = 0.0f; st.vf[0][2] = 0.0f; st.vf[0][3] = 1.0f;"
SHADOW_READ = re.compile(r"std::memcpy\((oldVf|upVf), st\.vf\[\d+\], 16\);")
SHADOW_WRITE = re.compile(r"std::memcpy\(st\.vf\[\d+\], (oldVf|upVf), 16\);")

stats = {"fmac": 0, "fmac_nrm": 0, "a": 0, "b": 0, "acc": 0, "mm": 0, "mm_nrm": 0}


def process(lines):
    m = [0] * 32
    m[0] = 0xF
    acc = 0

    def fresh():
        nonlocal acc
        for r in range(32):
            m[r] = 0
        m[0] = 0
        acc = 0

    out = []
    for ln in lines:
        if ln.strip() == "S = vu.m_cycle;":  # fused loop: each iteration starts from unknown contents
            fresh()
            m[0] = 0xF
            out.append(ln)
            continue
        mm = FMAC.search(ln)
        if mm:
            kind, src, bc = int(mm.group(1)), int(mm.group(2)), int(mm.group(3))
            toacc = mm.group(4) == "true"
            dest = int(mm.group(5))
            fs, ft, fd = int(mm.group(8)), int(mm.group(9)), int(mm.group(10))
            d4 = rev4(dest)
            nrm = 0
            if dest != 0:
                if (m[fs] & d4) == d4:
                    nrm |= 1
                if src == 3 and (m[ft] & d4) == d4:
                    nrm |= 2
                if src == 0 and (m[ft] >> bc) & 1:
                    nrm |= 2
                if kind in (2, 3) and (acc & d4) == d4:
                    nrm |= 4
            stats["fmac"] += 1
            if nrm:
                stats["fmac_nrm"] += 1
                stats["a"] += nrm & 1
                stats["b"] += (nrm >> 1) & 1
                stats["acc"] += (nrm >> 2) & 1
                ln = ln.replace("vuhot::fmacR<%s, %s, %s, %s, %s, %s>" % mm.groups()[:6], "vuhot::fmacR<%s, %s, %s, %s, %s, %s, %d>" % (mm.groups()[:6] + (nrm,)), 1)
            if dest != 0:
                if toacc:
                    acc |= d4
                elif fd == 0:
                    m[0] = 0
                else:
                    m[fd] |= d4
            out.append(ln)
            continue
        mm = MAXMINI.search(ln)
        if mm:
            src, bc, dest = int(mm.group(2)), int(mm.group(3)), int(mm.group(4))
            fs, ft, fd = int(mm.group(5)), int(mm.group(6)), int(mm.group(7))
            d4 = rev4(dest)
            nrm = 0
            if dest != 0:
                if (m[fs] & d4) == d4:
                    nrm |= 1
                if src == 3 and (m[ft] & d4) == d4:
                    nrm |= 2
                if src == 0 and (m[ft] >> bc) & 1:
                    nrm |= 2
            stats["mm"] += 1
            if nrm:
                stats["mm_nrm"] += 1
                ln = ln.replace("vuhot::maxmini<%s, %s, %s, %s>" % mm.groups()[:4], "vuhot::maxmini<%s, %s, %s, %s, %d>" % (mm.groups()[:4] + (nrm,)), 1)
            if dest != 0:
                if fd == 0:
                    m[0] = 0
                else:
                    m[fd] |= d4
            out.append(ln)
            continue
        mm = FTOI.search(ln)
        if mm:
            d4 = rev4(int(mm.group(2)))
            ft = int(mm.group(4))
            m[ft] &= ~d4 & 0xF
            out.append(ln)
            continue
        mm = LQ.search(ln)
        if mm:
            m[int(mm.group(2))] &= ~rev4(int(mm.group(1))) & 0xF
            out.append(ln)
            continue
        mm = LQI.search(ln)
        if mm:
            m[int(mm.group(2))] &= ~rev4(int(mm.group(1))) & 0xF
            out.append(ln)
            continue
        mm = MOVE.search(ln)
        if mm:
            d4 = rev4(int(mm.group(1)))
            t, s_ = int(mm.group(2)), int(mm.group(3))
            src_mask = m[s_]
            m[t] = (m[t] & ~d4 & 0xF) | (src_mask & d4)
            out.append(ln)
            continue
        mm = MR32.search(ln)
        if mm:
            m[int(mm.group(2))] &= ~rev4(int(mm.group(1))) & 0xF
            out.append(ln)
            continue
        mm = APPLY.search(ln)
        if mm:
            m[int(mm.group(1))] &= ~rev4(int(mm.group(2))) & 0xF
            out.append(ln)
            continue
        if VF0RESET in ln:
            m[0] = 0xF
            rest = ln.replace(VF0RESET, "")
            if "st.vf[" in rest:
                fresh()
            out.append(ln)
            continue
        if SHADOW_READ.search(ln):
            out.append(ln)
            continue
        if SHADOW_WRITE.search(ln):
            fresh()
            out.append(ln)
            continue
        if "st.vf[" in ln or "st.acc" in ln or ".vf[" in ln:
            ml = LANE.findall(ln)
            if ml and all(("st.vf[%s][%s]" % x) for x in ml) and "memcpy" not in ln and "st.acc" not in ln and len(ml) == ln.count("st.vf["):
                for r, l in ml:
                    m[int(r)] &= ~(1 << int(l)) & 0xF
            else:
                fresh()
        out.append(ln)
    return out


p = GEN / ("vu%d_hot_blocks.cpp" % UNIT)
t = p.read_text(encoding="utf-8", errors="surrogateescape")
if TAG in t:
    print("already patched")
    sys.exit(0)
lines = t.split("\n")
res = []
i = 0
nblk = 0
while i < len(lines):
    if HDR.match(lines[i]):
        j = i
        while lines[j] != "}":
            j += 1
        blk = lines[i:j + 1]
        if "fmacR<" in "\n".join(blk) or "maxmini<" in "\n".join(blk):
            nblk += 1
            blk = process(blk)
        res.extend(blk)
        i = j + 1
        continue
    res.append(lines[i])
    i += 1
out = "\n".join(res)
pfx = "vu0H_" if UNIT == 0 else "vuH_"
out = out.replace("static int %s0(" % pfx, "// " + TAG + ": provably redundant operand normalisation removed (tools/vu1gen/patch_nrm_hot.py)\nstatic int %s0(" % pfx, 1)
p.write_text(out, encoding="utf-8", errors="surrogateescape")
print("blocks processed:", nblk)
print("fmac calls: %(fmac)d, with NRM: %(fmac_nrm)d (A operand skips %(a)d, B operand %(b)d, ACC %(acc)d)" % stats)
print("maxmini calls: %(mm)d, with NRM: %(mm_nrm)d" % stats)
