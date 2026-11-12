"""Handler family 0C80 / 0C88 / 0CB0 (the stream -> VU memory copy command): closed form checked against logs/vu1regions.bin.
0C80: ILW.z vi3, -1(vi13)      ; vi3 = destination (z of the previous quad)
0C88: loop { LQI vf1, (vi13++); vi3++; IBNE vi2, vi3 ; SQ vf1, -1(vi3) (delay slot) }   -> n = vi2 - vi3_0 quads copied, vf1 = last
0CB0: JR vi1 ; (delay) ILW.x vi1, 0(vi13)  -> next command address is loaded after the copy.
Usage: python tools/vu1gen/h_copy.py [logs/vu1regions.bin]"""
import collections
import struct
import sys

sys.path.insert(0, "tools/vu1gen")
import regions as R  # noqa: E402


def s16(x):
    x &= 0xFFFF
    return x - 0x10000 if x & 0x8000 else x


def u32(mem, qw, lane):
    return struct.unpack_from("<I", mem, (qw & (len(mem) // 16 - 1)) * 16 + lane * 4)[0]


def copy_handler(e):
    """closed form -> (mem diff, vi dict, vf1, pc, extra cycles breakdown) or None if it declines"""
    st = e["st"]
    mem = bytearray(e["mem"])
    vi = list(st["vi"])
    pc0 = e["pc"]
    vi2, vi13 = vi[2], vi[13]
    nq = len(mem) // 16
    out = {}
    if pc0 == 0x0CB0:
        n = 0
        vi3 = vi[3]
        vf1 = None
    else:
        vi3 = s16(u32(mem, (vi13 - 1) & 0xFFFF, 2)) if pc0 == 0x0C80 else vi[3]
        n = (vi2 - vi3) & 0xFFFF
        if n == 0 or n > 2048:
            return None
        vf1 = None
        for i in range(n):
            src = (vi13 + i) & 0xFFFF
            dst = (vi3 + i) & 0xFFFF
            q = bytes(mem[(src & (nq - 1)) * 16:(src & (nq - 1)) * 16 + 16])
            mem[(dst & (nq - 1)) * 16:(dst & (nq - 1)) * 16 + 16] = q
            vf1 = struct.unpack("<4I", q)
    xvi = list(vi)
    if n:
        xvi[3] = vi2
        xvi[13] = s16(vi13 + n)
    xvi[1] = s16(u32(mem, xvi[13] & 0xFFFF, 0))
    pc = (vi[15] * 8) & 0x3FFF  # JR vi15: 5 -> the dispatcher loop at 0028, 0 -> end of program
    return mem, xvi, vf1, pc, n


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "logs/vu1regions.bin"
    stats = collections.Counter()
    cyc_by = collections.defaultdict(set)
    bad = collections.Counter()
    shown = 0
    for rec in R.records(path):
        e, x = rec["e"], rec["x"]
        if rec["region"] != 0 or e["pc"] not in (0x0C80, 0x0C88, 0x0CB0):
            continue
        r = copy_handler(e)
        stats[e["pc"]] += 1
        if r is None:
            bad["declined"] += 1
            continue
        mem, xvi, vf1, pc, n = r
        b_ = bytearray(e["mem"])
        for qw, q in x["diff"].items():
            b_[qw * 16:qw * 16 + 16] = q
        xs = x["st"]
        probs = []
        if bytes(mem) != bytes(b_):
            probs.append("mem")
        if xvi[1:] != xs["vi"][1:]:
            probs.append("vi(" + ",".join(str(i) for i in range(1, 16) if xvi[i] != xs["vi"][i]) + ")")
        if vf1 is not None and list(vf1) != list(xs["vf"][4:8]):
            probs.append("vf1")
        if vf1 is None and list(xs["vf"][4:8]) != list(e["st"]["vf"][4:8]):
            probs.append("vf1-changed")
        if pc != x["pc"]:
            probs.append("pc")
        for k in range(32):
            if k != 1 and list(xs["vf"][4 * k:4 * k + 4]) != list(e["st"]["vf"][4 * k:4 * k + 4]):
                probs.append("vf%d" % k)
        if xs["status"] != e["st"]["status"] or xs["acc"] != e["st"]["acc"] or xs["q"] != e["st"]["q"]:
            probs.append("flags/acc/q")
        cyc = x["cycle"] - e["cycle"]
        cyc_by[(e["pc"], n)].add(cyc)
        if probs:
            bad[",".join(probs)] += 1
            if shown < 4:
                shown += 1
                print("entry %04X n=%d: %s" % (e["pc"], n, probs))
    print("records by entry:", {"%04X" % k: v for k, v in stats.items()})
    print("mismatches:", dict(bad) if bad else "none")
    # cycle model: cycles = base + 5n ?
    for pc in (0x0C80, 0x0C88, 0x0CB0):
        pts = sorted((n, sorted(v)) for (p, n), v in cyc_by.items() if p == pc)
        print("%04X cycles by n:" % pc, pts[:8], "..." if len(pts) > 8 else "")
        ok = all(len(v) == 1 for n, v in pts)
        if pts and ok:
            d = [(n, v[0]) for n, v in pts]
            diffs = {(d[i + 1][1] - d[i][1]) / (d[i + 1][0] - d[i][0]) for i in range(len(d) - 1)}
            print("   unique cycles per n: yes; slope(s) per iteration:", diffs)


if __name__ == "__main__":
    main()
