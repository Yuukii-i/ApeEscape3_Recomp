"""Level B step 1: functional model of the VU1 skinned-vertex loop region [1FE0,2200) checked against logs/vu1region.bin (PROBE-REGION).
Runs the real instructions from the corpus code image with the interpreter's rules (RTZ fused FMAC, operand/result normalisation, DIV latency 7,
branch delay slot, per-block issue cycles from vublk2) and compares memory diff, vf, vi, acc, q, pc and cycle with the recorded exit.
Usage: python tools/vu1gen/lbmodel.py [logs/vu1region.bin] [max_records]"""
import re
import struct
import sys
from fractions import Fraction

sys.path.insert(0, "tools/vu1gen")
import corpus  # noqa: E402

CODE_GEN = 5566
ST_SIZE = 664
REGION = (0x1FE0, 0x2200)
BLK_FILE = "logs/vublk2_u1_86503d3905e35276.txt"
HOT_FILE = "PS2Recomp/ps2xRuntime/src/lib/vu/generated/vu1_hot_blocks.cpp"
M32 = 0xFFFFFFFF


# ---------------------------------------------------------------- float helpers
def norm(b):
    e = (b >> 23) & 0xFF
    if e == 0:
        return b & 0x80000000
    if e == 0xFF:
        return (b & 0x80000000) | 0x7F7FFFFF
    return b


def fr(b):
    s = -1 if b >> 31 else 1
    e = (b >> 23) & 0xFF
    m = b & 0x7FFFFF
    if e == 0:
        return Fraction(0)
    return s * Fraction(m | 0x800000) * Fraction(2) ** (e - 150)


def sgn(b):
    return b >> 31


def enc(x, zneg):
    """Fraction -> float32 bits, truncated toward zero, VU flush (tiny -> +-0) and clamp (huge -> +-FLT_MAX)."""
    if x == 0:
        return 0x80000000 if zneg else 0
    neg = x < 0
    m = -x if neg else x
    if m < Fraction(1, 1 << 126):
        return 0x80000000 if neg else 0
    e = m.numerator.bit_length() - m.denominator.bit_length()
    while Fraction(2) ** e > m:
        e -= 1
    while Fraction(2) ** (e + 1) <= m:
        e += 1
    if e > 127:
        bits = 0x7F7FFFFF
    else:
        mant = int(m / (Fraction(2) ** (e - 23)))  # floor: m is positive
        bits = ((e + 127) << 23) | (mant & 0x7FFFFF)
    return bits | (0x80000000 if neg else 0)


def fadd(fa, sa, fb, sb):
    """exact sum with IEEE zero sign (round toward zero)"""
    s = fa + fb
    if s == 0:
        return s, bool(fa == 0 and fb == 0 and sa and sb)
    return s, False


def fmac(kind, a, b, ac):
    a, b = norm(a), norm(b)
    fa, fb = fr(a), fr(b)
    sp = sgn(a) ^ sgn(b)
    if kind == 4:
        return enc(fa * fb, sp)
    if kind == 0:
        s, z = fadd(fa, sgn(a), fb, sgn(b))
        return enc(s, z)
    if kind == 1:
        s, z = fadd(fa, sgn(a), -fb, sgn(b) ^ 1)
        return enc(s, z)
    ac = norm(ac)
    fc = fr(ac)
    if kind == 2:
        s, z = fadd(fc, sgn(ac), fa * fb, sp)
        return enc(s, z)
    s, z = fadd(fc, sgn(ac), -(fa * fb), sp ^ 1)
    return enc(s, z)


FLT_MIN = Fraction(1, 1 << 126)
FLT_MAX = Fraction((1 << 24) - 1, 1 << 23) * Fraction(2) ** 127


def fmac_ex(kind, a, b, ac):
    """exact result, its zero sign, and the exact product (for the MADD/MSUB sticky extra flags)"""
    a, b = norm(a), norm(b)
    fa, fb = fr(a), fr(b)
    sp = bool(sgn(a) ^ sgn(b))
    if kind == 4:
        return fa * fb, sp, fa * fb, sp
    if kind == 0:
        return (*fadd(fa, sgn(a), fb, sgn(b)), fa * fb, sp)
    if kind == 1:
        return (*fadd(fa, sgn(a), -fb, sgn(b) ^ 1), fa * fb, sp)
    ac = norm(ac)
    fc = fr(ac)
    if kind == 2:
        return (*fadd(fc, sgn(ac), fa * fb, int(sp)), fa * fb, sp)
    return (*fadd(fc, sgn(ac), -(fa * fb), int(sp) ^ 1), fa * fb, sp)


