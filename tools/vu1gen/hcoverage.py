"""Task GH: Coverage map of logs/vu1regions.bin capture.

Ranks every region entry pc by total cycles and records, marking verified entries
and testing Model.run on non-verified entries with >= 10 records.

Usage: python tools/vu1gen/hcoverage.py [logs/vu1regions.bin]
"""
import collections
import sys

sys.path.insert(0, "tools/vu1gen")
import lbmodel as L  # noqa: E402
import regions as R  # noqa: E402

VERIFIED_PCS = {
    0x2440,  # vertex
    0x0C80,  # copy
    0x20F8,  # skinned
    0x00A8, 0x0158, 0x15E0, 0x16C0,
    0x1C48, 0x1C90, 0x1CB0,
    0x3160, 0x31B0, 0x31E0, 0x3220, 0x3268,
    0x0AF0, 0x0B28, 0x0B40, 0x0BC8, 0x0C28,
}


def test_model_entry(model, rec):
    e, x = rec["e"], rec["x"]
    reg = rec["region"]
    epc = e["pc"]
    sig = "%016x" % rec["ehash"]
    reg_bounds = (0x0000, 0x0050) if reg == 1 else (0x0050, 0x3400)

    try:
        r = model.run(e, pc=epc, sig=sig, region=reg_bounds, rings=rec["rings"])
        diffs = []
        if r["pc"] != x["pc"]:
            diffs.append("pc")
        if r["vi"] != x["st"]["vi"]:
            diffs.append("vi")
        if [val for v in r["vf"] for val in v] != x["st"]["vf"]:
            diffs.append("vf")
        if r["acc"] != x["st"]["acc"]:
            diffs.append("acc")
        if r["q"] != x["st"]["q"]:
            diffs.append("q")
        if r["cycle"] != (x["cycle"] - e["cycle"]):
            diffs.append("cycle")
        # Memory diff
        actual_mem = bytearray(e["mem"])
        for qw, q_bytes in x["diff"].items():
            actual_mem[qw * 16 : qw * 16 + 16] = q_bytes
        if bytes(r["mem"]) != bytes(actual_mem):
            diffs.append("mem")

        if diffs:
            return f"mismatch in {','.join(diffs)}"
        else:
            return "matches the record exit"
    except Exception as ex:
        return f"model blocked: {ex}"


def main():
    path = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "logs/vu1regions.bin"

    code = None
    for tag, p in L.corpus.chunks("logs/vu1corpus.bin"):
        if tag == b"CODE" and L.struct.unpack_from("<Q", p)[0] == 5566:
            code = p[8:]
            break
    blk = L.load_blocks()
    model = L.Model(code, blk)

    entries = collections.defaultdict(lambda: {"count": 0, "cycles": 0, "min_cyc": 10**9, "max_cyc": 0, "sample": None})
    for rec in R.records(path):
        k = (rec["region"], rec["e"]["pc"])
        cyc = rec["x"]["cycle"] - rec["e"]["cycle"]
        entries[k]["count"] += 1
        entries[k]["cycles"] += cyc
        if cyc < entries[k]["min_cyc"]:
            entries[k]["min_cyc"] = cyc
        if cyc > entries[k]["max_cyc"]:
            entries[k]["max_cyc"] = cyc
        if entries[k]["sample"] is None:
            entries[k]["sample"] = rec

    sorted_entries = sorted(entries.items(), key=lambda item: item[1]["cycles"], reverse=True)

    header = f"{'region':<6} {'pc':<8} {'records':<8} {'cycles':<10} {'verified':<10} {'model_status'}"
    print(header)
    print("-" * len(header) + "-" * 30)

    for (reg, epc), d in sorted_entries:
        cnt = d["count"]
        tot_cyc = d["cycles"]
        is_verified = epc in VERIFIED_PCS
        ver_str = "yes" if is_verified else "no"

        if is_verified:
            status_str = "verified"
        elif cnt < 10:
            status_str = "< 10 records"
        else:
            status_str = test_model_entry(model, d["sample"])

        print(f"{reg:<6} 0x{epc:04X}   {cnt:<8} {tot_cyc:<10} {ver_str:<10} {status_str}")


if __name__ == "__main__":
    main()
