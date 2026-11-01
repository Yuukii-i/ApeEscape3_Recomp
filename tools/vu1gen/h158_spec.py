"""Matrix-transform loop 0158..0180 (entry 0158) from the ENTRY state only, checked against the region capture (logs/vu1regions.bin, region 0).
Loop (6 cycles per pass j = 1..n, n = vi6 - vi5):
  0158 MULAx  ACC = vf1*V.x                 | SQI vf31, (vi7++)
  0160 MADDAy ACC += vf2*V.y                | LQ.xy vf5, 0(vi1)
  0168 MADDAz ACC += vf3*V.z                | SQI vf6, (vi5++)
  0170 MADDw  vf6 = ACC + vf4*V.w           | LQI.zw vf5, (vi1++)
  0178 IBNE vi6, vi5, -5                    | 0180 nop (delay slot)   then 0188 JR vi15 | 0190 ILW.x vi1, 0(vi13)
V of pass 1 is the entry vf5; V of pass j >= 2 is the quad loaded by pass j-1, i.e. mem[vi1_0 + j - 2].
Usage: python tools/vu1gen/h158_spec.py [records-per-entry]"""
import collections
import struct
import sys

sys.path.insert(0, "tools/vu1gen")
import lbmodel as L  # noqa: E402
import regions as R  # noqa: E402

MUL, MADD = 4, 2


def s16(x):
    x &= 0xFFFF
    return x - 0x10000 if x & 0x8000 else x


def cur_bits(lanes):
    """status low nibble of one FMAC: OR of the lane flags over the written lanes (1 zero, 2 sign, 4 underflow, 8 overflow)"""
    c = 0
    for ex, zneg in lanes:
        c |= L.lane_flags(ex, zneg)
    return c


def spec(e):
    """-> dict(mem, vi, vf5, vf6, acc, status, pc, n, macs) from the entry state"""
    st = e["st"]
    mem = bytearray(e["mem"])
    nq = len(mem) // 16
    vi = list(st["vi"])
    vf = [list(st["vf"][4 * k:4 * k + 4]) for k in range(32)]

    def lq(qw):
        return list(struct.unpack_from("<4I", mem, (qw & (nq - 1)) * 16))

    def sq(qw, q):
        struct.pack_into("<4I", mem, (qw & (nq - 1)) * 16, *q)

    n = (vi[6] - vi[5]) & 0xFFFF
    if n == 0 or n > 600:
        return None
    r = [vf[1], vf[2], vf[3], vf[4]]
    v = list(vf[5])
    vf6 = list(vf[6])
    vf31 = list(vf[31])
    vi1, vi5, vi7 = vi[1], vi[5], vi[7]
    acc = list(st["acc"])
    status = st["status"]
    sticky = 0
    last_cur = 0
    macs = []
    for j in range(1, n + 1):
        # pair 0
        sq(vi7, vf31)
        vi7 = s16(vi7 + 1)
        ops = []
        for k, kind in enumerate((MUL, MADD, MADD, MADD)):
            newacc, lanes = [], []
            maclanes = []
            for c in range(4):
                a, b = r[k][c], v[k]
                res = L.fmac(kind, a, b, acc[c])
                ex, zneg, pex, psgn = L.fmac_ex(kind, a, b, acc[c])
                newacc.append(res)
                lanes.append((ex, zneg))
                maclanes.append(L.lane_flags(ex, zneg))
            extra = 0
            if kind in (MADD,):
                for c in range(4):
                    a, b = r[k][c], v[k]
                    _, _, pex, psgn = L.fmac_ex(kind, a, b, acc[c])
                    if pex < 0 or (pex == 0 and psgn):
                        extra |= 2
            cur = cur_bits(lanes)
            sticky |= (cur | extra) << 6
            last_cur = cur
            # MAC word (bit 4+3-c sign/zero per lane x=bit7.. per the C++ rev4 layout): sign lanes in bits 7..4 (x=7), zero lanes 3..0
            mac = 0
            for c in range(4):
                if maclanes[c] & 2:
                    mac |= 1 << (7 - c)
                if maclanes[c] & 1:
                    mac |= 1 << (3 - c)
            macs.append((j, k, mac))
            if k < 3:
                acc = newacc
            else:
                vf6_new = newacc
            if k == 1:
                pass
            # lower-unit slot of this pair
            if k == 1:
                q = lq(vi1)
                v_next = [q[0], q[1], v[2], v[3]]
            elif k == 2:
                sq(vi5, vf6)
                vi5 = s16(vi5 + 1)
            elif k == 3:
                q = lq(vi1)
                v_next[2], v_next[3] = q[2], q[3]
                vi1 = s16(vi1 + 1)
        vf6 = vf6_new
        v = v_next
    xvi = list(vi)
    xvi[5], xvi[7] = vi5, vi7
    xvi[1] = s16(struct.unpack_from("<I", mem, ((vi[13] & 0xFFFF) & (nq - 1)) * 16)[0])
    return dict(mem=mem, vi=xvi, vf5=v, vf6=vf6, acc=acc, n=n, macs=macs,
                status=(st["status"] & 0xFF0) | last_cur | sticky, pc=(vi[15] * 8) & 0x3FFF)


def main():
    want = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    bad = collections.Counter()
    cyc = collections.defaultdict(set)
    seen = 0
    sh = 0
    for rec in R.records("logs/vu1regions.bin"):
        e, x = rec["e"], rec["x"]
        if rec["region"] != 0 or e["pc"] != 0x0158:
            continue
        seen += 1
        s = spec(e)
        if s is None:
            bad["declined"] += 1
            continue
        b_ = bytearray(e["mem"])
        for qw, q in x["diff"].items():
            b_[qw * 16:qw * 16 + 16] = q
        xs = x["st"]
        probs = []
        if bytes(s["mem"]) != bytes(b_):
            probs.append("mem")
        if s["vi"][1:] != xs["vi"][1:]:
            probs.append("vi(" + ",".join(str(i) for i in range(1, 16) if s["vi"][i] != xs["vi"][i]) + ")")
        if list(xs["vf"][20:24]) != list(s["vf5"]):
            probs.append("vf5")
        if list(xs["vf"][24:28]) != list(s["vf6"]):
            probs.append("vf6")
        if list(xs["acc"]) != list(s["acc"]):
            probs.append("acc")
        if xs["status"] != s["status"]:
            probs.append("status")
        if x["pc"] != s["pc"]:
            probs.append("pc")
        for k in range(32):
            if k not in (1, 5, 6) and list(xs["vf"][4 * k:4 * k + 4]) != list(e["st"]["vf"][4 * k:4 * k + 4]):
                probs.append("vf%d" % k)
        cyc[s["n"]].add(x["cycle"] - e["cycle"])
        if probs:
            bad[",".join(probs)] += 1
            if sh < 3:
                sh += 1
                print("n=%d: %s status exp %03X got %03X" % (s["n"], probs, s["status"], xs["status"]))
        if seen >= want:
            break
    print("entry 0158 records %d, mismatching classes: %s" % (seen, dict(bad) or "none"))
    print("cycles by n:", {k: sorted(v) for k, v in sorted(cyc.items())})


if __name__ == "__main__":
    main()
