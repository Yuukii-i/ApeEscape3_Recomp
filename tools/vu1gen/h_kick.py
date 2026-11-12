"""Handler family 0050 / 0060 / 0070 / 0088 / 0098 / 0188 (kick/pointer handlers and dispatcher):
closed form checked against logs/vu1regions.bin (region 0).

Disassembly:
  0008 IADDIU vi15, vi0, 5; 0010 XTOP vi12; 0018 ILW.x vi1, 0(vi12); 0020 IADDI vi13, vi12, 0;
  0028 IADDIU vi13, vi13, 1; 0030 JR vi1; 0038 ILW.y vi2, -1(vi13); 0040 B -7; 0048 IADDIU vi15, vi0, 0
  0050 IADDIU vi1, vi0, 1023; 0058 XGKICK vi1; 0060 JR vi15; 0068 ILW.x vi1, 0(vi13);
  0060 JR vi15; 0068 ILW.x vi1, 0(vi13);
  0070 ISUB vi2, vi2, vi12; 0078 B 33; 0080 IADD vi13, vi2, vi12;
  0088 XGKICK vi13; 0090 IADD vi13, vi13, vi2; 0098 JR vi15; 00A0 ILW.x vi1, 0(vi13);
  0098 JR vi15; 00A0 ILW.x vi1, 0(vi13);
  0188 JR vi15; 0190 ILW.x vi1, 0(vi13).

Usage: python tools/vu1gen/h_kick.py [logs/vu1regions.bin]
"""
import collections
import struct
import sys

sys.path.insert(0, "tools/vu1gen")
import regions as R  # noqa: E402


def s16(x):
    x &= 0xFFFF
    return x - 0x10000 if x & 0x8000 else x


