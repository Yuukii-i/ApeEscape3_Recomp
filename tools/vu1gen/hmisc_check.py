"""Task GE: Closed forms of miscellaneous VU1 handlers.
Entries:
  1C48, 1C90, 1CB0
  3160, 31B0, 31E0, 3220, 3268
  0AF0, 0AF8, 0B00, 0B08, 0B10, 0B18, 0B20, 0B28, 0B40, 0BC8, 0C28

Usage: python tools/vu1gen/hmisc_check.py [max_records=60]
"""
import collections
import struct
import sys

sys.path.insert(0, "tools/vu1gen")
import corpus  # noqa: E402
import lbmodel as L  # noqa: E402
import lbprov as P  # noqa: E402
import regions as R  # noqa: E402

ENTRIES = (
    0x1C48, 0x1C90, 0x1CB0,
    0x3160, 0x31B0, 0x31E0, 0x3220, 0x3268,
    0x0AF0, 0x0AF8, 0x0B00, 0x0B08, 0x0B10, 0x0B18, 0x0B20, 0x0B28, 0x0B40, 0x0BC8, 0x0C28
)

fmac = P._o["fmac"]
maxmini = P._o["maxmini"]
divq = P._o["divq"]
ADD, SUB, MADD, MSUB, MUL = 0, 1, 2, 3, 4
ONE = 0x3F800000


def s16(x):
    x &= 0xFFFF
    return x - 0x10000 if x & 0x8000 else x