def lane_flags(ex, zneg):
    """VU1Interpreter flagsOf: 1 = zero, 2 = sign, 4 = underflow, 8 = overflow"""
    f = 2 if (ex < 0 or (ex == 0 and zneg)) else 0
    m = abs(ex)
    if m == 0:
        f |= 1
    elif m > FLT_MAX:
        f |= 8
    elif m < FLT_MIN:
        f |= 5
    return f


def div_di(num, den):
    num, den = norm(num), norm(den)
    if den & 0x7FFFFFFF == 0:
        return 0x10 if num & 0x7FFFFFFF == 0 else 0x20
    return 0


def maxmini(is_max, a, b):
    a, b = norm(a), norm(b)
    fa, fb = fr(a), fr(b)
    if is_max:
        return a if fa > fb else b
    return a if fa < fb else b


def ftoi(a, scale):
    a = norm(a)
    v = fr(a) * scale
    t = int(v)  # toward zero
    if v >= 2147483647:
        t = 2147483647
    elif v <= -2147483648:
        t = -2147483648
    return t & M32


def itof(a, shift):
    v = a - (1 << 32) if a >> 31 else a
    return enc(Fraction(v, 1 << shift), v < 0 and False)


def divq(num, den):
    num, den = norm(num), norm(den)
    if den & 0x7FFFFFFF == 0:
        neg = sgn(num) != sgn(den)
        return 0xFF7FFFFF if neg else 0x7F7FFFFF
    fn, fd = fr(num), fr(den)
    return enc(fn / fd, sgn(num) ^ sgn(den))


# ---------------------------------------------------------------- tables
BCN = "xyzw"
KIND_OF = {0: 0, 1: 1, 2: 2, 3: 3}  # ADD SUB MADD MSUB by group index (op>>2), MAX/MINI handled separately


def upper_decode(u):
    """-> dict(op=name-ish tuple) or None for NOP. Returns (cls, kind, src, bc, toacc, dest, fs, ft, fd)"""
    op = u & 0x3F
    dest = (u >> 21) & 15
    ft = (u >> 16) & 31
    fs = (u >> 11) & 31
    fd = (u >> 6) & 31
    if op >= 0x3C:
        e = (u & 3) | ((u >> 4) & 0x7C)
        if e == 0x2F:
            return None
        if e == 0x1F:
            return ("clip", fs, ft)
        if e == 0x1D:
            return ("abs", dest, fs, ft)
        grp, b = e >> 2, e & 3
        if 0x10 <= e <= 0x17:
            k = e - 0x10
            return ("cvt", "itof" if k < 4 else "ftoi", [0, 4, 12, 15][k & 3], dest, fs, ft)
        if e < 0x10:  # ADDA SUBA MADDA MSUBA bc
            return ("fmac", grp, "bc", b, True, dest, fs, ft, 0)
        if 0x18 <= e <= 0x1B:
            return ("fmac", 4, "bc", b, True, dest, fs, ft, 0)
        tab = {0x1C: (4, "q"), 0x1E: (4, "i"), 0x20: (0, "q"), 0x21: (2, "q"), 0x22: (0, "i"), 0x23: (2, "i"), 0x24: (1, "q"), 0x25: (3, "q"),
               0x26: (1, "i"), 0x27: (3, "i"), 0x28: (0, "v"), 0x29: (2, "v"), 0x2A: (4, "v"), 0x2C: (1, "v"), 0x2D: (3, "v")}
        if e in tab:
            return ("fmac", tab[e][0], tab[e][1], 0, True, dest, fs, ft, 0)
        raise ValueError("upper special %02X" % e)
    if op < 0x18:
        grp, b = op >> 2, op & 3
        if grp < 4:
            return ("fmac", grp, "bc", b, False, dest, fs, ft, fd)
        return ("mm", grp == 4, "bc", b, dest, fs, ft, fd)
    if op < 0x1C:
        return ("fmac", 4, "bc", op & 3, False, dest, fs, ft, fd)
    tab = {0x1C: ("fmac", 4, "q"), 0x1D: ("mm", True, "i"), 0x1E: ("fmac", 4, "i"), 0x1F: ("mm", False, "i"), 0x20: ("fmac", 0, "q"), 0x21: ("fmac", 2, "q"),
           0x22: ("fmac", 0, "i"), 0x23: ("fmac", 2, "i"), 0x24: ("fmac", 1, "q"), 0x25: ("fmac", 3, "q"), 0x26: ("fmac", 1, "i"), 0x27: ("fmac", 3, "i"),
           0x28: ("fmac", 0, "v"), 0x29: ("fmac", 2, "v"), 0x2A: ("fmac", 4, "v"), 0x2B: ("mm", True, "v"), 0x2C: ("fmac", 1, "v"), 0x2D: ("fmac", 3, "v"),
           0x2F: ("mm", False, "v")}
    if op not in tab:
        raise ValueError("upper op %02X" % op)
    t = tab[op]
    if t[0] == "fmac":
        return ("fmac", t[1], t[2], 0, False, dest, fs, ft, fd)
    return ("mm", t[1], t[2], 0, dest, fs, ft, fd)


