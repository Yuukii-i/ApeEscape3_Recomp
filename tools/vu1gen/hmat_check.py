"""Verification of closed-form store expressions and cycle models for:
  00A8 / 0158 (matrix setup & transform)
  15E0 / 16C0 / 1708 (lerp & blend)

Evaluates the closed form from logged loads / constants / entry registers and compares
with every store executed by the model across records in logs/vu1regions.bin.
Usage: python tools/vu1gen/hmat_check.py [records_per_entry=40]
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

fmac = P._o["fmac"]
ADD, SUB, MADD, MSUB, MUL = 0, 1, 2, 3, 4
HALF = 0x3F000000


class StoreVerifierModel(L.Model):
    head = None

    def start(self, e):
        self.it = 0
        self.recorded_stores = []
        self.recorded_loads = {}

    def pair(self, pc, pidx, vf, acc, q, I, vi, fdiv, t, mem):
        if self.head is not None and pc == self.head:
            self.it += 1

    def ld(self, pc, c, addr, v):
        self.recorded_loads[(pc, self.it, c)] = int(v)
        return v

    def stv(self, pc, addr, c, v, kind):
        self.recorded_stores.append((pc, self.it, c, int(v), addr))


def eval_store_00a8(e, m, spc, it, c):
    """Evaluates expected store for Entry 0x00A8."""
    if spc == 0x0158:
        # vf31 is zeroed in prologue at 00A8: SUB.xyzw vf31, vf0, vf0
        return 0

    if spc == 0x0168:
        # Matrix rows loaded from memory constants in prologue
        mem = e["mem"]

        def qword(idx):
            return [struct.unpack_from("<I", mem, idx * 16 + 4 * lc)[0] for lc in range(4)]

        m998, m999, m1000, m1001 = qword(998), qword(999), qword(1000), qword(1001)
        m980, m981, m979, m978 = qword(980), qword(981), qword(979), qword(978)

        # Row 0 (vf1 from 978):
        r0_c = fmac(MADD, m1000[c], m978[2], fmac(MADD, m999[c], m978[1], fmac(MUL, m998[c], m978[0], 0)))
        # Row 1 (vf2 from 979):
        r1_c = fmac(MADD, m1000[c], m979[2], fmac(MADD, m999[c], m979[1], fmac(MUL, m998[c], m979[0], 0)))
        # Row 2 (vf3 from 980):
        r2_c = fmac(MADD, m1000[c], m980[2], fmac(MADD, m999[c], m980[1], fmac(MUL, m998[c], m980[0], 0)))
        # Row 3 (vf4 from 981):
        r3_c = fmac(MADD, m1001[c], m981[3], fmac(MADD, m1000[c], m981[2], fmac(MADD, m999[c], m981[1], fmac(MUL, m998[c], m981[0], 0))))

        if it == 1:
            inp = [m.recorded_loads[(0x0120, 0, lc)] for lc in range(4)]
        elif it == 2:
            inp = [m.recorded_loads[(0x0138, 0, lc)] for lc in range(4)]
        else:
            inp = [
                m.recorded_loads[(0x0160, it - 2, 0)],
                m.recorded_loads[(0x0160, it - 2, 1)],
                m.recorded_loads[(0x0170, it - 2, 2)],
                m.recorded_loads[(0x0170, it - 2, 3)],
            ]

        return fmac(MADD, r3_c, inp[3], fmac(MADD, r2_c, inp[2], fmac(MADD, r1_c, inp[1], fmac(MUL, r0_c, inp[0], 0))))

    return None


def eval_store_0158(e, m, spc, it, c):
    """Evaluates expected store for Entry 0x0158."""
    st_vf = e["st"]["vf"]
    if spc == 0x0158:
        # vf31 from entry register state
        return st_vf[31 * 4 + c]

    if spc == 0x0168:
        if it == 1:
            # First store writes vf6 from entry state
            return st_vf[6 * 4 + c]

        r0_c = st_vf[1 * 4 + c]
        r1_c = st_vf[2 * 4 + c]
        r2_c = st_vf[3 * 4 + c]
        r3_c = st_vf[4 * 4 + c]

        if it == 2:
            inp = [st_vf[5 * 4 + lc] for lc in range(4)]
        else:
            inp = [
                m.recorded_loads[(0x0160, it - 2, 0)],
                m.recorded_loads[(0x0160, it - 2, 1)],
                m.recorded_loads[(0x0170, it - 2, 2)],
                m.recorded_loads[(0x0170, it - 2, 3)],
            ]

        return fmac(MADD, r3_c, inp[3], fmac(MADD, r2_c, inp[2], fmac(MADD, r1_c, inp[1], fmac(MUL, r0_c, inp[0], 0))))

    return None


def eval_store_15e0(e, m, spc, it, c):
    """Evaluates expected store for Entry 0x15E0."""
    if spc == 0x16E8:
        W = [m.recorded_loads[(0x15E0, 0, lc)] for lc in range(3)]
        B0 = [m.recorded_loads[(0x15E8, 0, lc)] for lc in range(3)]
        B1 = [m.recorded_loads[(0x15F8, 0, lc)] for lc in range(3)]
        B2 = [m.recorded_loads[(0x1600, 0, lc)] for lc in range(3)]

        # T = B0*W0 + B1*W1 + B2*W2
        T = [fmac(MADD, B2[lc], W[2], fmac(MADD, B1[lc], W[1], fmac(MUL, B0[lc], W[0], 0))) for lc in range(3)]

        kf1_c = m.recorded_loads[(0x1678, 0, c)]
        kf2_c = m.recorded_loads[(0x1680, 0, c)]

        if it == 1:
            base_c = m.recorded_loads[(0x1688, 0, c)]
            S = [m.recorded_loads[(0x1618, 0, lc)] for lc in range(3)]
        elif it == 2:
            base_c = m.recorded_loads[(0x16D0, it - 1, c)]
            S = [m.recorded_loads[(0x1620, 0, lc)] for lc in range(3)]
        elif it == 3:
            base_c = m.recorded_loads[(0x16D0, it - 1, c)]
            S = [m.recorded_loads[(0x1640, 0, lc)] for lc in range(3)]
        elif it == 4:
            base_c = m.recorded_loads[(0x16D0, it - 1, c)]
            S = [m.recorded_loads[(0x1670, 0, lc)] for lc in range(3)]
        elif it == 5:
            base_c = m.recorded_loads[(0x16D0, it - 1, c)]
            S = [m.recorded_loads[(0x16B8, 0, lc)] for lc in range(3)]
        else:
            base_c = m.recorded_loads[(0x16D0, it - 1, c)]
            S = [m.recorded_loads[(0x1700, it - 5, lc)] for lc in range(3)]

        dot = fmac(ADD, fmac(ADD, fmac(MUL, T[0], S[0], 0), fmac(MUL, T[1], S[1], 0), 0), fmac(MUL, T[2], S[2], 0), 0)
        w1 = fmac(MADD, dot, HALF, HALF)
        w2 = fmac(MSUB, dot, HALF, HALF)

        acc = fmac(MADD, kf1_c, w1, fmac(ADD, base_c, 0, 0))
        return fmac(MADD, kf2_c, w2, acc)

    return None


def eval_store_16c0(e, m, spc, it, c):
    """Evaluates expected store for Entry 0x16C0."""
    if spc == 0x16E8:
        st_vf = e["st"]["vf"]
        if it == 1:
            return st_vf[7 * 4 + c]

        vf1_c = st_vf[1 * 4 + c]
        vf2_c = st_vf[2 * 4 + c]
        base_c = m.recorded_loads[(0x16D0, it - 1, c)]

        if it == 2:
            w1 = st_vf[8 * 4 + 0]
            w2 = st_vf[5 * 4 + 0]
        else:
            if it == 3:
                dot = fmac(ADD, st_vf[6 * 4 + 0], st_vf[5 * 4 + 2], 0)
            elif it == 4:
                dot = fmac(ADD, fmac(ADD, st_vf[4 * 4 + 0], st_vf[4 * 4 + 1], 0), st_vf[4 * 4 + 2], 0)
            elif it == 5:
                vf3 = [st_vf[3 * 4 + lc] for lc in range(3)]
                vf11 = [st_vf[11 * 4 + lc] for lc in range(3)]
                dot = fmac(ADD, fmac(ADD, fmac(MUL, vf3[0], vf11[0], 0), fmac(MUL, vf3[1], vf11[1], 0), 0), fmac(MUL, vf3[2], vf11[2], 0), 0)
            else:
                vf3 = [st_vf[3 * 4 + lc] for lc in range(3)]
                S = [m.recorded_loads[(0x1700, it - 5, lc)] for lc in range(3)]
                dot = fmac(ADD, fmac(ADD, fmac(MUL, vf3[0], S[0], 0), fmac(MUL, vf3[1], S[1], 0), 0), fmac(MUL, vf3[2], S[2], 0), 0)

            w1 = fmac(MADD, dot, HALF, HALF)
            w2 = fmac(MSUB, dot, HALF, HALF)

        acc = fmac(MADD, vf1_c, w1, fmac(ADD, base_c, 0, 0))
        return fmac(MADD, vf2_c, w2, acc)

    return None


def main():
    maxn = int(sys.argv[1]) if len(sys.argv) > 1 else 40

    code = None
    for tag, p in corpus.chunks("logs/vu1corpus.bin"):
        if tag == b"CODE" and struct.unpack_from("<Q", p)[0] == 5566:
            code = p[8:]
            break

    blk = L.load_blocks()

    tested = collections.Counter()
    stores_executed = collections.Counter()
    stores_verified = collections.Counter()
    stores_unverified = collections.Counter()
    mismatches = collections.Counter()
    cyc_mismatches = collections.Counter()

    # Pre-read records for all target entries
    records_by_entry = collections.defaultdict(list)
    for rec in R.records("logs/vu1regions.bin"):
        if rec["region"] != 0:
            continue
        epc = rec["e"]["pc"]
        if epc in ENTRIES and len(records_by_entry[epc]) < maxn:
            records_by_entry[epc].append(rec)
        if all(len(records_by_entry[p]) >= maxn for p in ENTRIES):
            break

    print("=== Task GD: Exact Closed-Form Store Verification ===")

    for epc in ENTRIES:
        m = StoreVerifierModel(code, blk)
        m.head = LOOP_HEADS[epc]
        recs = records_by_entry[epc]

        for rec in recs:
            e, x = rec["e"], rec["x"]
            tested[epc] += 1
            reg_bound = 0x0050 if epc < 0x0100 else 0x0100

            r = m.run(e, pc=epc, sig="%016x" % rec["ehash"], region=(reg_bound, 0x3400), rings=rec["rings"])

            # 1. Cycle formula verification
            actual_cyc = x["cycle"] - e["cycle"]
            mem = e["mem"]
            n = 0
            if epc == 0x00A8:
                # vi2 is loaded from mem[1011].w in prologue at 00E0
                w = struct.unpack_from("<I", mem, 1011 * 16 + 12)[0] & 0xFFFF
                n = w - 0x10000 if w & 0x8000 else w
                pred_cyc = 29 + 6 * n
            elif epc == 0x0158:
                # vi6 - vi5 is remaining iterations
                n = (e["st"]["vi"][6] - e["st"]["vi"][5]) & 0xFFFF
                pred_cyc = 2 + 6 * n
            elif epc == 0x15E0:
                # vi3 is loaded from mem[1011].w in prologue at 1668
                w = struct.unpack_from("<I", mem, 1011 * 16 + 12)[0] & 0xFFFF
                n = w - 0x10000 if w & 0x8000 else w
                pred_cyc = 38 + 9 * n
            elif epc == 0x16C0:
                # vi3 - vi2 is remaining iterations
                n = (e["st"]["vi"][3] - e["st"]["vi"][2]) & 0xFFFF
                pred_cyc = 2 + 9 * n
            elif epc == 0x1708:
                pred_cyc = 2

            if pred_cyc != actual_cyc:
                cyc_mismatches[epc] += 1

            # 2. Store verification
            # Every store executed by the model is evaluated and checked against closed form
            for (spc, it, c, v, addr) in m.recorded_stores:
                stores_executed[epc] += 1

                expected = None
                if epc == 0x00A8:
                    expected = eval_store_00a8(e, m, spc, it, c)
                elif epc == 0x0158:
                    expected = eval_store_0158(e, m, spc, it, c)
                elif epc == 0x15E0:
                    expected = eval_store_15e0(e, m, spc, it, c)
                elif epc == 0x16C0:
                    expected = eval_store_16c0(e, m, spc, it, c)

                if expected is None:
                    stores_unverified[epc] += 1
                else:
                    stores_verified[epc] += 1
                    if int(v) != expected:
                        mismatches[epc] += 1

        print(
            f"Entry 0x{epc:04X}: records {tested[epc]}, "
            f"stores verified {stores_verified[epc]}, "
            f"stores unverified {stores_unverified[epc]}, "
            f"mismatches {mismatches[epc] + cyc_mismatches[epc]} "
            f"(stores: {mismatches[epc]}, cycles: {cyc_mismatches[epc]})"
        )

    all_good = sum(mismatches.values()) + sum(cyc_mismatches.values()) + sum(stores_unverified.values()) == 0
    all_stores_covered = all(stores_verified[p] == stores_executed[p] for p in ENTRIES)
    print("-" * 75)
    print("Result:", "ALL VERIFIED (0 mismatches, 0 unverified)" if (all_good and all_stores_covered) else "FAIL")


if __name__ == "__main__":
    main()
