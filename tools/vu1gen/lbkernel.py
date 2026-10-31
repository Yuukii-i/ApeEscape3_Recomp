"""Level B step 3: closed-form kernel for the VU1 skinned-vertex loop region [1FE0,2200) (no instruction stepping), checked against logs/vu1region.bin.
Entry contract (from the provenance of lbprov2.py): N = vi5/2 vertices (>= 3); vertex v: idx_0 = vi7, idx_v = mem[vi4+v].x (low 16 bits);
A = mem[636+idx], B = mem[716+idx]; S3[v] = mem[vi3+v]; S2[v] = mem[vi2+vi12+v]; out base qw = vi6: header at +0, vertex v quads at +1+4v .. +4+4v.
Usage: python tools/vu1gen/lbkernel.py [logs/vu1region.bin] [max_records]"""
import struct
import sys

sys.path.insert(0, "tools/vu1gen")
import corpus  # noqa: E402
import lbmodel as L  # noqa: E402

ONE = 0x3F800000
F255 = 0x437F0000


def u32(mem, qw, lane):
    return struct.unpack_from("<I", mem, (qw & (len(mem) // 16 - 1)) * 16 + lane * 4)[0]  # VU memory addresses wrap (LQ masks with dataSize-1)


def kernel(e):
    """-> (memory diff {qw: 16 bytes}, info dict) or None if the kernel declines"""
    st = e["st"]
    mem = bytearray(e["mem"])
    n_qw = len(mem) // 16
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
    vi2, vi3, vi4, vi5, vi6, vi7, vi12 = vi[2], vi[3], vi[4], vi[5], vi[6], vi[7], vi[12]
    nv = (vi5 & 0xFFFF) // 2
    if (vi5 & 1) or nv < 3:
        return None
    vf3 = [u32(mem, 1002, c) for c in range(4)]
    vf4 = [u32(mem, 1003, c) for c in range(4)]
    vf2 = [u32(mem, 1014, c) for c in range(4)]
    vf1z, vf1w = u32(mem, 1016, 2), u32(mem, 1016, 3)
    vf16 = vf[16]
    out = {}

    def put(qw, lane, val):
        qw &= n_qw - 1
        out.setdefault(qw, bytearray(mem[qw * 16:qw * 16 + 16]))
        struct.pack_into("<I", out[qw], lane * 4, val & 0xFFFFFFFF)

    base = vi6 & 0xFFFF
    # header quad
    put(base, 0, vf[27][0])
    put(base, 1, vf[27][1])
    put(base, 2, u32(mem, 1012, 2))
    put(base, 3, u32(mem, 1012, 3))
    for v in range(nv):
        idx = vi7 if v == 0 else (u32(mem, (vi4 + v) & 0xFFFF, 0) & 0xFFFF)
        idx = ((idx + 0x8000) & 0xFFFF) - 0x8000  # ILW sign-extends the 16-bit lane
        A = [u32(mem, 636 + idx, c) for c in range(4)]
        B = [u32(mem, 716 + idx, c) for c in range(4)]
        S3 = [u32(mem, vi3 + v, c) for c in range(4)]
        S2 = [u32(mem, vi2 + vi12 + v, c) for c in range(4)]
        t5 = [L.fmac(2, vf4[c], A[3], L.fmac(4, vf3[c], A[c], 0)) for c in range(4)]  # vf5 = vf3*A + vf4*A.w
        q = L.divq(ONE, t5[3])
        q0 = base + 1 + 4 * v
        # q1.w
        acc_w = L.fmac(4, ONE, vf1z, 0)
        t = L.fmac(2, vf1w, q, acc_w)
        t = L.maxmini(True, t, 0)
        t = L.maxmini(False, t, F255)
        put(q0, 3, L.ftoi(t, 16))
        # q2.xyz
        for c in range(3):
            put(q0 + 1, c, L.fmac(4, S2[c], q, 0))
        # q3.xyzw
        for c in range(4):
            inner = L.fmac(2, vf2[c], vf16[c], L.fmac(4, B[c], vf16[c], 0))
            t = L.fmac(4, S3[c], inner, 0)
            t = L.maxmini(True, t, 0)
            t = L.maxmini(False, t, F255)
            put(q0 + 2, c, L.ftoi(t, 1))
        # q4.xyz (+ w = bone index)
        for c in range(3):
            put(q0 + 3, c, L.ftoi(L.fmac(4, t5[c], q, 0), 16))
        put(q0 + 3, 3, idx & 0xFFFF)
    # control quad 1023: z = old w (16 bit), w = out base
    put(1023, 2, u32(mem, 1023, 3) & 0xFFFF)
    put(1023, 3, base)
    diff = {qw: bytes(b) for qw, b in out.items() if bytes(b) != m0[qw * 16:qw * 16 + 16] or True}
    def s16(x):
        x &= 0xFFFF
        return x - 0x10000 if x & 0x8000 else x

    def idx_of(v):
        return vi7 if v == 0 else s16(u32(mem, (vi4 + v) & 0xFFFF, 0))

    xvi = list(vi)
    xvi[1] = s16(u32(mem, vi[13] & 0xFFFF, 0))        # ILW.x vi1, 0(vi13)
    xvi[2] = s16(vi2 + vi12 + nv)
    xvi[3] = s16(vi3 + nv)
    xvi[4] = s16(vi4 + nv)
    xvi[7] = idx_of(nv - 1)
    xvi[8] = s16(vi6 + 2 * vi5)
    xvi[9] = xvi[8]
    xvi[11] = s16(u32(mem, 1023, 3))                  # ILW.w vi11, 1023(vi0)
    xvi[12] = idx_of(1)
    return diff, dict(nv=nv, vi=xvi)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "logs/vu1region.bin"
    maxn = int(sys.argv[2]) if len(sys.argv) > 2 else 10 ** 9
    n = bad = declined = 0
    why = {}
    shown = 0
    for e, x in L.records(path):
        if n >= maxn:
            break
        n += 1
        r = kernel(e)
        if r is None:
            declined += 1
            continue
        diff, info = r
        # compare the effective memory result: apply both to the entry image
        a = bytearray(e["mem"])
        for qw, b in diff.items():
            a[qw * 16:qw * 16 + 16] = b
        b_ = bytearray(e["mem"])
        for qw, b in x["diff"].items():
            b_[qw * 16:qw * 16 + 16] = b
        vbad = [i for i in range(1, 16) if info["vi"][i] != x["st"]["vi"][i]]
        for i in vbad:
            why["vi%d" % i] = why.get("vi%d" % i, 0) + 1
        if vbad and shown < 3:
            shown += 1
            print("record %d vi mismatch %s" % (n, ", ".join("vi%d %d/%d" % (i, info["vi"][i], x["st"]["vi"][i]) for i in vbad)))
        if vbad:
            bad += 1
        if a != b_:
            bad += 1
            bq = sorted({i // 16 for i in range(len(a)) if a[i] != b_[i]})
            key = "qw%d" % ((bq[0] - (e["st"]["vi"][6] & 0xFFFF)) if bq[0] < 1000 else bq[0])
            why[key] = why.get(key, 0) + 1
            if shown < 3:
                shown += 1
                qw0 = bq[0]
                print("record %d nv=%d first bad qw=%d (out base %d) kernel=%s rec=%s" % (n, info["nv"], qw0, e["st"]["vi"][6], bytes(a[qw0 * 16:qw0 * 16 + 16]).hex(), bytes(b_[qw0 * 16:qw0 * 16 + 16]).hex()))
    print("records=%d bad=%d declined=%d" % (n, bad, declined))
    for k, v in sorted(why.items(), key=lambda kv: -kv[1])[:12]:
        print("  %5d  %s" % (v, k))


if __name__ == "__main__":
    main()
