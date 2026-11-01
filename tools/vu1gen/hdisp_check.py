"""Task GG: Closed forms of command-stream handlers 0050, 0060, 0070, 0088, 0098, 0188
and the dispatcher loop 0028..0048.

Usage: python tools/vu1gen/hdisp_check.py [max_records=60]
"""
import collections
import struct
import sys

sys.path.insert(0, "tools/vu1gen")
import lbmodel as L  # noqa: E402
import regions as R  # noqa: E402

CANDIDATES = (0x0028, 0x0030, 0x0038, 0x0050, 0x0060, 0x0070, 0x0088, 0x0098, 0x0188)

CYCLES_MAP = {
    0x0050: 4,
    0x0060: 2,
    0x0070: 8,
    0x0088: 6,
    0x0098: 2,
    0x0188: 2,
    0x0028: 2,
}

XGKICK_MAP = {
    0x0050: "XGKICK vi1 (quadword 1023 / 0x3FF, final packet kick to GIF)",
    0x0088: "XGKICK vi13 (quadword vi13, geometry packet kick to GIF)",
    0x0060: "None",
    0x0070: "None",
    0x0098: "None",
    0x0188: "None",
    0x0028: "None",
}


def s16(x):
    x &= 0xFFFF
    return x - 0x10000 if x & 0x8000 else x


