"""Clip machine, per-vertex routine 2440..2818: functional spec (layer A: control, integer state, memory output, decline condition) checked against the
region capture (entry 2440, exit at the dispatcher 0028). Floating point values come from the verified closed forms (vcheck1.py).
Usage: python tools/vu1gen/vspec.py [records]"""
import collections
import struct
import sys

sys.path.insert(0, "tools/vu1gen")
import lbmodel as L  # noqa: E402
import regions as R  # noqa: E402

fmac, maxmini, ftoi, divq = L.fmac, L.maxmini, L.ftoi, L.divq
ONE, F255, F2048 = 0x3F800000, 0x437F0000, 0x45000000
ADD, SUB, MADD, MSUB, MUL = 0, 1, 2, 3, 4
MASKS = (0xFDF7DF, 0xFEFBEF, 0xFF7DF7, 0xFFBEFB, 0xFFDF7D, 0xFFEFBE)


def s16(x):
    x &= 0xFFFF
    return x - 0x10000 if x & 0x8000 else x


def clip_bits(v):
    """CLIP.xyz vf, vf: six plane bits of the first three lanes against the |w| limit (same rule as the hot ops)"""
    w = v[3]
    limit = (w & 0x7FFFFFFF) if (w & 0x7F800000) else 0x007FFFFF
    fl = 0
    for k in range(3):
        for sg, mask in ((0, 0), (1, 0x80000000)):
            o = (v[k] ^ mask) & 0xFFFFFFFF
            o = o - (1 << 32) if o & 0x80000000 else o
            if o > limit:
                fl |= 1 << (2 * k + sg)
    return fl


class Spec:
    def __init__(self, e):
        st = e["st"]
        self.mem = bytearray(e["mem"])
        self.vi = list(st["vi"])
        self.vf = st["vf"]
        self.nq = len(self.mem) // 16

    def word(self, qw, lane):
        return struct.unpack_from("<I", self.mem, ((qw & (self.nq - 1)) * 16) + 4 * lane)[0]

    def quad(self, qw):
        return [self.word(qw, c) for c in range(4)]

    def put(self, qw, lane, v):
        struct.pack_into("<I", self.mem, ((qw & (self.nq - 1)) * 16) + 4 * lane, v & 0xFFFFFFFF)

    def run(self):
        vi = self.vi
        vf16 = self.vf[64:68]
        vi2, vi3, vi4, vi5, vi6, vi7, vi12, vi13 = vi[2], vi[3], vi[4], vi[5], vi[6], vi[7], vi[12], vi[13]
        N = vi5
        if N < 1 or N > 300:
            return None
        # ---- prologue
        c1 = [self.word(1002, c) for c in range(4)]
        c2 = [self.word(1003, c) for c in range(4)]
        c5 = [self.word(1016, c) for c in range(4)]
        c14 = [self.word(1014, c) for c in range(4)]
        q27 = [self.vf[4 * 27], self.vf[4 * 27 + 1], self.word(1012, 2), self.word(1012, 3)]
        vi11 = 0x7FFF
        vi2 = s16(vi2 + vi12)
        # vertex data are read in the exact order of the real code (the output stores can overwrite stream data that is read later)
        words, Ps, As, Ss, Cs, flags = [vi7], [], [], [], [], []
        pS, pC = vi2, vi3
        vi4_0 = vi4

        def outputs(j, adc):
            P, A, S, C = Ps[j], As[j], Ss[j], Cs[j]
            W = fmac(MADD, c2[3], P[3], fmac(MUL, c1[3], P[3], 0))
            Q = divq(ONE, W)
            xyz = [ftoi(fmac(MUL, fmac(MADD, c2[c], P[3], fmac(MUL, c1[c], P[c], 0)), Q, 0), 16) for c in range(3)]
            t = fmac(MADD, c5[3], Q, fmac(MUL, ONE, c5[2], 0))
            t = maxmini(False, maxmini(True, t, 0), F255)
            a = fmac(MUL, ONE, F2048, 0) if adc else fmac(SUB, ONE, ONE, 0)
            w = ftoi(fmac(ADD, t, a, 0), 16)
            st = [fmac(MUL, S[c], Q, 0) for c in range(3)]
            rgba = []
            for c in range(4):
                col = fmac(MUL, C[c], vf16[c], 0)
                u = fmac(MADD, A[c], col, fmac(MUL, c14[c], col, 0))
                rgba.append(ftoi(maxmini(True, maxmini(False, u, F255), 0), 1))
            return xyz + [w], st, rgba

        # prologue order: P0, header store, C0, A0, S0
        Ps.append(self.quad(636 + (words[0] & 0x7FFF)))
        for c in range(4):
            self.put(vi6, c, q27[c])
        vi6 = s16(vi6 + 1)
        Cs.append(self.quad(pC))
        pC = s16(pC + 1)
        As.append(self.quad(716 + (words[0] & 0x7FFF)))
        Ss.append(self.quad(pS))
        pS = s16(pS + 1)
        flags.append(clip_bits(Ps[0]))
        f = [1 if (flags[0] & 0x3F) else 0]
        # ---- loop
        vi8, vi9 = -2, -2
        vi1 = f[0]
        self.paths = []
        self.fl = f
        for it in range(1, N + 1):
            j = it - 1
            vi10 = vi1
            taken = "A" if words[j] < 0 else ("B" if vi8 <= 0 else "C")
            if taken == "C":
                cl = [flags[k] if k >= 0 else 0 for k in (j - 2, j - 1, j)]
                vis = (cl[0] << 12) | (cl[1] << 6) | cl[2]
                hit = None
                for m, mask in enumerate(MASKS):
                    if (vis | mask) == 0xFFFFFF:
                        hit = m
                        break
                if hit is None:
                    return None  # real clipping: not handled
                if hit == 5:
                    self.put(1022, 0, vi5)  # delay slot of the IBNE at 28F8 (ISW.x vi5, 1022) runs when the chain reaches its last test
            adc = 1 if taken in ("A", "C") else 0
            xyz, st, rgba = outputs(j, adc)
            # iteration body in program order: ILW word(it); LQ P(it); SQ ST; LQ A; LQI S; LQI C; SQ RGBA; SQ XYZ x2
            words.append(s16(self.word(vi4_0 + it, 0) & 0xFFFF))
            ix = words[it] & 0x7FFF
            Ps.append(self.quad(636 + ix))
            vi6 = s16(vi6 + 4)
            for c in range(3):
                self.put(vi6 - 3, c, st[c])
            As.append(self.quad(716 + ix))
            Ss.append(self.quad(pS))
            pS = s16(pS + 1)
            Cs.append(self.quad(pC))
            pC = s16(pC + 1)
            for c in range(4):
                self.put(vi6 - 2, c, rgba[c])
                self.put(vi6 - 4, c, xyz[c])
                self.put(vi6 - 1, c, xyz[c])
            flags.append(clip_bits(Ps[it]))
            f.append(1 if (flags[it] & 0x3F) else 0)
            vi1 = f[it]
            vi8 = s16(vi9 + vi10 + vi1)
            vi9 = vi10
            vi5 = s16(vi5 - 1)
            vi4 = s16(vi4 + 1)
            vi12 = words[it] & 0x7FFF
            vi7 = words[it]
            self.paths.append(taken if taken != 'C' else 'C%d' % hit)
        # ---- epilogue
        vi6_ep = self.word(1023, 3) & 0xFFFF
        vi7_ep = self.word(1023, 2) & 0xFFFF
        self.put(1023, 2, vi6_ep)
        self.put(1023, 3, vi7_ep)
        out = list(vi)
        out[2], out[3], out[4], out[5] = pS, pC, vi4, vi5
        out[6], out[7] = s16(vi6_ep), s16(vi7_ep)
        out[8], out[9], out[10], out[11] = vi8, vi9, vi10, vi11
        out[1] = s16(self.word(vi13, 0))
        out[12] = None  # XTOP (caller-supplied TOP)
        out[13] = vi13
        self.out_vi = out
        return True


