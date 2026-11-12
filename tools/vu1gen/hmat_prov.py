"""Expression provenance and closed-form derivation for handler entries:
  00A8 / 0158 (matrix setup)
  15E0 / 16C0 / 1708 (lerp)

Analyzes store expressions, exit registers, and cycle models across records.
Usage: python tools/vu1gen/hmat_prov.py [max_records_per_entry=60]
"""
import collections
import struct
import sys

sys.path.insert(0, "tools/vu1gen")
import corpus  # noqa: E402
import lbmodel as L  # noqa: E402
import lbprov as P  # noqa: E402
import regions as R  # noqa: E402

ENTRIES = (0x00A8, 0x0158, 0x15E0, 0x16C0, 0x1708)
LOOP_HEADS = {
    0x00A8: 0x0158,
    0x0158: 0x0158,
    0x15E0: 0x16C0,
    0x16C0: 0x16C0,
    0x1708: None,
}

P.CONST_PCS = {
    # 00A8 matrix setup constants
    0x00A8, 0x00B0, 0x00B8, 0x00C0, 0x00C8, 0x00D0, 0x00E8, 0x0100,
    # 15E0 lerp constants
    0x15E8, 0x15F8, 0x1600,
}


class HModel(P.PModel):
    head = None

    def pair(self, pc, pidx, vf, acc, q, I, vi, fdiv, t, mem):
        if self.head is not None and pc == self.head:
            self.it += 1


def fmt_expr(node_idx, depth=0):
    """Format expression node tree into readable algebraic string."""
    if depth > 10:
        return "..."
    node = P.NODES[node_idx]
    op = node[0]
    ch = node[1:]
    if op[0] == "C":
        return f"C_{op[1]:04X}.{'xyzw'[op[2]]}"
    if op[0] == "L":
        return f"L_{op[1]:04X}[it{op[3]:+d}].{'xyzw'[op[2]]}"
    if op[0] == "E":
        return f"E_vf{op[1]}.{'xyzw'[op[2]]}"
    if op[0] == "EACC":
        return f"E_acc.{'xyzw'[op[1]]}"
    if op[0] == "EQ":
        return "E_q"
    if op[0] == "EI":
        return "E_i"
    if op[0] == "K":
        val = op[1]
        fval = struct.unpack("<f", struct.pack("<I", val & 0xFFFFFFFF))[0]
        if fval == 0.0:
            return "0.0"
        if fval == 1.0:
            return "1.0"
        if fval == 0.5:
            return "0.5"
        return f"{fval:.4g}"
    if op[0] == "fmac":
        kind = op[1]
        a = fmt_expr(ch[0], depth + 1)
        b = fmt_expr(ch[1], depth + 1)
        if kind == 4:  # MUL
            return f"({a} * {b})"
        if kind == 0:  # ADD
            return f"({a} + {b})"
        if kind == 1:  # SUB
            return f"({a} - {b})"
        c = fmt_expr(ch[2], depth + 1)
        if kind == 2:  # MADD
            return f"({c} + {a} * {b})"
        if kind == 3:  # MSUB
            return f"({c} - {a} * {b})"
    if op[0] in ("max", "min"):
        a = fmt_expr(ch[0], depth + 1)
        b = fmt_expr(ch[1], depth + 1)
        return f"{op[0]}({a}, {b})"
    return f"{op}({', '.join(fmt_expr(c, depth + 1) for c in ch)})"