def simm11(x):
    x &= 0x7FF
    return x - 0x800 if x & 0x400 else x


# ---------------------------------------------------------------- block metadata
def load_blocks():
    blk = {}
    cur = None
    import glob
    for fn in [BLK_FILE] + sorted(glob.glob("logs/vublk2_u1_86503d3905e35276_*.txt")):
      for ln in open(fn, encoding="utf-8", errors="replace"):
        m = re.match(r"B pc=([0-9A-F]+) sig=([0-9a-f]+) exitsig=([0-9a-f]+) n=(\d+)", ln)
        if m:
            cur = (int(m.group(1), 16), m.group(2))
            if cur in blk:  # the first file wins (the current dump carries cyc=)
                cur = None
                continue
            blk[cur] = dict(exit=m.group(3), n=int(m.group(4)))
            mc = re.search(r"cyc=(\d+)", ln)
            if mc:
                blk[cur]["cycles"] = int(mc.group(1))
            continue
        if cur is not None and ln.startswith("  issue:"):
            blk[cur]["issue"] = [int(x) for x in ln.split()[1:]]
    for ln in open(HOT_FILE, encoding="utf-8", errors="replace"):
        m = re.search(r"// pc=([0-9A-F]+) entry=([0-9a-f]+) exit=([0-9a-f]+) n=(\d+) cycles=(\d+)", ln)
        if m:
            k = (int(m.group(1), 16), m.group(2))
            if k in blk:
                blk[k]["cycles"] = int(m.group(5))
    return blk


# ---------------------------------------------------------------- record reader
class Rd:
    def __init__(self, b):
        self.b, self.o = b, 0

    def u(self, f):
        v = struct.unpack_from("<" + f, self.b, self.o)
        self.o += struct.calcsize("<" + f)
        return v if len(v) > 1 else v[0]

    def raw(self, n):
        v = self.b[self.o:self.o + n]
        self.o += n
        return v


def read_pending(r):
    p = {}
    p["vf"] = [(r.u("q"), r.u("B"), r.u("B"), r.u("4I")) for _ in range(r.u("I"))]
    p["vi"] = [(r.u("q"), r.u("B"), r.u("i")) for _ in range(r.u("I"))]
    p["acc"] = [(r.u("q"), r.u("B"), r.u("4I")) for _ in range(r.u("I"))]
    p["flag"] = [(r.u("q"), r.u("q"), r.u("4I"), r.u("B")) for _ in range(r.u("I"))]
    p["store"] = [(r.u("q"), r.u("I"), r.u("4I"), r.u("B")) for _ in range(r.u("I"))]
    p["fdiv"] = (r.u("B"), r.u("q"), r.u("I"), r.u("I"))
    p["efu"] = [(r.u("B"), r.u("q"), r.u("I"), r.u("I")) for _ in range(2)]
    p["xg"] = r.u("B")
    return p