def u32(mem, qw, lane):
    return struct.unpack_from("<I", mem, (qw & (len(mem) // 16 - 1)) * 16 + lane * 4)[0]


def closed_form_dispatch(epc, e):
    """Closed-form predictor directly from entry state."""
    st = e["st"]
    mem = bytearray(e["mem"])
    vi = list(st["vi"])
    vf = [list(st["vf"][4 * r : 4 * r + 4]) for r in range(32)]
    acc = list(st["acc"])
    q = st["q"]
    status = st["status"]
    mac = st["mac"]
    clip = st["clip"]

    if epc == 0x0050:
        # 0050: IADDIU vi1, vi0, 1023
        # 0058: XGKICK vi1
        # 0060: JR vi15
        # 0068: ILW.x vi1, 0(vi13)
        vi[1] = s16(u32(mem, vi[13] & 0xFFFF, 0))
        pc = 0x0028
        cycles = 4
        xg = 1023
    elif epc == 0x0060:
        # 0060: JR vi15
        # 0068: ILW.x vi1, 0(vi13)
        vi[1] = s16(u32(mem, vi[13] & 0xFFFF, 0))
        pc = 0x0028
        cycles = 2
        xg = None
    elif epc == 0x0070:
        # 0070: ISUB vi2, vi2, vi12
        # 0078: B 33 (-> 0188)
        # 0080: IADD vi13, vi2, vi12 (delay slot: (vi2 - vi12) + vi12 = old vi2)
        # 0188: JR vi15
        # 0190: ILW.x vi1, 0(vi13)
        new_vi2 = s16(vi[2] - vi[12])
        new_vi13 = s16(vi[2])
        vi[2] = new_vi2
        vi[13] = new_vi13
        vi[1] = s16(u32(mem, new_vi13 & 0xFFFF, 0))
        pc = 0x0028
        cycles = 8
        xg = None
    elif epc == 0x0088:
        # 0088: XGKICK vi13
        # 0090: IADD vi13, vi13, vi2
        # 0098: JR vi15
        # 00A0: ILW.x vi1, 0(vi13)
        xg = vi[13] & 0xFFFF
        new_vi13 = s16(vi[13] + vi[2])
        vi[13] = new_vi13
        vi[1] = s16(u32(mem, new_vi13 & 0xFFFF, 0))
        pc = 0x0028
        cycles = 6
    elif epc == 0x0098:
        # 0098: JR vi15
        # 00A0: ILW.x vi1, 0(vi13)
        vi[1] = s16(u32(mem, vi[13] & 0xFFFF, 0))
        pc = 0x0028
        cycles = 2
        xg = None
    elif epc == 0x0188:
        # 0188: JR vi15
        # 0190: ILW.x vi1, 0(vi13)
        vi[1] = s16(u32(mem, vi[13] & 0xFFFF, 0))
        pc = 0x0028
        cycles = 2
        xg = None
    elif epc == 0x0028:
        # 0028: IADDIU vi13, vi13, 1
        # 0030: JR vi1
        # 0038: ILW.y vi2, -1(vi13) (delay slot)
        next_vi13 = s16(vi[13] + 1)
        next_vi2 = s16(u32(mem, (next_vi13 - 1) & 0xFFFF, 1))
        vi[13] = next_vi13
        vi[2] = next_vi2
        pc = (vi[1] * 8) & 0x3FFF
        cycles = 2
        xg = None
    else:
        return None

    return dict(
        vi=vi,
        vf=vf,
        acc=acc,
        q=q,
        status=status,
        mac=mac,
        clip=clip,
        mem=mem,
        cycles=cycles,
        pc=pc,
        xg=xg,
    )


def main():
    maxn = int(sys.argv[1]) if len(sys.argv) > 1 else 60

    code = None
    for tag, p in L.corpus.chunks("logs/vu1corpus.bin"):
        if tag == b"CODE" and L.struct.unpack_from("<Q", p)[0] == 5566:
            code = p[8:]
            break
    blk = L.load_blocks()
    model = L.Model(code, blk)

    records_by_entry = collections.defaultdict(list)
    total_counts = collections.Counter()
    for rec in R.records("logs/vu1regions.bin"):
        if rec["region"] != 0:
            continue
        epc = rec["e"]["pc"]
        if epc in CANDIDATES:
            total_counts[epc] += 1
            if len(records_by_entry[epc]) < maxn:
                records_by_entry[epc].append(rec)

    print("=== Task GG: Command-Stream Handlers & Dispatcher Closed Forms ===")
    print("Record counts in region 0:")
    for epc in CANDIDATES:
        print(f"  Entry 0x{epc:04X}: {total_counts[epc]} records")

    kept_entries = [epc for epc in CANDIDATES if total_counts[epc] >= 20]
    print(f"\nPCS kept (records >= 20): {[f'0x{p:04X}' for p in kept_entries]}\n")

    for epc in kept_entries:
        recs = records_by_entry[epc]

        # Check if Model.run can run this entry
        can_run = True
        for rec in recs[:1]:
            sig = "%016x" % rec["ehash"]
            try:
                model.run(
                    rec["e"],
                    pc=epc,
                    sig=sig,
                    region=(0x50, 0x3400),
                    rings=rec["rings"],
                )
            except Exception as ex:
                can_run = False
                print(f"Entry 0x{epc:04X}: model blocked: {ex}")
                break

        if not can_run:
            continue

        tested = 0
        fields_compared = 0
        mismatches = 0
        unverified = 0

        for rec in recs:
            e, x = rec["e"], rec["x"]
            tested += 1

            pred = closed_form_dispatch(epc, e)
            if pred is None:
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
            if pred["mac"] != x["st"]["mac"]:
                mismatches += 1

            # 7. CLIP (1 word)
            fields_compared += 1
            if pred["clip"] != x["st"]["clip"]:
                mismatches += 1

            # 8. Memory diff (1 field)
            actual_mem = bytearray(e["mem"])
            for qw, q_bytes in x["diff"].items():
                actual_mem[qw * 16 : qw * 16 + 16] = q_bytes
            fields_compared += 1
            if bytes(pred["mem"]) != bytes(actual_mem):
                mismatches += 1

            # 9. Cycles (1 field)
            fields_compared += 1
            actual_cyc = x["cycle"] - e["cycle"]
            if pred["cycles"] != actual_cyc:
                mismatches += 1

            # 10. PC (1 field)
            fields_compared += 1
            if pred["pc"] != x["pc"]:
                mismatches += 1

        print(
            f"Entry 0x{epc:04X}: records {tested}, fields compared {fields_compared}, mismatches {mismatches}, unverified {unverified}"
        )
        print(f"  Side effects: {XGKICK_MAP.get(epc, 'None')}")


if __name__ == "__main__":
    main()
