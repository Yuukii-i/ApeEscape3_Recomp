"""Keep only the block records of a variant-image dump whose whole span (n pairs + 1 margin) is identical (pair + usage record) to the main image.
Usage: python tools/vu1gen/filter_variant_dump.py <variant hash> <out.txt>   (reads logs/vublk2_u1_<variant>.txt and logs/vuusage_u1_<hash>.txt)"""
import re
import sys

MAIN = "86503d3905e35276"


def load(h):
    d = {}
    for ln in open("logs/vuusage_u1_%s.txt" % h):
        p = ln.split(None, 2)
        if len(p) == 3 and p[0] == "P":
            d[int(p[1], 16) >> 3] = p[2].strip()
    return d


v, out = sys.argv[1], sys.argv[2]
a, b = load(MAIN), load(v)
same = [i in a and b.get(i) == a[i] for i in range(2048)]
keep = drop = 0
w = open(out, "w")
cur = None
for ln in open("logs/vublk2_u1_%s.txt" % v, errors="replace"):
    m = re.match(r"B pc=(\w+) .* n=(\d+)", ln)
    if m:
        i, n = int(m.group(1), 16) >> 3, int(m.group(2))
        ok = all(i + k < 2048 and same[i + k] for k in range(n + 1))
        keep += ok
        drop += not ok
        cur = ok
    if cur:
        w.write(ln)
print("kept", keep, "dropped", drop)