def u32(mem, qw, lane):
    return struct.unpack_from("<I", mem, (qw & (len(mem) // 16 - 1)) * 16 + lane * 4)[0]


CYCLES_MAP = {
    0x0050: 4,
    0x0060: 2,
    0x0070: 8,
    0x0088: 6,
    0x0098: 2,
    0x0188: 2,
    0x0008: 7,  # 0008..0038 if encountered
    0x0028: 2,  # 0028..0038 if encountered
}

KICK_HANDLERS = {0x0050, 0x0060, 0x0070, 0x0088, 0x0098, 0x0188, 0x0008, 0x0028}


def kick_handler(e):
    """Closed form prediction for entry state e -> (xvi, exit_pc, cycles, xg_addr)."""
    st = e["st"]
    mem = e["mem"]
    vi = list(st["vi"])
    pc0 = e["pc"]

    if pc0 not in CYCLES_MAP:
        return None

    xvi = list(vi)
    xg_addr = None

    if pc0 == 0x0008:
        # 0008 IADDIU vi15, vi0, 5
        # 0010 XTOP vi12
        # 0018 ILW.x vi1, 0(vi12)
        # 0020 IADDI vi13, vi12, 0
        # 0028 IADDIU vi13, vi13, 1
        # 0030 JR vi1
        # 0038 ILW.y vi2, -1(vi13)
        top = st.get("top", 0) & 0x3FF
        xvi[15] = 5
        xvi[12] = top
        next_vi1 = s16(u32(mem, top, 0))
        next_vi13 = s16(top + 1)
        next_vi2 = s16(u32(mem, (next_vi13 - 1) & 0xFFFF, 1))
        xvi[1] = next_vi1
        xvi[13] = next_vi13
        xvi[2] = next_vi2
        exit_pc = (next_vi1 * 8) & 0x3FFF
        return xvi, exit_pc, CYCLES_MAP[pc0], None
    elif pc0 == 0x0028:
        # 0028 IADDIU vi13, vi13, 1
        # 0030 JR vi1
        # 0038 ILW.y vi2, -1(vi13)
        next_vi13 = s16(vi[13] + 1)
        next_vi2 = s16(u32(mem, (next_vi13 - 1) & 0xFFFF, 1))
        xvi[13] = next_vi13
        xvi[2] = next_vi2
        exit_pc = (vi[1] * 8) & 0x3FFF
        return xvi, exit_pc, CYCLES_MAP[pc0], None
    elif pc0 == 0x0050:
        # 0050 IADDIU vi1, vi0, 1023
        # 0058 XGKICK vi1 (kick 1023)
        # 0060 JR vi15
        # 0068 ILW.x vi1, 0(vi13)
        xg_addr = 1023
        xvi[1] = s16(u32(mem, vi[13] & 0xFFFF, 0))
    elif pc0 == 0x0060:
        # 0060 JR vi15
        # 0068 ILW.x vi1, 0(vi13)
        xvi[1] = s16(u32(mem, vi[13] & 0xFFFF, 0))
    elif pc0 == 0x0070:
        # 0070 ISUB vi2, vi2, vi12
        # 0078 B 33 (-> 0188)
        # 0080 IADD vi13, vi2, vi12 (delay slot: new_vi2 + vi12 = old_vi2)
        # 0188 JR vi15
        # 0190 ILW.x vi1, 0(vi13)
        new_vi2 = s16(vi[2] - vi[12])
        new_vi13 = s16(new_vi2 + vi[12])  # equals s16(vi[2])
        xvi[2] = new_vi2
        xvi[13] = new_vi13
        xvi[1] = s16(u32(mem, new_vi13 & 0xFFFF, 0))
    elif pc0 == 0x0088:
        # 0088 XGKICK vi13
        # 0090 IADD vi13, vi13, vi2
        # 0098 JR vi15
        # 00A0 ILW.x vi1, 0(vi13)
        xg_addr = vi[13] & 0xFFFF
        new_vi13 = s16(vi[13] + vi[2])
        xvi[13] = new_vi13
        xvi[1] = s16(u32(mem, new_vi13 & 0xFFFF, 0))
    elif pc0 == 0x0098:
        # 0098 JR vi15
        # 00A0 ILW.x vi1, 0(vi13)
        xvi[1] = s16(u32(mem, vi[13] & 0xFFFF, 0))
    elif pc0 == 0x0188:
        # 0188 JR vi15
        # 0190 ILW.x vi1, 0(vi13)
        xvi[1] = s16(u32(mem, vi[13] & 0xFFFF, 0))

    # All these routines end with JR vi15: target = (vi15 * 8) & 0x3FFF
    exit_pc = (vi[15] * 8) & 0x3FFF
    cycles = CYCLES_MAP[pc0]

    return xvi, exit_pc, cycles, xg_addr


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "logs/vu1regions.bin"
    stats = collections.Counter()
    bad_vi = collections.Counter()
    bad_pc = collections.Counter()
    bad_cyc = collections.Counter()
    bad_other = collections.Counter()
    next_handler_hist = collections.defaultdict(collections.Counter)
    exit_pc_hist = collections.defaultdict(collections.Counter)
    xg_addrs = collections.defaultdict(set)
    xg_active_seen = collections.defaultdict(set)

    MAX_RECS_PER_ENTRY = 300

    for rec in R.records(path):
        if rec["region"] != 0:
            continue
        epc = rec["e"]["pc"]
        if epc not in KICK_HANDLERS:
            continue
        if stats[epc] >= MAX_RECS_PER_ENTRY:
            continue

        stats[epc] += 1
        e, x = rec["e"], rec["x"]
        r = kick_handler(e)
        if r is None:
            continue

        xvi, pred_pc, pred_cyc, xg_addr = r

        # Compare outputs against recorded exit state x
        xs = x["st"]
        real_cyc = x["cycle"] - e["cycle"]

        # vi mismatch check
        vi_diffs = [i for i in range(1, 16) if xvi[i] != xs["vi"][i]]
        if vi_diffs:
            bad_vi[epc] += 1

        # pc mismatch check
        if pred_pc != x["pc"]:
            bad_pc[epc] += 1

        # cycle mismatch check
        if pred_cyc != real_cyc:
            bad_cyc[epc] += 1

        # verify other state did not change
        if list(xs["vf"]) != list(e["st"]["vf"]) or xs["status"] != e["st"]["status"] or xs["acc"] != e["st"]["acc"] or xs["q"] != e["st"]["q"]:
            bad_other[epc] += 1

        # Next handler target loaded into vi1 (JR vi1 at dispatcher 0x0030)
        target_handler = (xs["vi"][1] * 8) & 0x3FFF
        next_handler_hist[epc][target_handler] += 1
        exit_pc_hist[epc][x["pc"]] += 1

        if xg_addr is not None:
            xg_addrs[epc].add(xg_addr)
            xg_active_seen[epc].add(x["pend"]["xg"])

    print("=== Task GB: Closed-Form Prediction Results ===")
    print(f"{'Entry PC':<10} {'Checked':<10} {'Bad VI':<10} {'Bad PC':<10} {'Bad Cyc':<10} {'Formula / Cycles':<20} {'XGKICK Addr':<15}")
    print("-" * 90)
    for epc in sorted(stats.keys()):
        chk = stats[epc]
        bvi = bad_vi[epc]
        bpc = bad_pc[epc]
        bcyc = bad_cyc[epc]
        cyc_str = f"fixed {CYCLES_MAP[epc]}"
        xg_str = "-"
        if epc in xg_addrs:
            addrs = sorted(xg_addrs[epc])
            addr_preview = ", ".join(f"{a}" for a in addrs[:3])
            if len(addrs) > 3:
                addr_preview += "..."
            xg_str = f"vi={addr_preview} (act={sorted(xg_active_seen[epc])})"
        print(f"0x{epc:04X}     {chk:<10} {bvi:<10} {bpc:<10} {bcyc:<10} {cyc_str:<20} {xg_str:<15}")

    total_mismatches = sum(bad_vi.values()) + sum(bad_pc.values()) + sum(bad_cyc.values()) + sum(bad_other.values())
    print("-" * 90)
    print(f"Total records checked: {sum(stats.values())}, Total mismatches: {total_mismatches}")

    print("\n=== Entry PC -> Exit PC Histogram ===")
    for epc in sorted(stats.keys()):
        exits = dict(exit_pc_hist[epc])
        print(f"0x{epc:04X} -> exit PCs: {', '.join(f'0x{p:04X}: {c}' for p, c in sorted(exits.items()))}")

    print("\n=== Entry PC -> Next Handler Targeted via (vi1 * 8) ===")
    for epc in sorted(stats.keys()):
        targets = dict(next_handler_hist[epc])
        print(f"0x{epc:04X} -> next handlers: {', '.join(f'0x{h:04X}: {c}' for h, c in sorted(targets.items()))}")


if __name__ == "__main__":
    main()
