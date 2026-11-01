"""Trace of the real-clipping path (2900..2F08) for one captured vertex-routine record: pcs visited in order with the integer registers, then the buffers 918..953
and the packet at 876.. at exit. Used to derive the Python functional spec of the clipper (tools/vu1gen/clipspec.py).
Usage: python tools/vu1gen/clip_trace.py [record-index-among-clipping-records]"""
import struct
import sys

sys.path.insert(0, "tools/vu1gen")
import corpus  # noqa: E402
import lbmodel as L  # noqa: E402
import regions as R  # noqa: E402
import vspec  # noqa: E402


class Tr(L.Model):
    def __init__(self, code, blk):
        super().__init__(code, blk)
        self.log = []

    def pair(self, pc, pidx, vf, acc, q, I, vi, fdiv, t, mem):
        self.log.append((pc, list(vi), t))


def load_code():
    for tag, p in corpus.chunks("logs/vu1corpus_v1.bin"):
        if tag == b"CODE" and struct.unpack_from("<Q", p)[0] == 5566:
            return p[8:]
    raise SystemExit("code image 5566 not found")


def clip_records(limit=100):
    out = []
    for rec in R.records("logs/vu1regions.bin"):
        if rec["region"] == 0 and rec["e"]["pc"] == 0x2440:
            sp = vspec.Spec(rec["e"])
            if sp.run() is None:
                out.append(rec)
                if len(out) >= limit:
                    break
    return out


def qw(mem, i):
    return struct.unpack_from("<4I", mem, (i & 1023) * 16)


def fl(w):
    return struct.unpack("<f", struct.pack("<I", w))[0]


def main():
    which = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    code = load_code()
    blk = L.load_blocks()
    recs = clip_records(which + 1)
    rec = recs[which]
    e, x = rec["e"], rec["x"]
    m = Tr(code, blk)
    r = m.run(e, pc=0x2440, sig="%016x" % rec["ehash"], region=(0x100, 0x3400), rings=rec["rings"])
    print("record %d: entry cycles %d -> exit cycles %d (%d)" % (which, e["cycle"], x["cycle"], x["cycle"] - e["cycle"]))
    prev = None
    seen2900 = False
    for pc, vi, t in m.log:
        if pc >= 0x2900 and not seen2900:
            seen2900 = True
            print("--- first pair at/after 2900: pc=%04X t=%s vi=%s" % (pc, t, vi))
        if pc >= 0x2900 or pc in (0x25B8,):
            tag = "" if prev is None or pc == prev + 8 else "  <-- jump from %04X" % prev
            print("%04X t=%s vi5..15=%s%s" % (pc, t, vi[5:16], tag))
        prev = pc
    mem = r["mem"]
    print("memory 876..:")
    for i in range(876, 900):
        print("  %4d %s" % (i, " ".join("%08X" % w for w in qw(mem, i))))
    print("memory 918..953:")
    for i in range(918, 954):
        print("  %4d %s" % (i, " ".join("%08X" % w for w in qw(mem, i))))


if __name__ == "__main__":
    main()
