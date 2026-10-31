"""Level B step 2: provenance of the skinned-vertex loop. Every vf/ACC/Q value carries an expression node (hash-consed); loads are leaves tagged
(pc, lane, loop iteration). For each float store the tree is canonicalised relative to the iteration that executed the store, so equal ids across
iterations / records mean the same function of (relatively-numbered) inputs.
Usage: python tools/vu1gen/lbprov.py [logs/vu1region.bin] [max_records] [--dump]"""
import collections
import struct
import sys

sys.path.insert(0, "tools/vu1gen")
import corpus  # noqa: E402
import lbmodel as L  # noqa: E402

NODES = []
INTERN = {}


def mk(op, *ch):
    k = (op,) + ch
    i = INTERN.get(k)
    if i is None:
        i = len(NODES)
        NODES.append(k)
        INTERN[k] = i
    return i


class S(int):
    n = None


def sv(v, n):
    s = S(v)
    s.n = n
    return s


def nd(x):
    return x.n if isinstance(x, S) else mk(("K", int(x)))


_o = dict(fmac=L.fmac, maxmini=L.maxmini, ftoi=L.ftoi, divq=L.divq)


def fmac(kind, a, b, ac):
    r = _o["fmac"](kind, int(a), int(b), int(ac))
    return sv(r, mk(("fmac", kind), nd(a), nd(b), nd(ac) if kind in (2, 3) else mk(("K", 0))))


def maxmini(is_max, a, b):
    return sv(_o["maxmini"](is_max, int(a), int(b)), mk(("max" if is_max else "min",), nd(a), nd(b)))


def ftoi(a, scale):
    return sv(_o["ftoi"](int(a), scale), mk(("ftoi", scale), nd(a)))


def divq(num, den):
    return sv(_o["divq"](int(num), int(den)), mk(("div",), nd(num), nd(den)))


L.fmac, L.maxmini, L.ftoi, L.divq = fmac, maxmini, ftoi, divq


CONST_PCS = {0x1FE8, 0x1FF0, 0x2000, 0x2008, 0x2178}


class PModel(L.Model):
    def start(self, e):
        self.it = 0
        self.cur_pc = 0
        self.shadow = {}
        self.stores = []

    def ld(self, pc, c, addr, v):
        s = self.shadow.get(addr)
        if s is not None:
            return s
        if pc in CONST_PCS:  # vi0-based loads of loop-invariant constants (vf3 vf4 vf2 vf1.zw vf27.zw): not iteration-relative
            return sv(v, mk(("C", pc, c)))
        return sv(v, mk(("L", pc, c, self.it)))

    def stv(self, pc, addr, c, v, kind):
        if isinstance(v, S):
            self.shadow[addr + 4 * c] = v
        self.stores.append((pc, self.it, c, kind, v, addr))


CANON = {}


def canon(n, ref, memo):
    k = (n, ref)
    r = memo.get(k)
    if r is not None:
        return r
    node = NODES[n]
    op, ch = node[0], node[1:]
    if op[0] == "L":
        key = ("L", op[1], op[2], op[3] - ref)
    else:
        key = (op,) + tuple(canon(c, ref, memo) for c in ch)
    r = CANON.setdefault(key, len(CANON))
    memo[k] = r
    return r


def wrap_entry(e):
    st = e["st"]
    st["vf"] = [sv(v, mk(("E", i >> 2, i & 3))) for i, v in enumerate(st["vf"])]
    st["acc"] = [sv(v, mk(("EACC", i))) for i, v in enumerate(st["acc"])]
    st["q"] = sv(st["q"], mk(("EQ",)))
    st["i"] = sv(st["i"], mk(("EI",)))


def dump(n, ref):
    seen = []
    stack = [n]
    got = set()
    while stack:
        x = stack.pop()
        if x in got:
            continue
        got.add(x)
        seen.append(x)
        stack.extend(NODES[x][1:])
    for x in sorted(got):
        op, ch = NODES[x][0], NODES[x][1:]
        if op[0] == "L":
            print("  n%-5d L pc=%04X lane=%d iter%+d" % (x, op[1], op[2], op[3] - ref))
        elif op[0] == "C":
            print("  n%-5d C pc=%04X lane=%d" % (x, op[1], op[2]))
        else:
            print("  n%-5d %s %s" % (x, op, " ".join("n%d" % c for c in ch)))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = args[0] if args else "logs/vu1region.bin"
    maxn = int(args[1]) if len(args) > 1 else 10 ** 9
    do_dump = "--dump" in sys.argv
    code = None
    for tag, p in corpus.chunks("logs/vu1corpus.bin"):
        if tag == b"CODE" and struct.unpack_from("<Q", p)[0] == L.CODE_GEN:
            code = p[8:]
            break
    m = PModel(code, L.load_blocks())
    # (pc, lane) -> class -> set of canon ids ; class: first (it<=2), mid (3<=it<=N-1), last (it==N)
    ids = collections.defaultdict(lambda: collections.defaultdict(set))
    n = 0
    dumped = False
    for e, x in L.records(path):
        if n >= maxn:
            break
        trips = (x["cycle"] - e["cycle"] - 74) // 15
        wrap_entry(e)
        r = m.run(e)
        n += 1
        memo = {}
        for (pc, it, c, kind, v, addr) in m.stores:
            if kind != "f":
                continue
            cid = canon(nd(v), it, memo)
            cls = "pro" if it == 0 else "first" if it <= 2 else "last" if it == trips else "mid"
            ids[(pc, c)][cls].add(cid)
            if do_dump and not dumped and trips >= 6 and cls == "mid" and pc == 0x2110:
                print("store pc=%04X lane=%d iter=%d trips=%d" % (pc, c, it, trips))
                dump(nd(v), it)
                dumped = True
    print("records", n, "canonical expressions", len(CANON))
    print("pc    lane  pro first  mid last   (distinct canonical functions per class)")
    for (pc, c) in sorted(ids):
        d = ids[(pc, c)]
        print("%04X  %d     %3d %5d %4d %4d" % (pc, c, len(d["pro"]), len(d["first"]), len(d["mid"]), len(d["last"])))


if __name__ == "__main__":
    main()
