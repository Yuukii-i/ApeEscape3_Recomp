import sys, collections
sys.path.insert(0, "tools/vu1gen")
import regions as R, vspec as V
xh = collections.Counter(); xp = collections.Counter(); xg = collections.Counter(); st = collections.Counter()
n = 0
for rec in R.records("logs/vu1regions.bin"):
    e, x = rec["e"], rec["x"]
    if rec["region"] != 0 or e["pc"] != 0x2440 or (x["pc"] != 0x28 and x["pc"] != 0): continue
    sp = V.Spec(e)
    if sp.run() is None: continue
    n += 1
    xh[hex(rec["xhash"])] += 1; xp[x["pc"]] += 1
    p = x["pend"]
    xg[(p["xg"], len(p["vf"]), len(p["vi"]), len(p["acc"]), len(p["flag"]), len(p["store"]), p["fdiv"][0])] += 1
    st[(hex(x["st"]["status"]), hex(e["st"]["status"]))] += 1
    if n >= 145: break
print("exit hashes", xh.most_common(5)); print("exit pcs", xp)
print("pend (xg,vf,vi,acc,flag,store,fdiv):", xg.most_common(5))
print("status exit/entry:", st.most_common(6))
