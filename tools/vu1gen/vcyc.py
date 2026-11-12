import sys, collections
sys.path.insert(0, "tools/vu1gen")
import regions as R, vspec as V
import numpy as np
rows = []; ys = []; hs = []
KEYS = ["A", "B", "C0", "C1", "C2", "C3", "C4", "C5"]
for rec in R.records("logs/vu1regions.bin"):
    e, x = rec["e"], rec["x"]
    if rec["region"] != 0 or e["pc"] != 0x2440 or (x["pc"] != 0x28 and x["pc"] != 0): continue
    sp = V.Spec(e)
    if sp.run() is None: continue
    cnt = collections.Counter(sp.paths)
    rows.append([1] + [cnt[k] for k in KEYS]); ys.append(x["cycle"] - e["cycle"]); hs.append(rec["ehash"])
    if len(rows) >= 300: break
A = np.array(rows, float); y = np.array(ys, float)
sol, res, rk, sv = np.linalg.lstsq(A, y, rcond=None)
print("records", len(rows), "rank", rk, "of", A.shape[1])
print("fit:", dict(zip(["base"] + KEYS, [round(v, 3) for v in sol])))
err = A @ sol - y
print("max |err|", abs(err).max(), " exact count", int((abs(err) < 0.5).sum()))
bad = [(i, int(ys[i]), round(float(A[i] @ sol), 1), dict(zip(["base"] + KEYS, rows[i])), hex(hs[i])) for i in range(len(rows)) if abs(err[i]) >= 0.5][:6]
for b in bad: print(b)
print("distinct entry hashes:", collections.Counter(hex(h) for h in hs).most_common(6))
