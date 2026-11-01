"""Clip machine, per-vertex stores: evaluate the closed form from the logged load values and compare with every float store of the loop (2538 ST, 2598 RGBA,
25A0 / 25B0 XYZ + w). Usage: python tools/vu1gen/vcheck1.py [entry hex, default 2440] [records]"""
import collections
import struct
import sys

sys.path.insert(0, "tools/vu1gen")
import corpus  # noqa: E402
import lbmodel as L  # noqa: E402
import lbprov as P  # noqa: E402
import regions as R  # noqa: E402
import vprov as V  # noqa: E402

fmac, maxmini, ftoi, divq = P._o["fmac"], P._o["maxmini"], P._o["ftoi"], P._o["divq"]
ONE, F255, F2048 = 0x3F800000, 0x437F0000, 0x45000000
ADD, SUB, MADD, MSUB, MUL = 0, 1, 2, 3, 4


class LModel(V.VModel):
    def start(self, e):
        super().start(e)
        self.iw = {}      # iteration -> index word loaded into vi7 in that iteration
        self.ll = {}      # (pc, it, lane) -> value of the last load at that pc in that iteration
        self.cc = {}      # (pc, lane) -> value of the loop-invariant constants
        self.vf16 = list(e["st"]["vf"][16 * 4:16 * 4 + 4]) if not isinstance(e["st"]["vf"][0], P.S) else [int(v) for v in e["st"]["vf"][64:68]]

    def ildw(self, pc, reg, v):
        if reg == 7:
            self.iw[self.it] = v

    def ld(self, pc, c, addr, v):
        if pc in P.CONST_PCS:
            self.cc[(pc, c)] = int(v)
        else:
            self.ll[(pc, self.it, c)] = int(v)
        return super().ld(pc, c, addr, v)


def clamp255(x):
    return maxmini(True, maxmini(False, x, F255), 0)


def vertex_outputs(m, it, base):
    """closed-form words stored for the vertex whose inputs were loaded in iteration `it-1` (first-iteration loads come from the prologue pcs)"""
    j = it - 1

    def get(pcs, c):
        for pc in pcs:
            if (pc, j, c) in m.ll:
                return m.ll[(pc, j, c)]
        return None

    cc = lambda pc, c: m.cc[(pc, c)]
    c1 = lambda c: cc(0x2450 if base == 0x2440 else 0x2680, c)
    c2 = lambda c: cc(0x2458 if base == 0x2440 else 0x2688, c)
    c5 = lambda c: cc(0x2470 if base == 0x2440 else 0x26A0, c)
    c14 = lambda c: cc(0x2478 if base == 0x2440 else 0x26A8, c)
    PP = [get((0x2520, 0x2448), c) for c in range(4)]
    A = [get((0x2540, 0x2480), c) for c in range(4)]
    S = [get((0x2550, 0x2498), c) for c in range(4)]
    C = [get((0x2560, 0x2468), c) for c in range(4)]
    if None in PP or None in A or None in C:
        return None
    W = fmac(MADD, c2(3), PP[3], fmac(MUL, c1(3), PP[3], 0))
    Q = divq(ONE, W)
    out = {}
    for c in range(3):
        out[("xyz", c)] = ftoi(fmac(MUL, fmac(MADD, c2(c), PP[3], fmac(MUL, c1(c), PP[c], 0)), Q, 0), 16)
        if S[c] is not None:
            out[("st", c)] = fmac(MUL, S[c], Q, 0)
    t = fmac(MADD, c5(3), Q, fmac(MUL, ONE, c5(2), 0))
    t = maxmini(False, maxmini(True, t, 0), F255)
    out[("w", 1)] = ftoi(fmac(ADD, t, fmac(MUL, ONE, F2048, 0), 0), 16)
    out[("w", 0)] = ftoi(fmac(ADD, t, fmac(SUB, ONE, ONE, 0), 0), 16)
    for c in range(4):
        col = fmac(MUL, C[c], m.vf16[c], 0)
        out[("rgba", c)] = ftoi(clamp255(fmac(MADD, A[c], col, fmac(MUL, c14(c), col, 0))), 1)
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    entry = int(args[0], 16) if args else 0x2440
    maxn = int(args[1]) if len(args) > 1 else 60
    code = None
    for tag, p in corpus.chunks("logs/vu1corpus.bin"):
        if tag == b"CODE" and struct.unpack_from("<Q", p)[0] == 5566:
            code = p[8:]
            break
    m = LModel(code, L.load_blocks())
    m.head = 0x24C8 if entry < 0x2600 else 0x26F0
    stat = collections.Counter()
    bad = collections.Counter()
    n = 0
    for rec in R.records("logs/vu1regions.bin"):
        e = rec["e"]
        if rec["region"] != 0 or e["pc"] != entry:
            continue
        P.wrap_entry(e)
        try:
            m.run(e, pc=entry, sig="%016x" % rec["ehash"], region=(0x100, 0x3400), rings=rec["rings"])
        except Exception:  # noqa: BLE001
            continue
        n += 1
        cache = {}
        for (pc, it, c, kind, v, addr) in m.stores:
            if kind != "f" or pc not in (0x2538, 0x2598, 0x25A0, 0x25B0):
                continue
            if it not in cache:
                cache[it] = vertex_outputs(m, it, entry)
            o = cache[it]
            if o is None:
                stat["noinput"] += 1
                continue
            if pc == 0x2538:
                key = [("st", c)]
            elif pc == 0x2598:
                key = [("rgba", c)]
            else:
                key = [("xyz", c)] if c < 3 else [("w", 0), ("w", 1)]
            if key[0] not in o:
                stat["nokey"] += 1
                continue
            hit = any(int(v) == o[k] for k in key)
            if pc == 0x25A0 and c == 3:
                var = [k[1] for k in key if int(v) == o[k]]
                for lag in (0, 1, 2):
                    iw = m.iw.get(it - lag)
                    if iw is not None and len(var) == 1:
                        stat[("w-rule lag%d bit15=%d variant" % (lag, (iw >> 15) & 1), var[0])] += 1
            stat[("ok" if hit else "BAD", pc, c)] += 1
            if not hit:
                bad[(pc, c)] += 1
        if n >= maxn:
            break
    print("records", n)
    for k, v in sorted(stat.items(), key=lambda kv: str(kv[0])):
        print(k, v)


if __name__ == "__main__":
    main()