def u32(mem, qw, lane):
    return struct.unpack_from("<I", mem, (qw & (len(mem) // 16 - 1)) * 16 + lane * 4)[0]


class MiscVerifierModel(L.Model):
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
        self.recorded_stores.append((pc, self.it, c, int(v), addr, kind))


def predict_cycles(epc, e):
    """Predict cycle count for runnable entry."""
    mem = e["mem"]
    st_vi = e["st"]["vi"]
    if epc in (0x1CB0, 0x3268, 0x0B28, 0x0C28):
        return 2

    if epc == 0x0AF0:
        w = struct.unpack_from("<I", mem, 1011 * 16 + 12)[0] & 0xFFFF
        n = w - 0x10000 if w & 0x8000 else w
        return 11 + 3 * n

    if epc == 0x1C48:
        w = struct.unpack_from("<I", mem, 1018 * 16 + 12)[0] & 0xFFFF
        n = w - 0x10000 if w & 0x8000 else w
        return 14 + 6 * n

    if epc == 0x1C90:
        n = (st_vi[2] - st_vi[1]) & 0xFFFF
        return 2 + 6 * n

    if epc == 0x3160:
        return 103

    if epc == 0x31B0:
        return 84

    if epc == 0x31E0:
        return 72

    if epc == 0x3220:
        return 29

    if epc == 0x0B40:
        w = struct.unpack_from("<I", mem, 1018 * 16 + 12)[0] & 0xFFFF
        n = w - 0x10000 if w & 0x8000 else w
        return 23 + 12 * n

    if epc == 0x0BC8:
        n = (st_vi[2] - st_vi[1]) & 0xFFFF
        return 2 + 12 * n

    return None


def eval_float_store(epc, e, m, spc, it, c):
    """Evaluates expected float store value using FMAC primitives."""
    if epc == 0x0AF0 and spc == 0x0B20:
        return 0

    if epc in (0x1C48, 0x1C90) and spc == 0x1CA8:
        if epc == 0x1C48:
            r0_c = m.recorded_loads[(0x1C58, 0, c)]
            r1_c = m.recorded_loads[(0x1C60, 0, c)]
            r2_c = m.recorded_loads[(0x1C78, 0, c)]
            r3_c = m.recorded_loads[(0x1C80, 0, c)]
        else:
            r0_c = e["st"]["vf"][1 * 4 + c]
            r1_c = e["st"]["vf"][2 * 4 + c]
            r2_c = e["st"]["vf"][3 * 4 + c]
            r3_c = e["st"]["vf"][4 * 4 + c]

        if epc == 0x1C48 and it == 1:
            inp = [m.recorded_loads[(0x1C70, 0, lc)] for lc in range(3)]
        else:
            load_it = it - 1
            if load_it == 0 and epc == 0x1C90:
                inp = [e["st"]["vf"][5 * 4 + lc] for lc in range(3)]
            else:
                inp = [m.recorded_loads[(0x1C90, load_it, lc)] for lc in range(3)]

        acc = fmac(MADD, r2_c, inp[2], fmac(MADD, r1_c, inp[1], fmac(MUL, r0_c, inp[0], 0)))
        return fmac(MADD, r3_c, ONE, acc)

    if epc in (0x3160, 0x31B0, 0x31E0, 0x3220) and spc == 0x3240:
        if epc == 0x3220:
            Q = e["st"]["q"]
            vf1_z = e["st"]["vf"][1 * 4 + 2]
            vf2_z = e["st"]["vf"][2 * 4 + 2]
        else:
            vf4_w = e["st"]["vf"][4 * 4 + 3]
            if epc == 0x3160:
                vf1_z = m.recorded_loads[(0x3190, 0, 2)]
                vf2_z = m.recorded_loads[(0x31A0, 0, 2)]
                vf3_x_const = m.recorded_loads[(0x31A8, 0, 0)]
            elif epc == 0x31B0:
                vf1_z = e["st"]["vf"][1 * 4 + 2]
                vf2_z = e["st"]["vf"][2 * 4 + 2]
                vf3_x_const = e["st"]["vf"][3 * 4 + 0]
            else:  # 31E0
                vf1_z = e["st"]["vf"][1 * 4 + 2]
                vf2_z = e["st"]["vf"][2 * 4 + 2]
                vf3_x_const = e["st"]["vf"][3 * 4 + 0]

            v1_x = fmac(SUB, ONE, vf4_w, 0)
            v1_x = maxmini(True, v1_x, vf3_x_const)
            v2_x = maxmini(False, v1_x, 0)
            vf1_w_load = m.recorded_loads[(0x31F8, 0, 3)]
            v2_w = fmac(ADD, vf1_w_load, v2_x, 0)
            Q = divq(v2_w, vf1_w_load)

        if epc == 0x3220 and it == 1:
            if c in (0, 1, 3):
                return e["st"]["vf"][3 * 4 + c]
            else:
                return fmac(MADD, vf2_z, ONE, e["st"]["acc"][2])
        elif epc != 0x3220 and it == 1:
            inp = [m.recorded_loads[(0x31F0, 0, 0)], m.recorded_loads[(0x31F0, 0, 1)], 0, m.recorded_loads[(0x31F0, 0, 3)]]
            if c in (0, 1, 3):
                return fmac(MUL, inp[c], Q, 0)
            else:
                w_prime = fmac(MUL, inp[3], Q, 0)
                return fmac(MADD, vf2_z, ONE, fmac(MUL, vf1_z, w_prime, 0))
        else:
            inp = [m.recorded_loads[(0x3220, it - 1, 0)], m.recorded_loads[(0x3220, it - 1, 1)], 0, m.recorded_loads[(0x3220, it - 1, 3)]]
            if c in (0, 1, 3):
                return fmac(MUL, inp[c], Q, 0)
            else:
                w_prime = fmac(MUL, inp[3], Q, 0)
                return fmac(MADD, vf2_z, ONE, fmac(MUL, vf1_z, w_prime, 0))

    return None


def main():
    maxn = int(sys.argv[1]) if len(sys.argv) > 1 else 60

    code = None
    for tag, p in corpus.chunks("logs/vu1corpus.bin"):
        if tag == b"CODE" and struct.unpack_from("<Q", p)[0] == 5566:
            code = p[8:]
            break

    blk = L.load_blocks()

    records_by_entry = collections.defaultdict(list)
    for rec in R.records("logs/vu1regions.bin"):
        if rec["region"] != 0:
            continue
        epc = rec["e"]["pc"]
        if epc in ENTRIES and len(records_by_entry[epc]) < maxn:
            records_by_entry[epc].append(rec)
        if all(len(records_by_entry[p]) >= maxn for p in ENTRIES):
            break

    print("=== Task GE: Closed Forms of Handlers ===")

    for epc in ENTRIES:
        recs = records_by_entry[epc]
        if not recs:
            print(f"Entry 0x{epc:04X}: records 0, fields compared 0, mismatches 0, unverified 0")
            continue

        m = MiscVerifierModel(code, blk)
        if epc in (0x1C48, 0x1C90):
            m.head = 0x1C90
        elif epc in (0x3160, 0x31B0, 0x31E0, 0x3220):
            m.head = 0x3220
        elif epc == 0x0AF0:
            m.head = 0x0B18
        elif epc in (0x0B40, 0x0BC8):
            m.head = 0x0BC8

        reg_bound = 0x50 if epc < 0x100 else 0x100
        sig0 = "%016x" % recs[0]["ehash"]
        try:
            m.run(recs[0]["e"], pc=epc, sig=sig0, region=(reg_bound, 0x3400), rings=recs[0]["rings"])
        except Exception as ex:
            print(f"Entry 0x{epc:04X}: model blocked: {ex}")
            continue

        tested = 0
        fields_compared = 0
        mismatches = 0
        unverified = 0

        for rec in recs:
            e, x = rec["e"], rec["x"]
            tested += 1
            sig = "%016x" % rec["ehash"]

            r = m.run(e, pc=epc, sig=sig, region=(reg_bound, 0x3400), rings=rec["rings"])

            # 1. VI
            for vi_idx in range(16):
                fields_compared += 1
                if r["vi"][vi_idx] != x["st"]["vi"][vi_idx]:
                    mismatches += 1

            # 2. VF
            for vf_idx in range(32):
                for c in range(4):
                    fields_compared += 1
                    if r["vf"][vf_idx][c] != x["st"]["vf"][vf_idx * 4 + c]:
                        mismatches += 1

            # 3. ACC
            for c in range(4):
                fields_compared += 1
                if r["acc"][c] != x["st"]["acc"][c]:
                    mismatches += 1

            # 4. Q
            fields_compared += 1
            if r["q"] != x["st"]["q"]:
                mismatches += 1

            # 5. PC
            fields_compared += 1
            if x["pc"] != 0x0028:
                mismatches += 1

            # 6. Cycle model verification
            pred_cyc = predict_cycles(epc, e)
            actual_cyc = x["cycle"] - e["cycle"]
            fields_compared += 1
            if pred_cyc is None:
                unverified += 1
            elif pred_cyc != actual_cyc:
                mismatches += 1

            # 7. Memory diff verification
            actual_mem = bytearray(e["mem"])
            for qw, q in x["diff"].items():
                actual_mem[qw * 16 : qw * 16 + 16] = q
            fields_compared += 1
            if bytes(r["mem"]) != bytes(actual_mem):
                mismatches += 1

            # 8. Float stores closed-form verification
            for (spc, it, c, v, addr, kind) in m.recorded_stores:
                if kind != "f":
                    continue
                fields_compared += 1
                exp_v = eval_float_store(epc, e, m, spc, it, c)
                if exp_v is None:
                    unverified += 1
                else:
                    if int(v) != exp_v:
                        mismatches += 1

        print(
            f"Entry 0x{epc:04X}: records {tested}, fields compared {fields_compared}, mismatches {mismatches}, unverified {unverified}"
        )


if __name__ == "__main__":
    main()
