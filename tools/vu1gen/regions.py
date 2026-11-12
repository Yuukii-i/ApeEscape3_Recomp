"""Reader and summary for logs/vu1regions.bin (PROBE-REGION with PS2X_VU1_REGIONS). Record 'RGM ': u32 region, u64 entry block hash, ENTRY, EXIT, u64 exit block hash
(ENTRY/EXIT as in lbmodel.records). Usage: python tools/vu1gen/regions.py [file] [--detail <region index>]"""
import collections
import statistics
import struct
import sys

sys.path.insert(0, "tools/vu1gen")
import corpus  # noqa: E402
import lbmodel as L  # noqa: E402

RANGES = "1E00:1FE0,2440:2840,2840:2980,2D00:2F40,0050:0300,0000:0050,0AC0:0D00,29C0:2D00,1600:1740,1C00:1D00".split(",")


def records(path):
    for tag, p in corpus.chunks(path):
        if tag != b"RGM ":
            continue
        r = L.Rd(p)
        rec = dict(region=r.u("I"), ehash=r.u("Q"))
        e = dict(pc=r.u("I"), cycle=r.u("Q"))
        e["st"] = L.st_decode(r.raw(L.ST_SIZE))
        dsz = r.u("I")
        e["mem"] = bytearray(r.raw(dsz))
        e["pend"] = L.read_pending(r)
        x = dict(pc=r.u("I"), cycle=r.u("Q"))
        x["st"] = L.st_decode(r.raw(L.ST_SIZE))
        x["diff"] = {}
        for _ in range(r.u("I")):
            q = r.u("I")
            x["diff"][q] = bytes(r.raw(16))
        x["pend"] = L.read_pending(r)
        rec["xhash"] = r.u("Q")
        rec["trace"] = []
        if r.o < len(p):  # newer probe: dispatch pcs visited inside the run
            nt = r.u("I")
            rec["trace"] = list(struct.unpack_from("<%dH" % nt, p, r.o))
            r.o += 2 * nt
        rec["rings"] = None
        if r.o < len(p):  # probe v3: flag rings (oldest first) and the working clip at entry
            assert r.u("I") == 0x33565247, "bad v3 marker"
            rings = []
            for _ in range(2):
                cnt, base = r.u("I"), r.u("I")
                rings.append(dict(base=base, ent=[(r.u("Q"), r.u("I")) for _ in range(cnt)]))
            rec["rings"] = dict(clip=rings[0], mac=rings[1], wclip=r.u("I"))
        assert r.o == len(p), "record parse mismatch"
        rec["e"], rec["x"] = e, x
        yield rec


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = args[0] if args else "logs/vu1regions.bin"
    by = collections.defaultdict(list)
    for rec in records(path):
        by[rec["region"]].append(rec)
    print("regions with records:", len(by), " total records:", sum(len(v) for v in by.values()))
    print("reg range      recs  entry pcs (top)                       exit pcs (top)                   cycles min/mean/max   ehash xhash  qw-diff mean  xg@entry xg@exit")
    for i in sorted(by):
        rs = by[i]
        ep = collections.Counter("%04X" % r["e"]["pc"] for r in rs)
        xp = collections.Counter("%04X" % r["x"]["pc"] for r in rs)
        cy = [r["x"]["cycle"] - r["e"]["cycle"] for r in rs]
        eh = len({r["ehash"] for r in rs})
        xh = len({r["xhash"] for r in rs})
        dq = statistics.mean(len(r["x"]["diff"]) for r in rs)
        xge = sum(r["e"]["pend"]["xg"] for r in rs)
        xgx = sum(r["x"]["pend"]["xg"] for r in rs)
        print("%2d  %-9s %5d  %-36s  %-30s  %d/%.0f/%d  %5d %5d  %8.1f  %5d %5d" % (
            i, RANGES[i] if i < len(RANGES) else "?", len(rs), ",".join("%s:%d" % kv for kv in ep.most_common(4)), ",".join("%s:%d" % kv for kv in xp.most_common(3)),
            min(cy), statistics.mean(cy), max(cy), eh, xh, dq, xge, xgx))
    if "--detail" in sys.argv:
        i = int(sys.argv[sys.argv.index("--detail") + 1])
        rs = by[i]
        print("detail region", i, "entry pcs:", collections.Counter("%04X" % r["e"]["pc"] for r in rs).most_common(12))
        print("exit pcs:", collections.Counter("%04X" % r["x"]["pc"] for r in rs).most_common(12))
        print("cycle histogram:", sorted(collections.Counter(r["x"]["cycle"] - r["e"]["cycle"] for r in rs).items())[:30])


if __name__ == "__main__":
    main()
