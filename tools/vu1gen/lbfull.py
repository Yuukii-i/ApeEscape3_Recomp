"""Level B step 5: full-routine closed form. From the state at 1FE0 entry (and VU memory) alone compute the whole exit state of the skinned-vertex routine
(prologue + loop + tail, N >= 4 vertices) and compare with the recorded exit and the exact model: memory, vi, vf1-12/27, ACC, Q, I, status, pc, cycle, MAC ring pushes.
Usage: python tools/vu1gen/lbfull.py [logs/vu1region.bin] [max_records]"""
import struct
import sys

sys.path.insert(0, "tools/vu1gen")
import corpus  # noqa: E402
import lbmodel as L  # noqa: E402
import lbtele as T  # noqa: E402

ONE, F255 = T.ONE, T.F255
u32, s16, clamp = T.u32, T.s16, T.clamp


def full(e):
    """-> dict(mem diff, vi, vf, acc, q, i, status, pc, cycle, mac pushes) or None when the kernel declines"""
    st = e["st"]
    mem = bytearray(e["mem"])
    vf = [list(st["vf"][4 * r:4 * r + 4]) for r in range(32)]
    vi = list(st["vi"])
    for rel, reg, mask, val in e["pend"]["vf"]:
        for c in range(4):
            if mask & (8 >> c):
                vf[reg][c] = val[c]
    for rel, reg, val in e["pend"]["vi"]:
        vi[reg] = val
    for rel, addr, words, mask in e["pend"]["store"]:
        for c in range(4):
            if mask & (8 >> c):
                struct.pack_into("<I", mem, addr + 4 * c, words[c])
    m0 = bytes(mem)
    N = (vi[5] & 0xFFFF) // 2
    if (vi[5] & 1) or N < 4:
        return None
    K = N - 3
    s = T.Stages(mem, vf, vi, 0)
    s.idxbase, s.s3base, s.s2base = vi[4], vi[3], vi[2] + vi[12]
    old = s.idx
    vi7 = vi[7]
    s.idx = lambda t: vi7 if t == 0 else old(t)
    V = [s.v(t) for t in range(N)]
    for t in range(N):
        if V[t].di:
            return None
    out = {}
    base = vi[6] & 0xFFFF
    nq = len(mem) // 16

    def put(qw, lane, val):
        qw &= nq - 1
        out.setdefault(qw, bytearray(mem[qw * 16:qw * 16 + 16]))
        struct.pack_into("<I", out[qw], lane * 4, val & 0xFFFFFFFF)

    put(base, 0, vf[27][0])
    put(base, 1, vf[27][1])
    put(base, 2, u32(mem, 1012, 2))
    put(base, 3, u32(mem, 1012, 3))
    for v in range(N):
        q0 = base + 1 + 4 * v
        put(q0, 3, L.ftoi(clamp(V[v].Wraw), 16))
        for c in range(3):
            put(q0 + 1, c, V[v].S2Q[c])
        for c in range(4):
            put(q0 + 2, c, L.ftoi(clamp(V[v].prod[c]), 1))
        for c in range(3):
            put(q0 + 3, c, L.ftoi(V[v].R7[c], 16))
        put(q0 + 3, 3, V[v].idx & 0xFFFF)
    put(1023, 2, u32(mem, 1023, 3) & 0xFFFF)
    put(1023, 3, base)
    # integer registers
    xvi = list(vi)
    xvi[1] = s16(u32(mem, vi[13] & 0xFFFF, 0))
    xvi[2] = s16(vi[2] + vi[12] + N)
    xvi[3] = s16(vi[3] + N)
    xvi[4] = s16(vi[4] + N)
    xvi[7] = V[N - 1].idx
    xvi[8] = s16(vi[6] + 2 * vi[5])
    xvi[9] = xvi[8]
    xvi[11] = s16(u32(mem, 1023, 3))
    xvi[12] = V[1].idx
    # vector registers
    x = [list(r) for r in vf]
    L_, L1, L2, L3 = V[N - 1], V[N - 2], V[N - 3], None
    x[1][:3] = L_.T5[:3]
    x[1][3] = s.vf1w
    x[2] = [L.ftoi(clamp(L1.prod[c]), 1) for c in range(4)]
    x[3][:3] = L_.S2[:3]
    x[3][3] = s.vf3[3]
    x[4][:3] = L_.S2Q
    x[4][3] = L_.prodop.res[3]
    x[5] = [L.ftoi(L1.R7[c], 16) for c in range(3)] + [L.ftoi(clamp(L1.Wraw), 16)]
    x[6] = [L.ftoi(L_.R7[c], 16) for c in range(3)] + [L.ftoi(clamp(L_.Wraw), 16)]
    x[7] = list(V[N - 3].R7) + [clamp(V[N - 3].Wraw)]
    x[8] = [clamp(L_.prod[c]) for c in range(4)]
    x[9] = [L.ftoi(clamp(L_.prod[c]), 1) for c in range(4)]
    x[10] = list(L_.S3)
    x[11] = list(L_.inner)
    x[12][:3] = L1.S2Q
    x[27][2] = u32(mem, 1012, 2)
    x[27][3] = u32(mem, 1012, 3)
    acc = [L_.BVop.res[0], L_.BVop.res[1], L_.BVop.res[2], s.accw.res[3]]
    # status: sticky OR over every stage op of every vertex, low 4 = last FMAC of the tail (R7 of the last vertex), bits 4-5 cleared by the last landing
    sticky = s.accw.sticky
    for v in V:
        for o in (v.mulaA, v.T5op, v.R7op, v.S2Qop, v.Wop, v.BVop, v.inop, v.prodop):
            sticky |= o.sticky
    en = st["status"]
    status = (en & 0xC00) | ((en & 0x3C0) | ((sticky & 0xF) << 6)) | V[N - 1].R7op.cur
    # MAC ring pushes: prologue inner(2) at 20D8, loop inner(k+2) per pass, tail R7(N-1)
    c0 = e["cycle"]
    pushes = [(c0 + 41, V[2].inop.mac)]  # pair 31 of the 45-cycle prologue issues at +41 (10 stall cycles)
    for k in range(1, K + 1):
        pushes.append((c0 + 45 + 15 * (k - 1) + 11, V[k + 2].inop.mac))
    pushes.append((c0 + 45 + 15 * K + 10, V[N - 1].R7op.mac))
    return dict(diff={qw: bytes(b) for qw, b in out.items()}, vi=xvi, vf=x, acc=acc, q=V[N - 1].Q, i=F255, status=status, pc=(vi[15] * 8) & 0x3FFF,
                cycle=c0 + 74 + 15 * K, pushes=pushes, N=N)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].isdigit() else "logs/vu1region.bin"
    maxn = int(sys.argv[-1]) if sys.argv[-1].isdigit() else 10 ** 9
    code = next(p[8:] for tag, p in corpus.chunks("logs/vu1corpus.bin") if tag == b"CODE" and struct.unpack_from("<Q", p)[0] == L.CODE_GEN)
    m = L.Model(code, L.load_blocks())
    n = bad = declined = 0
    why = {}
    shown = 0
    for e, x in L.records(path):
        if n >= maxn:
            break
        n += 1
        r = full(e)
        if r is None:
            declined += 1
            continue
        probs = []
        xs = x["st"]
        a = bytearray(e["mem"])
        for qw, b in r["diff"].items():
            a[qw * 16:qw * 16 + 16] = b
        b_ = bytearray(e["mem"])
        for qw, b in x["diff"].items():
            b_[qw * 16:qw * 16 + 16] = b
        if a != b_:
            probs.append("mem")
        if r["vi"][1:] != xs["vi"][1:]:
            probs.append("vi")
        for rg in list(range(1, 13)) + [27]:
            if r["vf"][rg] != list(xs["vf"][4 * rg:4 * rg + 4]) and not (rg == 12 and r["vf"][12][:3] == list(xs["vf"][48:51])):
                probs.append("vf%d" % rg)
        if r["acc"] != xs["acc"]:
            probs.append("acc")
        if r["q"] != xs["q"]:
            probs.append("q")
        if r["i"] != xs["i"]:
            probs.append("i")
        if r["status"] != xs["status"]:
            probs.append("status")
        if r["pc"] != x["pc"]:
            probs.append("pc")
        if r["cycle"] != x["cycle"]:
            probs.append("cycle")
        # status with an empty entry status against the exact model (sticky bits then depend on the data)
        e2 = dict(e)
        e2["st"] = dict(e["st"], status=0)
        r2 = full(e2)
        mr = m.run(dict(e2, mem=bytearray(e["mem"])))
        if r2["status"] != mr["status"]:
            probs.append("status0 %03X/%03X" % (r2["status"], mr["status"]))
        want = [(t, mac) for (t, pc, mac) in mr["maclog"] if pc in (0x20D8, 0x2150, 0x21C0)]
        if want != r["pushes"]:
            probs.append("ring")
        if probs:
            bad += 1
            for pr in probs:
                why[pr.split()[0]] = why.get(pr.split()[0], 0) + 1
            if shown < 5:
                shown += 1
                print("rec %d N=%d: %s" % (n, r["N"], "; ".join(probs)))
    print("records=%d bad=%d declined(N<4)=%d" % (n, bad, declined))
    for k, v in sorted(why.items(), key=lambda kv: -kv[1]):
        print("  %5d  %s" % (v, k))


if __name__ == "__main__":
    main()
