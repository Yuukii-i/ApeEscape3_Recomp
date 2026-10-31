"""Level B step 4: teleport check. From the model's REAL state at loop boundary p (just before pass p executes), compute the state at boundary b > p with
closed-form stage values only, and compare every register, vi, status, memory and the cycle with the model's own snapshot at b.
Pass k (steady state) = 9 FMACs on: prod(k+1), R7(k)=T5(k)*Q(k), accw, S2Q(k+1), Wraw(k+1), T5(k+2) [MULA+MADDw], B(k+2)*vf16 [MULA], inner(k+2) [MADD];
stores q1.w(k-1) q4.xyz(k-1) q3(k) q2(k+1) q4.w(k+2).  Usage: python tools/vu1gen/lbtele.py [logs/vu1region.bin] [max_records]"""
import struct
import sys

sys.path.insert(0, "tools/vu1gen")
import corpus  # noqa: E402
import lbmodel as L  # noqa: E402

ONE, F255 = 0x3F800000, 0x437F0000


def s16(x):
    x &= 0xFFFF
    return x - 0x10000 if x & 0x8000 else x


def u32(mem, qw, lane):
    return struct.unpack_from("<I", mem, (qw & (len(mem) // 16 - 1)) * 16 + lane * 4)[0]


class Op:
    """one FMAC instruction instance: results per lane + the flag contributions the interpreter would record"""

    def __init__(self, kind, lanes, a, b, acc=None):
        self.res = {}
        cur = xf = mac = 0
        for c in lanes:
            ac = acc[c] if acc is not None else 0
            self.res[c] = L.fmac(kind, a[c], b[c], ac)
            ex, zn, pex, pzn = L.fmac_ex(kind, a[c], b[c], ac)
            lf = L.lane_flags(ex, zn)
            cur |= lf
            if kind in (2, 3):
                xf |= L.lane_flags(pex, pzn) & 0xF
            lane = 8 >> c
            mac |= (lane if lf & 1 else 0) | ((lane << 4) if lf & 2 else 0) | ((lane << 8) if lf & 4 else 0) | ((lane << 12) if lf & 8 else 0)
        self.cur, self.xf, self.mac = cur & 0xF, xf, mac

    @property
    def sticky(self):
        return self.cur | self.xf


def clamp(x):
    return L.maxmini(False, L.maxmini(True, x, 0), F255)


class Stages:
    """stage values of vertex t, computed once and cached; streams addressed from the boundary-p pointers"""

    def __init__(self, mem, vf, vi, p):
        self.mem, self.p = mem, p
        self.vf3 = [u32(mem, 1002, c) for c in range(4)]
        self.vf4 = [u32(mem, 1003, c) for c in range(4)]
        self.vf2 = [u32(mem, 1014, c) for c in range(4)]
        self.vf1z, self.vf1w = u32(mem, 1016, 2), u32(mem, 1016, 3)
        self.vf16 = list(vf[16])
        self.idxbase = vi[4] - (p + 2)
        self.s3base = vi[3] - (p + 2)
        self.s2base = vi[2] - (p + 1)
        self.cache = {}
        self.accw = Op(4, [3], [ONE] * 4, [self.vf1z] * 4)

    def idx(self, t):
        return s16(u32(self.mem, (self.idxbase + t) & 0xFFFF, 0))

    def v(self, t):
        r = self.cache.get(t)
        if r is not None:
            return r
        m = self.mem
        idx = self.idx(t)
        A = [u32(m, 636 + idx, c) for c in range(4)]
        B = [u32(m, 716 + idx, c) for c in range(4)]
        S3 = [u32(m, self.s3base + t, c) for c in range(4)]
        S2 = [u32(m, self.s2base + t, c) for c in range(4)]
        r = type("V", (), {})()
        r.idx, r.A, r.B, r.S3, r.S2 = idx, A, B, S3, S2
        r.mulaA = Op(4, range(4), self.vf3, A)                                   # MULA.xyzw ACC = vf3 * A
        r.T5op = Op(2, range(4), self.vf4, [A[3]] * 4, [r.mulaA.res[c] for c in range(4)])  # MADDw vf5 = ACC + vf4 * A.w
        r.T5 = [r.T5op.res[c] for c in range(4)]
        r.Q = L.divq(ONE, r.T5[3])
        r.di = L.div_di(ONE, r.T5[3])
        r.R7op = Op(4, range(3), r.T5, [r.Q] * 4)                                  # MULq.xyz  T5 * Q
        r.R7 = [r.R7op.res.get(c, 0) for c in range(3)]
        r.S2Qop = Op(4, range(3), S2, [r.Q] * 4)                                   # MULq.xyz  S2 * Q
        r.S2Q = [r.S2Qop.res[c] for c in range(3)]
        r.Wop = Op(2, [3], [self.vf1w] * 4, [r.Q] * 4, [self.accw.res[3]] * 4)     # MADDq.w  ACC.w + vf1.w * Q
        r.Wraw = r.Wop.res[3]
        r.BVop = Op(4, range(4), B, self.vf16)                                     # MULA.xyzw ACC = B * vf16
        r.inop = Op(2, range(4), self.vf2, self.vf16, [r.BVop.res[c] for c in range(4)])   # MADD vf11 = ACC + vf2 * vf16
        r.inner = [r.inop.res[c] for c in range(4)]
        r.prodop = Op(4, range(4), S3, r.inner)                                    # MUL.xyzw  S3 * inner
        r.prod = [r.prodop.res[c] for c in range(4)]
        self.cache[t] = r
        return r


def teleport(snap, b, mem_at_p):
    """snap: model snapshot at boundary p; returns predicted dict for boundary b (b >= p)"""
    p = snap["it"]
    vf = [list(r) for r in snap["vf"]]
    acc = list(snap["acc"])
    vi = list(snap["vi"])
    st = Stages(mem_at_p, vf, vi, p)
    out = {}
    stores = {}                       # (qw offset from base, lane) -> value
    base = vi[6] & 0xFFFF
    status = snap["status"]
    maclog = []
    for k in range(p, b):
        ops = [st.v(k + 1).prodop, st.v(k).R7op, st.accw, st.v(k + 1).S2Qop, st.v(k + 1).Wop, st.v(k + 2).mulaA, st.v(k + 2).T5op, st.v(k + 2).BVop, st.v(k + 2).inop]
        sticky = 0
        for o in ops:
            sticky |= o.sticky
        # low 4 = last op's flags, bits 6-9 = sticky OR, bits 4-5 cleared by the DIV landing (no DI in range), 10-11 untouched
        status = (status & 0xC00) | ((status & 0x3C0) | ((sticky & 0xF) << 6)) | ops[-1].cur
        maclog.append((snap["t"] + 15 * (k - p) + 11, ops[-1].mac))
        # stores of pass k
        wv = st.v(k - 1)
        stores[(4 * k - 3, 3)] = L.ftoi(clamp(wv.Wraw), 16)
        for c in range(3):
            stores[(4 * k, c)] = L.ftoi(wv.R7[c], 16)
        for c in range(4):
            stores[(4 * k + 3, c)] = L.ftoi(clamp(st.v(k).prod[c]), 1)
        for c in range(3):
            stores[(4 * k + 6, c)] = st.v(k + 1).S2Q[c]
        stores[(4 * k + 12, 3)] = st.v(k + 2).idx & 0xFFFF
    # state at boundary b
    v5, v4, v3 = st.v(b + 1), st.v(b - 1), st.v(b)
    vf[5] = list(v5.T5)
    vf[6] = [L.ftoi(v4.R7[c], 16) for c in range(3)] + [L.ftoi(clamp(v4.Wraw), 16)]
    vf[7] = list(v4.R7) + [clamp(v4.Wraw)]
    vf[8] = [clamp(v3.prod[c]) for c in range(4)]
    vf[9] = list(v3.T5[:3]) + [L.maxmini(True, v3.Wraw, 0)]
    vf[10] = list(v5.S3)
    vf[11] = list(v5.inner)
    vf[12] = list(v3.S2Q) + [snap["vf"][12][3]]
    acc = [v5.BVop.res[c] for c in range(4)]
    vi[2] += b - p
    vi[3] += b - p
    vi[4] += b - p
    vi[7] = st.v(b + 1).idx
    vi[9] += 4 * (b - p)
    return dict(vf=vf, acc=acc, q=v3.Q, pend=(st.v(b + 1).Q, st.v(b + 1).di), vi=vi, status=status, stores=stores, base=base, t=snap["t"] + 15 * (b - p), maclog=maclog)


class SnapModel(L.Model):
    def start(self, e):
        super().start(e)
        self.snaps = {}

    def pair(self, pc, pidx, vf, acc, q, I, vi, fdiv, t, mem):
        if (pc == 0x20F8 or pc == 0x2170) and pidx == 0:
            key = self.it if pc == 0x20F8 else self.it + 1      # tail entry = boundary after the last pass
            self.snaps[key] = dict(it=key, vf=[list(r) for r in vf], acc=list(acc), q=q, I=I, vi=list(vi), fdiv=fdiv, t=t, status=self.status,
                                   mem=bytes(mem), nmac=len(self.maclog))
        elif False:
            self.snaps[self.it] = dict(it=self.it, vf=[list(r) for r in vf], acc=list(acc), q=q, I=I, vi=list(vi), fdiv=fdiv, t=t, status=self.status,
                                       mem=bytes(mem), nmac=len(self.maclog))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = args[0] if args else "logs/vu1region.bin"
    maxn = int(args[1]) if len(args) > 1 else 10 ** 9
    code = next(p[8:] for tag, p in corpus.chunks("logs/vu1corpus.bin") if tag == b"CODE" and struct.unpack_from("<Q", p)[0] == L.CODE_GEN)
    m = SnapModel(code, L.load_blocks())
    n = tests = bad = 0
    why = {}
    shown = 0
    for e, x in L.records(path):
        if n >= maxn:
            break
        n += 1
        r = m.run(e)
        trips = (x["cycle"] - e["cycle"] - 74) // 15
        if trips < 5:
            continue
        maclog = [(t, mac) for (t, pc, mac) in r["maclog"] if pc == 0x2150]
        for p in (2, 3, 4, 6):
            if p + 1 > trips:
                continue
            for b in range(p + 1, trips + 2):
                sp, sb = m.snaps[p], m.snaps[b]
                tp = teleport(sp, b, sp["mem"])
                tests += 1
                probs = []
                for rg in range(1, 13):
                    for c in range(4):
                        if rg in (5, 6, 7, 8, 9, 10, 11) or (rg == 12 and c < 3):
                            if tp["vf"][rg][c] != sb["vf"][rg][c]:
                                probs.append("vf%d.%s" % (rg, "xyzw"[c]))
                if tp["acc"] != sb["acc"]:
                    probs.append("acc")
                if tp["q"] != sb["q"]:
                    probs.append("q")
                fd = sb["fdiv"]
                if fd is None or fd[1] != tp["pend"][0] or (fd[0] - sb["t"]) != 6:
                    probs.append("fdiv")
                if tp["vi"][1:] != sb["vi"][1:]:
                    probs.append("vi" + ",".join(str(i) for i in range(1, 16) if tp["vi"][i] != sb["vi"][i]))
                if tp["status"] != sb["status"]:
                    probs.append("status %03X/%03X" % (tp["status"], sb["status"]))
                if tp["t"] != sb["t"]:
                    probs.append("t")
                # memory: apply stores to mem at p and compare with mem at b
                mm = bytearray(sp["mem"])
                for (qo, lane), v in tp["stores"].items():
                    struct.pack_into("<I", mm, (((tp["base"] + qo) & (len(mm) // 16 - 1)) * 16) + lane * 4, v)
                if bytes(mm) != sb["mem"]:
                    probs.append("mem")
                # MAC ring pushes of passes p..b-1
                want = [(t - 0, mac) for (t, mac) in maclog if sp["t"] <= t < sb["t"]]
                if want != tp["maclog"]:
                    probs.append("mac")
                if probs:
                    bad += 1
                    for pr in probs:
                        k = pr.split()[0]
                        why[k] = why.get(k, 0) + 1
                    if shown < 6:
                        shown += 1
                        print("rec %d p=%d b=%d: %s" % (n, p, b, "; ".join(probs[:8])))
    print("records=%d teleport tests=%d bad=%d" % (n, tests, bad))
    for k, v in sorted(why.items(), key=lambda kv: -kv[1])[:12]:
        print("  %6d  %s" % (v, k))


if __name__ == "__main__":
    main()