def main():
    maxn = int(sys.argv[1]) if len(sys.argv) > 1 else 60

    code = None
    for tag, p in corpus.chunks("logs/vu1corpus.bin"):
        if tag == b"CODE" and struct.unpack_from("<Q", p)[0] == 5566:
            code = p[8:]
            break

    blk = L.load_blocks()

    recs_by_entry = collections.Counter()
    models = {epc: HModel(code, blk) for epc in ENTRIES}
    for epc, m in models.items():
        m.head = LOOP_HEADS[epc]

    store_canon = collections.defaultdict(lambda: collections.defaultdict(set))
    store_exprs = {}
    store_counts = collections.defaultdict(lambda: collections.defaultdict(int))

    exit_canon = collections.defaultdict(lambda: collections.defaultdict(set))
    exit_counts = collections.defaultdict(lambda: collections.defaultdict(int))

    cycles_data = collections.defaultdict(list)

    print(f"Streaming records for entries {tuple(f'{p:04X}' for p in ENTRIES)}, max {maxn} per entry...")

    for rec in R.records("logs/vu1regions.bin"):
        if rec["region"] != 0:
            continue
        epc = rec["e"]["pc"]
        if epc not in models:
            continue
        if recs_by_entry[epc] >= maxn:
            if all(recs_by_entry[p] >= maxn for p in ENTRIES):
                break
            continue

        e = rec["e"]
        P.wrap_entry(e)
        m = models[epc]

        try:
            reg_bound = 0x0050 if epc < 0x0100 else 0x0100
            r = m.run(e, pc=epc, sig="%016x" % rec["ehash"], region=(reg_bound, 0x3400), rings=rec["rings"])
        except Exception as ex:
            print(f"Exception on entry {epc:04X}: {ex}")
            continue

        recs_by_entry[epc] += 1
        memo = {}
        its = m.it

        # 1. Stores
        for (pc, it, c, kind, v, addr) in m.stores:
            if kind != "f":
                continue
            v_nd = P.nd(v)
            cid = P.canon(v_nd, it, memo)
            store_canon[epc][(pc, c)].add(cid)
            store_counts[epc][(pc, c)] += 1
            if cid not in store_exprs:
                store_exprs[cid] = fmt_expr(v_nd)

        # 2. Exit registers
        for rg in range(1, 32):
            for c in range(4):
                cid = P.canon(P.nd(r["vf"][rg][c]), its, memo)
                exit_canon[epc][(f"vf{rg}", c)].add(cid)
                exit_counts[epc][(f"vf{rg}", c)] += 1
        for c in range(4):
            cid = P.canon(P.nd(r["acc"][c]), its, memo)
            exit_canon[epc][("acc", c)].add(cid)
            exit_counts[epc][("acc", c)] += 1
        cid_q = P.canon(P.nd(r["q"]), its, memo)
        exit_canon[epc][("q", 0)].add(cid_q)
        exit_counts[epc][("q", 0)] += 1

        # 3. Cycles and loop iterations
        cyc = rec["x"]["cycle"] - rec["e"]["cycle"]
        cycles_data[epc].append((rec["ehash"], cyc, its, list(e["st"]["vi"])))

    print("\n" + "=" * 80)
    print("PROVENANCE SUMMARY BY ENTRY")
    print("=" * 80)

    for epc in ENTRIES:
        n = recs_by_entry[epc]
        print(f"\n--- Entry 0x{epc:04X} ({n} records) ---")

        # Stores summary
        stores_pc = store_canon[epc]
        if not stores_pc:
            print("  Stores: None (pure computation or branch/return)")
        else:
            print("  Stores:")
            for (spc, c) in sorted(stores_pc.keys()):
                cids = stores_pc[(spc, c)]
                cnt = store_counts[epc][(spc, c)]
                rep = store_exprs[next(iter(cids))]
                print(f"    Store at 0x{spc:04X}.{'xyzw'[c]}: {len(cids)} distinct forms across {cnt} stores")
                print(f"      Expr: {rep}")

        # Exit register canonicality
        ex_regs = exit_canon[epc]
        all_single = True
        multi_regs = []
        for reg_key, cids in ex_regs.items():
            if len(cids) != 1:
                all_single = False
                multi_regs.append((reg_key, len(cids)))

        if all_single:
            print(f"  Exit Registers: All {len(ex_regs)} exit lanes have EXACTLY 1 canonical form (single canonical function: YES)")
        else:
            print(f"  Exit Registers: Multiple canonical forms in {len(multi_regs)} lanes: {multi_regs[:8]}")

        # Cycle model analysis
        cyc_list = cycles_data[epc]
        if cyc_list:
            cycs_by_it = collections.defaultdict(set)
            cycs_by_hash = collections.defaultdict(collections.Counter)
            for ehash, cyc, its, vi_list in cyc_list:
                cycs_by_it[its].add(cyc)
                cycs_by_hash[f"{ehash:016x}"][cyc] += 1

            print("  Cycle counts by loop iterations (its):")
            for its, cset in sorted(cycs_by_it.items())[:8]:
                print(f"    its={its}: cycles={sorted(cset)}")

            # Fit cycle formula: cycles = base + rate * its
            pts = [(its, next(iter(cset))) for its, cset in sorted(cycs_by_it.items()) if len(cset) == 1]
            if len(pts) >= 2:
                slopes = set((pts[i + 1][1] - pts[i][1]) / (pts[i + 1][0] - pts[i][0]) for i in range(len(pts) - 1))
                if len(slopes) == 1:
                    rate = int(list(slopes)[0])
                    base = pts[0][1] - rate * pts[0][0]
                    print(f"    Cycle formula: cycles = {base} + {rate} * n (exact linear fit, slope={rate})")
                else:
                    print(f"    Slopes between points: {slopes}")
            elif len(pts) == 1:
                print(f"    Constant cycles: {pts[0][1]}")

            print("  Cycles by entry hash:")
            for eh in sorted(cycs_by_hash.keys())[:4]:
                print(f"    hash {eh}: {dict(cycs_by_hash[eh])}")


if __name__ == "__main__":
    main()
