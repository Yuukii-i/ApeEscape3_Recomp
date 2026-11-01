"""Level B (clip machine): expression provenance of the per-vertex routine (2440-25B0, copy at 2670-27D8). Reuses the lbprov machinery: every vf / ACC / Q
value carries a hash-consed expression node, loads are leaves tagged (pc, lane, loop iteration), constant loads are loop-invariant leaves.
For each float store the tree is printed relative to the iteration that executed it, i.e. the closed form of what one vertex writes.
Usage: python tools/vu1gen/vprov.py [entry pc hex, default 2440] [max records] [--dump pc lane]"""
import collections
import struct
import sys

sys.path.insert(0, "tools/vu1gen")
import corpus  # noqa: E402
import lbmodel as L  # noqa: E402
import lbprov as P  # noqa: E402
import regions as R  # noqa: E402

LOOP_HEAD = {0x2440: 0x24C8, 0x24F8: 0x24C8, 0x24C8: 0x24C8, 0x2670: 0x2740 - 0x28 + 0x28, 0x26F0: 0x26F0}
P.CONST_PCS = {0x2440, 0x2450, 0x2458, 0x2470, 0x2478, 0x2670, 0x2680, 0x2688, 0x26A0, 0x26A8}


class VModel(P.PModel):
    head = 0x24C8

    def pair(self, pc, pidx, vf, acc, q, I, vi, fdiv, t, mem):
        if pc == self.head:
            self.it += 1


def run_records(entry, maxn, head):
    code = None
    for tag, p in corpus.chunks("logs/vu1corpus.bin"):
        if tag == b"CODE" and struct.unpack_from("<Q", p)[0] == 5566:
            code = p[8:]
            break
    m = VModel(code, L.load_blocks())
    m.head = head
    n = 0
    for rec in R.records("logs/vu1regions.bin"):
        if rec["region"] != 0 or rec["e"]["pc"] != entry:
            continue
        e = rec["e"]
        P.wrap_entry(e)
        try:
            r = m.run(e, pc=entry, sig="%016x" % rec["ehash"], region=(0x100, 0x3400), rings=rec["rings"])
        except Exception:  # noqa: BLE001
            continue
        n += 1
        yield rec, m
        if n >= maxn:
            break


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    entry = int(args[0], 16) if args else 0x2440
    maxn = int(args[1]) if len(args) > 1 else 40
    head = 0x24C8 if entry < 0x2600 else 0x26F0 - 0x28 + 0x28
    ids = collections.defaultdict(lambda: collections.defaultdict(set))
    dumped = set()
    want = None
    if "--dump" in sys.argv:
        i = sys.argv.index("--dump")
        want = (int(sys.argv[i + 1], 16), int(sys.argv[i + 2]))
    recs = 0
    for rec, m in run_records(entry, maxn, head):
        recs += 1
        memo = {}
        its = max((s[1] for s in m.stores), default=0)
        for (pc, it, c, kind, v, addr) in m.stores:
            if kind != "f":
                continue
            cid = P.canon(P.nd(v), it, memo)
            cls = "first" if it <= 2 else "mid"
            ids[(pc, c)][cls].add(cid)
            if want == (pc, c) and cls == "mid" and (want, cid) not in dumped and it >= 4:
                dumped.add((want, cid))
                print("store pc=%04X lane=%d iter=%d canon=%d" % (pc, c, it, cid))
                P.dump(P.nd(v), it)
    print("records", recs, "canonical expressions", len(P.CANON))
    print("pc    lane  first mid   (distinct canonical functions per class)")
    for (pc, c) in sorted(ids):
        d = ids[(pc, c)]
        print("%04X  %d     %3d %4d" % (pc, c, len(d["first"]), len(d["mid"])))


if __name__ == "__main__":
    main()