def st_decode(b):
    return dict(vf=list(struct.unpack_from("<128I", b, 0)), vi=list(struct.unpack_from("<16i", b, 512)), acc=list(struct.unpack_from("<4I", b, 576)),
                q=struct.unpack_from("<I", b, 592)[0], p=struct.unpack_from("<I", b, 596)[0], i=struct.unpack_from("<I", b, 600)[0], pc=struct.unpack_from("<I", b, 608)[0],
                mac=struct.unpack_from("<I", b, 612)[0], clip=struct.unpack_from("<I", b, 616)[0], status=struct.unpack_from("<I", b, 620)[0], top=struct.unpack_from("<I", b, 640)[0])


def records(path):
    for tag, p in corpus.chunks(path):
        if tag != b"RGN ":
            continue
        r = Rd(p)
        e = dict(pc=r.u("I"), cycle=r.u("Q"))
        e["st"] = st_decode(r.raw(ST_SIZE))
        dsz = r.u("I")
        e["mem"] = bytearray(r.raw(dsz))
        e["pend"] = read_pending(r)
        x = dict(pc=r.u("I"), cycle=r.u("Q"))
        x["st"] = st_decode(r.raw(ST_SIZE))
        nd = r.u("I")
        x["diff"] = {}
        for _ in range(nd):
            q = r.u("I")
            x["diff"][q] = bytes(r.raw(16))
        x["pend"] = read_pending(r)
        assert r.o == len(p), "record parse mismatch %d != %d" % (r.o, len(p))
        yield e, x


