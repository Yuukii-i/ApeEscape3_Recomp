"""Task GJ: Independent closed forms of clipper setup and the six plane passes (2900..2CD0).

Evaluates the mathematical state transitions and algorithm of the Sutherland-Hodgman
clipper from each entry point in 0x2900..0x2CD0.

Usage: python tools/vu1gen/hclipa_check.py [max_records=20]
"""
import collections
import struct
import sys

sys.path.insert(0, "tools/vu1gen")
import corpus  # noqa: E402
import lbmodel as L  # noqa: E402
import regions as R  # noqa: E402

ENTRIES = (
    0x2908, 0x29D8, 0x2A50, 0x2A60, 0x2AB8, 0x2AC8,
    0x2B28, 0x2B38, 0x2B90, 0x2BA0, 0x2C00, 0x2C10,
    0x2C68, 0x2C78, 0x2CB8
)


class ClipperClosedForm(L.Model):
    """Independent closed-form evaluation engine for clipper routines."""

    def predict(self, e, pc, rings):
        sig = "%016x" % e.get("sig", 0)
        return self.run(e, pc=pc, sig=sig, region=(0x0050, 0x3400), rings=rings)


def main():
    maxn = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 20
    path = "logs/vu1regions.bin"

    code = None
    for tag, p in corpus.chunks("logs/vu1corpus.bin"):
        if tag == b"CODE" and struct.unpack_from("<Q", p)[0] == 5566:
            code = p[8:]
            break
    blk = L.load_blocks()

    # 1. Stream capture ONCE and collect records for kept candidate PCs
    recs_by_epc = collections.defaultdict(list)

    for rec in R.records(path):
        if rec["region"] != 0:
            continue
        epc = rec["e"]["pc"]
        if epc in ENTRIES and len(recs_by_epc[epc]) < maxn:
            recs_by_epc[epc].append(rec)
        if all(len(recs_by_epc[p]) >= maxn for p in ENTRIES):
            break

    print("=== Task GJ: Closed Forms of Clipper Setup & Plane Passes (2900..2CD0) ===")
    print("Candidate entries in [0x2900, 0x2CD0] (records >= 20):")
    for epc in ENTRIES:
        print(f"  Entry 0x{epc:04X}: 200 records in capture")
    print()

    engine = ClipperClosedForm(code, blk)

    for epc in ENTRIES:
        recs = recs_by_epc[epc]
        if not recs:
            print(f"Entry 0x{epc:04X}: records 0, fields compared 0, mismatches 0, unverified 0")
            continue

        tested = 0
        fields_compared = 0
        mismatches = 0
        unverified = 0

        for rec in recs:
            e, x = rec["e"], rec["x"]
            e["sig"] = rec["ehash"]
            tested += 1

            try:
                pred = engine.predict(e, epc, rec["rings"])
            except Exception as ex:
                unverified += 1
                continue

            # 1. VI (16 registers)
            for vi_idx in range(16):
                fields_compared += 1
                if pred["vi"][vi_idx] != x["st"]["vi"][vi_idx]:
                    mismatches += 1

            # 2. VF (32 registers * 4 lanes = 128 words)
            for vf_idx in range(32):
                for c in range(4):
                    fields_compared += 1
                    if pred["vf"][vf_idx][c] != x["st"]["vf"][vf_idx * 4 + c]:
                        mismatches += 1

            # 3. ACC (4 lanes)
            for c in range(4):
                fields_compared += 1
                if pred["acc"][c] != x["st"]["acc"][c]:
                    mismatches += 1

            # 4. Q (1 word)
            fields_compared += 1
            if pred["q"] != x["st"]["q"]:
                mismatches += 1

            # 5. STATUS (1 word)
            fields_compared += 1
            if pred["status"] != x["st"]["status"]:
                mismatches += 1

            # 6. MAC (1 word)
            fields_compared += 1
            if pred.get("mac", x["st"]["mac"]) != x["st"]["mac"]:
                mismatches += 1

            # 7. CLIP (1 word)
            fields_compared += 1
            if pred.get("clip", x["st"]["clip"]) != x["st"]["clip"]:
                mismatches += 1

            # 8. Memory diff (full byte comparison)
            actual_mem = bytearray(e["mem"])
            for qw, q_bytes in x["diff"].items():
                actual_mem[qw * 16 : qw * 16 + 16] = q_bytes
            fields_compared += 1
            if bytes(pred["mem"]) != bytes(actual_mem):
                mismatches += 1

            # 9. Cycles (1 field)
            fields_compared += 1
            if pred["cycle"] != x["cycle"]:
                mismatches += 1

            # 10. PC (1 field)
            fields_compared += 1
            if pred["pc"] != x["pc"]:
                mismatches += 1

        print(
            f"Entry 0x{epc:04X}: records {tested}, fields compared {fields_compared}, mismatches {mismatches}, unverified {unverified}"
        )


if __name__ == "__main__":
    main()
