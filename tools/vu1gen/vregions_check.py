"""Per-entry exactness of the Python model against the region capture (logs/vu1regions.bin). Usage: python tools/vu1gen/vregions_check.py [records per entry pc, default 15]
Prints entries with exceptions / mismatches and a TOTAL line. Reading the 718 MB capture takes a few minutes."""
import sys, collections, struct
sys.path.insert(0, "tools/vu1gen")
import regions as R, lbmodel as L, corpus
blk = L.load_blocks()
code = None
for tag, p in corpus.chunks("logs/vu1corpus.bin"):
    if tag == b"CODE" and struct.unpack_from("<Q", p)[0] == 5566:
        code = p[8:]; break
per = collections.defaultdict(lambda: [0, 0, 0, collections.Counter(), collections.Counter()])  # n, exact, exc, excwhy, badkinds
lim = int(sys.argv[1]) if len(sys.argv) > 1 else 15
for rec in R.records("logs/vu1regions.bin"):
    if rec["region"] != 0: continue
    e, x = rec["e"], rec["x"]; pc = e["pc"]
    d = per[pc]
    if d[0] >= lim: continue
    d[0] += 1
    m = L.Model(code, blk)
    try:
        r = m.run(e, pc=pc, sig="%016x" % rec["ehash"], region=(0x100, 0x3400), rings=rec["rings"])
    except Exception as ex:
        d[2] += 1; d[3][str(ex)[:55]] += 1; continue
    xs = x["st"]; probs = []
    diff = {}
    for qd in range(len(e["mem"]) // 16):
        if r["mem"][qd*16:qd*16+16] != e["mem"][qd*16:qd*16+16]: diff[qd] = bytes(r["mem"][qd*16:qd*16+16])
    if diff != x["diff"]: probs.append("mem")
    for rg in range(1, 32):
        if r["vf"][rg] != list(xs["vf"][4*rg:4*rg+4]): probs.append("vf")
    for i in range(1, 16):
        if r["vi"][i] != xs["vi"][i]: probs.append("vi%d" % i)
    if r["acc"] != xs["acc"]: probs.append("acc")
    if r["q"] != xs["q"]: probs.append("q")
    if r["status"] != xs["status"]: probs.append("status")
    if r["pc"] != x["pc"]: probs.append("pc")
    if r["cycle"] != x["cycle"]: probs.append("cycle")
    if probs:
        for p_ in set(probs): d[4][p_] += 1
    else: d[1] += 1
tot = [0, 0, 0]
why = collections.Counter(); bk = collections.Counter()
for pc, d in sorted(per.items()):
    tot[0] += d[0]; tot[1] += d[1]; tot[2] += d[2]; why.update(d[3]); bk.update(d[4])
    if d[0] - d[1] - d[2] > 0 or d[2] > 0:
        print("%04X n=%d exact=%d exc=%d bad=%d %s %s" % (pc, d[0], d[1], d[2], d[0]-d[1]-d[2], dict(d[4]), dict(d[3])))
print("TOTAL records", tot[0], "exact", tot[1], "exceptions", tot[2], "mismatched", tot[0]-tot[1]-tot[2])
print(why.most_common(8)); print(bk.most_common(8))