# ---------------------------------------------------------------- the model
class Model:
    def __init__(self, code, blk):
        self.code, self.blk = code, blk
        self.warn = {}

    def w(self, k):
        self.warn[k] = self.warn.get(k, 0) + 1

    # provenance hooks (identity here; tools/vu1gen/lbprov.py overrides them)
    def ld(self, pc, c, addr, v):
        return v

    def stv(self, pc, addr, c, v, kind):
        pass

    def pair(self, pc, pidx, vf, acc, q, I, vi, fdiv, t, mem):
        pass

    def start(self, e):
        self.it = 0
        self.cur_pc = 0

    def run(self, e, pc=0x1FE0, sig="ed9ddb4fd6ac295f", region=None, rings=None):
        st = e["st"]
        vf = [list(st["vf"][4 * r:4 * r + 4]) for r in range(32)]
        vf[0] = [0, 0, 0, 0x3F800000]
        vi = list(st["vi"])
        acc = list(st["acc"])
        q, I = st["q"], st["i"]
        mem = bytearray(e["mem"])
        dsz = len(mem)
        cycle0 = e["cycle"]
        pend = e["pend"]
        for rel, reg, mask, val in pend["vf"]:  # pending writes land eventually (readers interlock)
            for c in range(4):
                if mask & (8 >> c):
                    vf[reg][c] = val[c]
        for rel, reg, val in pend["vi"]:
            vi[reg] = val
        for rel, mask, val in pend["acc"]:
            for c in range(4):
                if mask & (8 >> c):
                    acc[c] = val[c]
        for rel, addr, words, mask in pend["store"]:
            for c in range(4):
                if mask & (8 >> c):
                    struct.pack_into("<I", mem, addr + 4 * c, words[c])
        fdiv = None
        if pend["fdiv"][0]:
            fdiv = (cycle0 + pend["fdiv"][1], pend["fdiv"][2], pend["fdiv"][3])
        self.status = st["status"]
        self.maclog = []
        region = region or REGION
        S = cycle0
        bk = None
        pidx = 0
        branch = None
        prev_ialu = {}
        trace_pairs = 0
        self.path = []
        self.dbg = []
        if rings is not None:  # probe v3: the real ring contents and working clip at entry (cycles are absolute)
            self.clipring = [(-100, rings["clip"]["base"])] + list(rings["clip"]["ent"])
            self.wclip = rings["wclip"]
        else:
            self.clipring = [(-100, st["clip"])]
            self.wclip = st["clip"]
        self.top = st["top"]
        self.start(e)
        while True:
            if bk is None:
                bk = self.blk.get((pc, sig))
                if bk is None or "issue" not in bk or "cycles" not in bk:
                    raise RuntimeError("no block meta for pc=%04X sig=%s" % (pc, sig))
                pidx = 0
                self.path.append(pc)
            t = S + bk["issue"][pidx]
            if fdiv is not None and fdiv[0] <= t:  # Q landing before the pair issues
                q = fdiv[1]
                di = fdiv[2] & 0x30
                self.status = (self.status & 0xFCF) | di | (di << 6)
                fdiv = None
            lo, up = struct.unpack_from("<II", self.code, pc)
            self.cur_pc = pc
            if pc == 0x20F8:
                self.it += 1
            self.pair(pc, pidx, vf, acc, q, I, vi, fdiv, t, mem)
            cvf = []          # staged vf lane writes (reg, lane, bits)
            vi_old = {}
            new_branch = None
            ialu_now = {}
            Iload = None
            ud = upper_decode(up)
            # ---- upper
            uw = []
            uacc = []
            if ud is not None:
                if ud[0] == "fmac":
                    _, kind, src, bc, toacc, dest, fs, ft, fd = ud
                    cur = xf = mac = 0
                    for c in range(4):
                        if not dest & (8 >> c):
                            continue
                        a = vf[fs][c]
                        if src == "bc":
                            b = vf[ft][bc]
                        elif src == "q":
                            b = q
                        elif src == "i":
                            b = I
                        else:
                            b = vf[ft][c]
                        r = fmac(kind, a, b, acc[c])
                        (uacc if toacc else uw).append((0 if toacc else fd, c, r))
                        ex, zn, pex, pzn = fmac_ex(kind, int(a), int(b), int(acc[c]))
                        lf = lane_flags(ex, zn)
                        cur |= lf
                        if kind in (2, 3):
                            xf |= lane_flags(pex, pzn) & 0xF
                        lane = 8 >> c
                        mac |= (lane if lf & 1 else 0) | ((lane << 4) if lf & 2 else 0) | ((lane << 8) if lf & 4 else 0) | ((lane << 12) if lf & 8 else 0)
                    if dest:
                        cur &= 0xF
                        self.status = (self.status & 0xFF0) | cur | ((cur | xf) << 6)
                        self.maclog.append((t, pc, mac))
                elif ud[0] == "mm":
                    _, is_max, src, bc, dest, fs, ft, fd = ud
                    for c in range(4):
                        if not dest & (8 >> c):
                            continue
                        b = vf[ft][bc] if src == "bc" else (I if src == "i" else vf[ft][c])
                        uw.append((fd, c, maxmini(is_max, vf[fs][c], b)))
                elif ud[0] == "clip":
                    _, cfs, cft = ud
                    wbits = vf[cft][3]
                    limit = (wbits & 0x7FFFFFFF) if (wbits & 0x7F800000) else 0x007FFFFF
                    fl = 0
                    for k in range(3):
                        v_ = vf[cfs][k]
                        for sgn_, mask_ in ((0, 0), (1, 0x80000000)):
                            o_ = (v_ ^ mask_) & 0xFFFFFFFF
                            o_ = o_ - (1 << 32) if o_ & 0x80000000 else o_
                            if o_ > limit:
                                fl |= 1 << (2 * k + sgn_)
                    self.wclip = ((self.wclip << 6) | fl) & 0xFFFFFF
                    self.clipring.append((t, self.wclip))
                elif ud[0] == "abs":
                    _, adest, afs, aft = ud
                    for c in range(4):
                        if adest & (8 >> c):
                            uw.append((aft, c, vf[afs][c] & 0x7FFFFFFF))
                elif ud[0] == "cvt":
                    _, name, sh, dest, fs, ft = ud
                    for c in range(4):
                        if not dest & (8 >> c):
                            continue
                        if name == "ftoi":
                            uw.append((ft, c, ftoi(vf[fs][c], 1 << sh)))
                        else:
                            uw.append((ft, c, itof(vf[fs][c], sh)))
            # ---- lower
            lw = []        # vf lane writes
            stores = []    # (addr, c, bits)
            if (up >> 31) & 1:
                Iload = lo
            else:
                op = (lo >> 25) & 0x7F
                dest = (lo >> 21) & 15
                ft = (lo >> 16) & 31
                fs = (lo >> 11) & 31
                fd = (lo >> 6) & 31
                imm = simm11(lo)
                imm15 = (lo & 0x7FF) | ((lo >> 10) & 0x7800)
                if op == 0x00:  # LQ
                    a = ((vi[fs] + imm) * 16) & (dsz - 1)
                    for c in range(4):
                        if dest & (8 >> c):
                            lw.append((ft, c, self.ld(pc, c, a + 4 * c, struct.unpack_from("<I", mem, a + 4 * c)[0])))
                elif op == 0x01:  # SQ
                    a = ((vi[ft] + imm) * 16) & (dsz - 1)
                    for c in range(4):
                        if dest & (8 >> c):
                            stores.append((a, c, vf[fs][c], pc, "f"))
                elif op == 0x04:  # ILW
                    a = ((vi[fs] + imm) * 16) & (dsz - 1)
                    comp = 0 if dest & 8 else 1 if dest & 4 else 2 if dest & 2 else 3
                    v = struct.unpack_from("<I", mem, a + 4 * comp)[0] & 0xFFFF
                    if ft:
                        ialu_now[ft] = ("ld", v - 0x10000 if v & 0x8000 else v)
                elif op == 0x05:  # ISW
                    a = ((vi[fs] + imm) * 16) & (dsz - 1)
                    val = vi[ft] & 0xFFFF
                    for c in range(4):
                        if dest & (8 >> c):
                            stores.append((a, c, val, pc, "i"))
                elif op == 0x08:  # IADDIU
                    if ft:
                        ialu_now[ft] = ("alu", _s16(vi[fs] + imm15))
                elif op == 0x09:
                    if ft:
                        ialu_now[ft] = ("alu", _s16(vi[fs] - imm15))
                elif op in (0x28, 0x29):  # IBEQ / IBNE
                    def rv(r):
                        if r in prev_ialu and prev_ialu[r][0] == "alu":
                            return prev_ialu[r][2]   # branch reads the value before the immediately preceding ALU write
                        return vi[r]
                    cond = (rv(ft) & 0xFFFF) == (rv(fs) & 0xFFFF)
                    if (op == 0x29) ^ cond:
                        new_branch = (pc + 8 + imm * 8) & 0x3FFF
                elif op in (0x2C, 0x2D, 0x2E, 0x2F):  # IBLTZ IBGTZ IBLEZ IBGEZ
                    sv = prev_ialu[fs][2] if (fs in prev_ialu and prev_ialu[fs][0] == "alu") else vi[fs]
                    sv &= 0xFFFF
                    sv = sv - 0x10000 if sv & 0x8000 else sv
                    cond = {0x2C: sv < 0, 0x2D: sv > 0, 0x2E: sv <= 0, 0x2F: sv >= 0}[op]
                    if cond:
                        new_branch = (pc + 8 + imm * 8) & 0x3FFF
                elif op == 0x21:  # BAL
                    if ft:
                        ialu_now[ft] = ("alu", (pc + 16) // 8)
                    new_branch = (pc + 8 + imm * 8) & 0x3FFF
                elif op == 0x1C:  # FCGET
                    vis = self.clipring[0][1]
                    for (tc, vc) in self.clipring:
                        if tc + 4 <= t:
                            vis = vc
                    if ft:
                        ialu_now[ft] = ("ld", vis & 0xFFF)
                elif op in (0x12, 0x13, 0x10):  # FCAND FCOR FCEQ
                    vis = self.clipring[0][1]
                    for (tc, vc) in self.clipring:
                        if tc + 4 <= t:
                            vis = vc
                    i24 = lo & 0xFFFFFF
                    res = {0x12: (vis & i24) != 0, 0x13: (vis | i24) == 0xFFFFFF, 0x10: (vis & 0xFFFFFF) == i24}[op]
                    ialu_now[1] = ("ld", 1 if res else 0)  # the interpreter writes vi1 directly: a branch right after sees the new value
                    self.dbg.append((pc, t - cycle0, hex(vis), hex(i24), res))
                elif op == 0x24:  # JR
                    new_branch = (vi[fs] * 8) & 0x3FFF
                elif op == 0x20:
                    new_branch = (pc + 8 + imm * 8) & 0x3FFF
                elif op == 0x40:
                    o6 = lo & 0x3F
                    if o6 >= 0x3C:
                        ee = (lo & 3) | ((lo >> 4) & 0x7C)
                        if ee == 0x30:  # MOVE
                            for c in range(4):
                                if dest & (8 >> c):
                                    lw.append((ft, c, vf[fs][c]))
                        elif ee == 0x31:  # MR32
                            for c in range(4):
                                if dest & (8 >> c):
                                    lw.append((ft, c, vf[fs][(c + 1) & 3]))
                        elif ee == 0x34:  # LQI
                            a = ((vi[fs] & 0xFFFF) * 16) & (dsz - 1)
                            for c in range(4):
                                if dest & (8 >> c):
                                    lw.append((ft, c, self.ld(pc, c, a + 4 * c, struct.unpack_from("<I", mem, a + 4 * c)[0])))
                            if fs:
                                ialu_now[fs] = ("ld", _s16(vi[fs] + 1))
                        elif ee == 0x38:  # DIV
                            fsf, ftf = dest & 3, (dest >> 2) & 3
                            val = divq(vf[fs][fsf], vf[ft][ftf])
                            if fdiv is not None:
                                self.w("div_overlap")
                            fdiv = (t + 7, val, div_di(vf[fs][fsf], vf[ft][ftf]))
                        elif ee == 0x35:  # SQI
                            a = ((vi[ft] & 0xFFFF) * 16) & (dsz - 1)
                            for c in range(4):
                                if dest & (8 >> c):
                                    stores.append((a, c, vf[fs][c], pc, "f"))
                            if ft:
                                ialu_now[ft] = ("ld", _s16(vi[ft] + 1))
                        elif ee == 0x3D:  # MFIR
                            for c in range(4):
                                if dest & (8 >> c):
                                    lw.append((ft, c, _s16(vi[fs]) & 0xFFFFFFFF))
                        elif ee == 0x3C:  # MTIR
                            if ft:
                                ialu_now[ft] = ("alu", _s16(vf[fs][(lo >> 21) & 3] & 0xFFFF))
                        elif ee == 0x68:  # XTOP
                            if ft:
                                ialu_now[ft] = ("alu", self.top & 0x3FF)
                        elif ee == 0x3B:  # WAITQ
                            pass
                        elif ee == 0x6C:  # XGKICK
                            pass
                        else:
                            raise ValueError("lower special %02X at %04X" % (ee, pc))
                    else:
                        a, b = vi[fs], vi[ft]
                        if o6 == 0x30 and fd:
                            ialu_now[fd] = ("alu", _s16(a + b))
                        elif o6 == 0x31 and fd:
                            ialu_now[fd] = ("alu", _s16(a - b))
                        elif o6 == 0x34 and fd:
                            ialu_now[fd] = ("alu", _s16((a & b) & 0xFFFF))
                        elif o6 == 0x35 and fd:
                            ialu_now[fd] = ("alu", _s16((a | b) & 0xFFFF))
                        elif o6 == 0x32:
                            if ft:
                                ialu_now[ft] = ("alu", _s16(a + (fd - 32 if fd & 16 else fd)))
                        else:
                            raise ValueError("lower sub %02X at %04X" % (o6, pc))
                else:
                    raise ValueError("lower op %02X at %04X" % (op, pc))
            # ---- commit (vf lane conflicts: report)
            seen = {}
            for (r, c, v) in lw + uw:
                if r == 0:
                    continue
                if (r, c) in seen:
                    self.w("vf_conflict")
                seen[(r, c)] = v
            for (r, c, v) in lw:
                if r:
                    vf[r][c] = v
            for (r, c, v) in uw:
                if r:
                    vf[r][c] = v
            for (_, c, v) in uacc:
                acc[c] = v
            for (a, c, v, spc, kind) in stores:
                struct.pack_into("<I", mem, a + 4 * c, v)
                self.stv(spc, a, c, v, kind)
            prev_next = {}
            for r, (kind, v) in ialu_now.items():
                prev_next[r] = (kind, v, vi[r])
                vi[r] = v
            prev_ialu = prev_next
            if Iload is not None:
                I = Iload
            # ---- pc / delay slot
            was_branch = branch
            if was_branch is not None:   # this pair was the delay slot
                npc = was_branch
                branch = None
                if new_branch is not None:
                    self.w("branch_in_delay")
            else:
                npc = (pc + 8) & 0x3FFF
                branch = new_branch
            pidx += 1
            pc_next = npc
            if pidx == bk["n"]:
                S += bk["cycles"]
                sig = bk["exit"]
                bk = None
            pc = pc_next
            trace_pairs += 1
            if branch is None and not (region[0] <= pc < region[1]):
                break
            if trace_pairs > 60000:
                raise RuntimeError("runaway")
        return dict(vf=vf, vi=vi, acc=acc, q=q, I=I, mem=mem, pc=pc, cycle=S, fdiv=fdiv, status=self.status, maclog=self.maclog)


def _s16(v):
    v &= 0xFFFF
    return v - 0x10000 if v & 0x8000 else v


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "logs/vu1region.bin"
    maxn = int(sys.argv[2]) if len(sys.argv) > 2 else 10 ** 9
    code = None
    for tag, p in corpus.chunks("logs/vu1corpus.bin"):
        if tag == b"CODE" and struct.unpack_from("<Q", p)[0] == CODE_GEN:
            code = p[8:]
            break
    blk = load_blocks()
    m = Model(code, blk)
    n = bad = 0
    why = {}
    trips = {}
    for e, x in records(path):
        if n >= maxn:
            break
        n += 1
        try:
            r = m.run(e)
        except Exception as ex:  # noqa: BLE001
            bad += 1
            why["EXC " + str(ex)[:60]] = why.get("EXC " + str(ex)[:60], 0) + 1
            continue
        probs = []
        xs = x["st"]
        # memory
        diff = {}
        for qd in range(len(e["mem"]) // 16):
            if r["mem"][qd * 16:qd * 16 + 16] != e["mem"][qd * 16:qd * 16 + 16]:
                diff[qd] = bytes(r["mem"][qd * 16:qd * 16 + 16])
        if diff != x["diff"]:
            probs.append("mem(model %d qw, rec %d qw, firstbad %s)" % (len(diff), len(x["diff"]), sorted(set(diff) ^ set(x["diff"]) | {k for k in diff if k in x["diff"] and diff[k] != x["diff"][k]})[:3]))
        for rg in range(32):
            if r["vf"][rg] != list(xs["vf"][4 * rg:4 * rg + 4]) and rg:
                probs.append("vf%d" % rg)
        if r["vi"][1:] != xs["vi"][1:]:
            probs.append("vi " + ",".join("%d:%d/%d" % (i, r["vi"][i], xs["vi"][i]) for i in range(1, 16) if r["vi"][i] != xs["vi"][i]))
        if r["acc"] != xs["acc"]:
            probs.append("acc")
        expq = xs["q"]
        if r["q"] != expq:
            probs.append("q %08X/%08X" % (r["q"], expq))
        if r["status"] != xs["status"]:
            probs.append("status %03X/%03X" % (r["status"], xs["status"]))
        if r["pc"] != x["pc"]:
            probs.append("pc %04X/%04X" % (r["pc"], x["pc"]))
        if r["cycle"] != x["cycle"]:
            probs.append("cycle %d/%d" % (r["cycle"] - e["cycle"], x["cycle"] - e["cycle"]))
        if probs:
            bad += 1
            for p_ in probs[:3]:
                why[p_.split()[0]] = why.get(p_.split()[0], 0) + 1
            if bad <= 5:
                print("record %d mismatches: %s" % (n, "; ".join(probs[:6])))
    print("records=%d bad=%d" % (n, bad))
    for k, v in sorted(why.items(), key=lambda kv: -kv[1]):
        print("  %5d  %s" % (v, k))
    print("model warnings:", m.warn)


if __name__ == "__main__":
    main()
