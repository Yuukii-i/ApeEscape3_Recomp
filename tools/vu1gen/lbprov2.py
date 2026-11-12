"""Level B step 2b: per-vertex output function of the skinned-vertex loop. Loads become role leaves (A = matrix quad at 636+idx, B = 716+idx, S3 = LQI via
vi3, S2 = LQI via vi2, C = vi0 constants) numbered per role in execution order, so a leaf's index is the vertex whose data it is. The FINAL memory image is
analysed: every written dword has an expression; they are grouped by (output quad offset from the buffer base, lane).
Usage: python tools/vu1gen/lbprov2.py [logs/vu1region.bin] [max_records] [--show]"""
import collections
import struct
import sys

sys.path.insert(0, "tools/vu1gen")
import corpus  # noqa: E402
import lbmodel as L  # noqa: E402
import lbprov as P  # noqa: E402


def role_of(code, pc):
    lo, _ = struct.unpack_from("<II", code, pc)
    op = (lo >> 25) & 0x7F
    fs = (lo >> 11) & 31
    if op == 0x00:
        imm = L.simm11(lo)
        if fs == 0:
            return "C"
        return "A" if imm == 636 else "B" if imm == 716 else "LQ%d" % imm
    if op == 0x40:
        return "S%d" % fs
    return "?%02X" % op


class RModel(P.PModel):
    def start(self, e):
        super().start(e)
        self.cnt = collections.Counter()
        self.last = {}

    def ld(self, pc, c, addr, v):
        s = self.shadow.get(addr)
        if s is not None:
            return s
        role = role_of(self.code, pc)
        if role == "C":
            return P.sv(v, P.mk(("C", pc, c)))
        inst = (self.it, self.cur_pc)  # one load instruction execution
        if self.last.get(role) != inst:
            self.cnt[role] += 1
            self.last[role] = inst
        return P.sv(v, P.mk(("R", role, c, self.cnt[role] - 1)))

    def stv(self, pc, addr, c, v, kind):
        if kind == "i":
            v = P.sv(int(v), P.mk(("IS", pc)))
        super().stv(pc, addr, c, v, kind)


def canon(n, ref, memo):
    k = (n, ref)
    r = memo.get(k)
    if r is not None:
        return r
    node = P.NODES[n]
    op, ch = node[0], node[1:]
    key = ("R", op[1], op[2], op[3] - ref) if op[0] == "R" else (op,) + tuple(canon(c, ref, memo) for c in ch)
    r = P.CANON.setdefault(key, len(P.CANON))
    memo[k] = r
    return r


def text(n, ref):
    node = P.NODES[n]
    op, ch = node[0], node[1:]
    if op[0] == "R":
        return "%s.%s[v%+d]" % (op[1], "xyzw"[op[2]], op[3] - ref)
    if op[0] == "C":
        return "C%04X.%s" % (op[1], "xyzw"[op[2]])
    if op[0] == "IS":
        return "ISW@%04X" % op[1]
    if op[0] == "K":
        return {0: "0", 1065353216: "1.0", 1132396544: "255.0"}.get(op[1], "K%08X" % op[1])
    if op[0] == "E":
        return "E.vf%d.%s" % (op[1], "xyzw"[op[2]])
    name = op[0] if len(op) == 1 else "%s%s" % (op[0], op[1])
    return "%s(%s)" % (name, ",".join(text(c, ref) for c in ch))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = args[0] if args else "logs/vu1region.bin"
    maxn = int(args[1]) if len(args) > 1 else 10 ** 9
    show = "--show" in sys.argv
    code = next(p[8:] for tag, p in corpus.chunks("logs/vu1corpus.bin") if tag == b"CODE" and struct.unpack_from("<Q", p)[0] == L.CODE_GEN)
    m = RModel(code, L.load_blocks())
    n = shown = 0
    groups = collections.defaultdict(collections.Counter)
    edge = collections.defaultdict(list)
    for e, x in L.records(path):
        if n >= maxn:
            break
        n += 1
        P.wrap_entry(e)
        m.run(e)
        trips = (x["cycle"] - e["cycle"] - 74) // 15
        if m.shadow:
            base = min(k >> 4 for k in m.shadow)
            memo = {}
            nv = (max(k >> 4 for k in m.shadow) - base) // 4 + 1
            for k, val in m.shadow.items():
                qw, lane = (k >> 4) - base, (k >> 2) & 3
                if qw == 0:
                    continue
                v, slot = (qw - 1) // 4, (qw - 1) % 4
                cid = canon(val.n, v, memo)
                groups[(slot, lane)][cid] += 1
                if v == 0 or v == nv - 1:
                    edge[(slot, lane)].append((cid, "first" if v == 0 else "last"))
        if show and trips >= 5 and shown < 1:
            shown += 1
            addrs = sorted(m.shadow)
            base = min(a >> 4 for a in addrs)
            print("record %d trips=%d base qw=%d" % (n, trips, base))
            for a in addrs:
                print("  qw+%-3d %s = %s" % ((a >> 4) - base, "xyzw"[(a >> 2) & 3], text(m.shadow[a].n, 0)[:240]))
    print("records", n)
    print("slot lane  distinct-functions  (counts)")
    for k in sorted(groups):
        print("  q%d   %s     %d   %s" % (k[0] + 1, "xyzw"[k[1]], len(groups[k]), dict(groups[k])))


if __name__ == "__main__":
    main()
