import sys, collections
sys.path.insert(0, "tools/vu1gen")
import vprov as V, lbprov as P, lbmodel as L, regions as R, struct, corpus
code = None
for tag, p in corpus.chunks("logs/vu1corpus.bin"):
    if tag == b"CODE" and struct.unpack_from("<Q", p)[0] == 5566:
        code = p[8:]; break
blk = L.load_blocks()
m = V.VModel(code, blk); m.head = 0x24C8
forms = collections.defaultdict(lambda: collections.defaultdict(int)); n = 0
for rec in R.records("logs/vu1regions.bin"):
    e = rec["e"]
    if rec["region"] != 0 or e["pc"] != 0x2440: continue
    # no clip subroutine on this record: trace never visits 28A0
    if 0x28A0 in rec["trace"] or len(rec["trace"]) >= 4096: continue
    P.wrap_entry(e)
    try:
        r = m.run(e, pc=0x2440, sig="%016x" % rec["ehash"], region=(0x100, 0x3400), rings=rec["rings"])
    except Exception: continue
    n += 1
    its = m.it
    memo = {}
    for rg in range(1, 32):
        for c in range(4):
            forms[(rg, c)][P.canon(P.nd(r["vf"][rg][c]), its, memo)] += 1
    for c in range(4):
        forms[("acc", c)][P.canon(P.nd(r["acc"][c]), its, memo)] += 1
    forms[("q", 0)][P.canon(P.nd(r["q"]), its, memo)] += 1
    if n >= 80: break
print("records", n)
for k, d in forms.items():
    print(k, len(d), sorted(d.values(), reverse=True)[:4])