def main():
    maxn = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    n = ok = declined = 0
    bad = collections.Counter()
    shown = 0
    for rec in R.records("logs/vu1regions.bin"):
        e, x = rec["e"], rec["x"]
        if rec["region"] != 0 or e["pc"] != 0x2440 or x["pc"] != 0x28 and x["pc"] != 0:
            continue
        n += 1
        sp = Spec(e)
        r = sp.run()
        if r is None:
            declined += 1
            continue
        probs = []
        diff = {}
        for qd in range(sp.nq):
            if sp.mem[qd * 16:qd * 16 + 16] != e["mem"][qd * 16:qd * 16 + 16]:
                diff[qd] = bytes(sp.mem[qd * 16:qd * 16 + 16])
        if diff != x["diff"]:
            probs.append("mem(spec %d qw, rec %d qw, differing %s)" % (len(diff), len(x["diff"]), sorted((set(diff) ^ set(x["diff"])) | {k for k in diff if k in x["diff"] and diff[k] != x["diff"][k]})[:4]))
        xv = x["st"]["vi"]
        for i in range(1, 16):
            if sp.out_vi[i] is not None and sp.out_vi[i] != xv[i]:
                probs.append("vi%d %d/%d" % (i, sp.out_vi[i], xv[i]))
        if probs:
            for p_ in probs:
                bad[p_.split()[0].split("(")[0]] += 1
            if shown < 4:
                shown += 1
                print("rec", n, "N", e["st"]["vi"][5], "paths", ",".join(sp.paths), probs[:5])
        else:
            ok += 1
        if n >= maxn:
            break
    print("records", n, "exact(mem+vi)", ok, "declined", declined, "bad", dict(bad))


if __name__ == "__main__":
    main()
