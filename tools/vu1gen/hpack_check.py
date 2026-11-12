"""Task GF: Independent closed forms of the 0B40 / 0BC8 packer handlers.

Derives the bit-exact state transitions directly from entry state and formulas,
without invoking Model.run.

Usage: python tools/vu1gen/hpack_check.py [max_records=60]
"""
import collections
import struct
import sys

sys.path.insert(0, "tools/vu1gen")
import lbmodel as L  # noqa: E402
import lbprov as P  # noqa: E402
import regions as R  # noqa: E402

fmac = P._o["fmac"]
fmac_ex = L.fmac_ex
ADD, SUB, MADD, MSUB, MUL = 0, 1, 2, 3, 4
ONE = 0x3F800000


def s16(x):
    x &= 0xFFFF
    return x - 0x10000 if x & 0x8000 else x


def u32(mem, qw, lane):
    return struct.unpack_from("<I", mem, (qw & (len(mem) // 16 - 1)) * 16 + lane * 4)[0]


def update_fmac_flags(status, kinds, a_vals, b_vals, acc_vals, dest_mask):
    """Computes updated status sticky bits and MAC flags for an FMAC operation."""
    cur = 0
    xf = 0
    mac = 0
    for c in range(4):
        lane_bit = 8 >> c
        if not (dest_mask & lane_bit):
            continue
        kind = kinds[c]
        a = a_vals[c]
        b = b_vals[c]
        acc_c = acc_vals[c]
        ex, zn, pex, pzn = fmac_ex(kind, int(a), int(b), int(acc_c))
        lf = L.lane_flags(ex, zn)
        cur |= lf
        if kind in (2, 3):
            xf |= L.lane_flags(pex, pzn) & 0xF
        lane = 8 >> c
        mac |= (lane if lf & 1 else 0) | ((lane << 4) if lf & 2 else 0) | ((lane << 8) if lf & 4 else 0) | ((lane << 12) if lf & 8 else 0)

    if dest_mask:
        cur &= 0xF
        new_status = (status & 0xFF0) | cur | ((cur | xf) << 6)
    else:
        new_status = status
    return new_status, mac


def closed_form_0bc8(e, rings):
    """Independent closed form of loop 0BC8 -> predicted exit state."""
    st = e["st"]
    mem = bytearray(e["mem"])
    dsz = len(mem)
    vi = list(st["vi"])
    vf = [list(st["vf"][4 * r : 4 * r + 4]) for r in range(32)]
    acc = list(st["acc"])
    q = st["q"]
    status = st["status"]
    cycle0 = e["cycle"]

    vi1 = vi[1]
    vi2 = vi[2]
    n = (vi2 - vi1) & 0xFFFF
    if n == 0:
        return None

    vi3 = vi[3]
    vi4 = vi[4]
    vi6 = vi[6]
    vi7 = vi[7]
    vi8 = vi[8]
    vi9 = vi[9]
    vi11 = vi[11]
    vi13 = vi[13]
    vi15 = vi[15]

    vf1 = list(vf[1])
    vf2 = list(vf[2])
    vf3 = list(vf[3])
    vf4 = list(vf[4])
    vf5 = list(vf[5])
    vf11 = list(vf[11])

    # Initial MAC ring
    if rings and "mac" in rings:
        macring = [(-100, rings["mac"]["base"])] + list(rings["mac"]["ent"])
    else:
        macring = [(-100, st["mac"])]

    last_fmand_mac = macring[0][1]

    for k in range(n):
        s_k = cycle0 + 12 * k

        # 0BC8: ADDw.xyzw vf5, vf0, vf3; IADDIU vi1, vi1, 1
        vf5 = list(vf3)
        vi1 = (vi1 + 1) & 0xFFFF

        # 0BD0: ADDw.xyzw vf3, vf0, vf2; FMAND vi9, vi3
        vf3 = list(vf2)
        fmand_cycle = s_k + 1
        vis = macring[0][1]
        for tc, vc in macring:
            if tc + 4 <= fmand_cycle:
                vis = vc
        last_fmand_mac = vis
        vi9 = (vis & 0xFFFF) & (vi3 & 0xFFFF)

        # 0BD8: NOP; LQ vf2, 636(vi7)
        q_addr = ((636 + vi7) * 16) & (dsz - 1)
        vf2 = list(struct.unpack_from("<4I", mem, q_addr))

        # 0BE0: ADDAy.x ACC, vf4, vf4; IADDIU vi9, vi9, 32767
        r = fmac(ADD, vf4[0], vf4[1], 0)
        status, mac = update_fmac_flags(
            status, [ADD, 0, 0, 0], [vf4[0], 0, 0, 0], [vf4[1], 0, 0, 0], [0, 0, 0, 0], 8
        )
        acc[0] = r
        macring.append((s_k + 3, mac))
        vi9 = (vi9 + 32767) & 0xFFFF

        # 0BE8: MADDz.x vf4, vf11, vf4; IADD vi8, vi8, vi9
        r = fmac(MADD, vf11[0], vf4[2], acc[0])
        status, mac = update_fmac_flags(
            status, [MADD, 0, 0, 0], [vf11[0], 0, 0, 0], [vf4[2], 0, 0, 0], [acc[0], 0, 0, 0], 8
        )
        vf4[0] = r
        macring.append((s_k + 4, mac))
        vi8 = (vi8 + vi9) & 0xFFFF

        # 0BF0: OPMULA.xyz ACC, vf5, vf3; IAND vi8, vi8, vi4
        acc[0] = fmac(MUL, vf5[1], vf3[2], 0)
        acc[1] = fmac(MUL, vf5[2], vf3[0], 0)
        acc[2] = fmac(MUL, vf5[0], vf3[1], 0)
        status, mac = update_fmac_flags(
            status,
            [MUL, MUL, MUL, 0],
            [vf5[1], vf5[2], vf5[0], 0],
            [vf3[2], vf3[0], vf3[1], 0],
            [0, 0, 0, 0],
            14,
        )
        macring.append((s_k + 5, mac))
        vi8 = (vi8 & vi4) & 0xFFFF

        # 0BF8: OPMSUB.xyz vf5, vf3, vf5; IOR vi6, vi6, vi8
        new_vf5 = list(vf5)
        new_vf5[0] = fmac(MSUB, vf3[1], vf5[2], acc[0])
        new_vf5[1] = fmac(MSUB, vf3[2], vf5[0], acc[1])
        new_vf5[2] = fmac(MSUB, vf3[0], vf5[1], acc[2])
        status, mac = update_fmac_flags(
            status,
            [MSUB, MSUB, MSUB, 0],
            [vf3[1], vf3[2], vf3[0], 0],
            [vf5[2], vf5[0], vf5[1], 0],
            [acc[0], acc[1], acc[2], 0],
            14,
        )
        vf5 = new_vf5
        macring.append((s_k + 6, mac))
        vi6 = (vi6 | vi8) & 0xFFFF

        # 0C00: ADDw.z vf2, vf0, vf2; ISW.x vi6, -3(vi1)
        r = fmac(ADD, 0, vf2[3], 0)
        status, mac = update_fmac_flags(
            status, [0, 0, ADD, 0], [0, 0, 0, 0], [0, 0, vf2[3], 0], [0, 0, 0, 0], 2
        )
        vf2[2] = r
        macring.append((s_k + 7, mac))

        store_addr = (((vi1 - 3) & 0xFFFF) * 16) & (dsz - 1)
        struct.pack_into("<I", mem, store_addr, vi6 & 0xFFFF)

        # 0C08: NOP; ILW.x vi6, -2(vi1)
        vi6 = s16(u32(mem, (vi1 - 2) & 0xFFFF, 0))

        # 0C10: MULy.x vf0, vf4, vf1; ILW.x vi7, 0(vi1)
        r = fmac(MUL, vf4[0], vf1[1], 0)
        status, mac = update_fmac_flags(
            status, [MUL, 0, 0, 0], [vf4[0], 0, 0, 0], [vf1[1], 0, 0, 0], [0, 0, 0, 0], 8
        )
        macring.append((s_k + 9, mac))
        vi7 = s16(u32(mem, vi1 & 0xFFFF, 0))

        # 0C18: NOP; IBNE vi1, vi2, -11
        # Loop continues if vi1 != vi2

        # 0C20: MUL.xyzw vf4, vf5, vf2; ILW.y vi8, -2(vi1)
        vf4[0] = fmac(MUL, vf5[0], vf2[0], 0)
        vf4[1] = fmac(MUL, vf5[1], vf2[1], 0)
        vf4[2] = fmac(MUL, vf5[2], vf2[2], 0)
        vf4[3] = fmac(MUL, vf5[3], vf2[3], 0)
        status, mac = update_fmac_flags(
            status, [MUL, MUL, MUL, MUL], vf5, vf2, [0, 0, 0, 0], 15
        )
        macring.append((s_k + 11, mac))
        vi8 = s16(u32(mem, (vi1 - 2) & 0xFFFF, 1))

    # Exit stub: 0C28 JR vi15; 0C30 ILW.x vi1, 0(vi13)
    vi1 = s16(u32(mem, vi13 & 0xFFFF, 0))
    xvi = list(vi)
    xvi[1] = s16(vi1)
    xvi[2] = s16(vi2)
    xvi[3] = s16(vi3)
    xvi[4] = s16(vi4)
    xvi[6] = s16(vi6)
    xvi[7] = s16(vi7)
    xvi[8] = s16(vi8)
    xvi[9] = s16(vi9)

    xvf = [list(r) for r in vf]
    xvf[2] = list(vf2)
    xvf[3] = list(vf3)
    xvf[4] = list(vf4)
    xvf[5] = list(vf5)

    cycles = 2 + 12 * n
    pc = 0x0028

    return dict(
        vi=xvi,
        vf=xvf,
        acc=acc,
        q=q,
        status=status,
        mac=last_fmand_mac,
        clip=st["clip"],
        mem=mem,
        cycles=cycles,
        pc=pc,
    )


def closed_form_0b40(e, rings):
    """Independent closed form of prologue 0B40 -> predicted exit state."""
    st = e["st"]
    mem = bytearray(e["mem"])
    dsz = len(mem)
    vi = list(st["vi"])
    vf = [list(st["vf"][4 * r : 4 * r + 4]) for r in range(32)]
    cycle0 = e["cycle"]
    status = st["status"]

    vi12 = vi[12]
    vi13 = vi[13]

    # 0B40..0BC0 Prologue execution
    # 0B40: ILW.z vi1, 1018(vi0); MAX.xyzw vf1, vf0, vf0
    vi1 = s16(u32(mem, 1018, 2))
    vf1 = [0, 0, 0, ONE]

    # 0B48: IADDIU vi3, vi0, 128; MAX.xyzw vf4, vf0, vf0
    vi3 = 128
    vf4 = [0, 0, 0, ONE]

    # 0B50: ILW.w vi2, 1018(vi0); MAXw.xyzw vf11, vf0, vf0
    vi2 = s16(u32(mem, 1018, 3))
    vf11 = [ONE, ONE, ONE, ONE]

    # 0B58: LQ.y vf1, -1(vi13)
    vf1[1] = u32(mem, (vi13 - 1) & 0xFFFF, 1)

    # 0B60: IADD vi1, vi1, vi12
    vi1 = (vi1 + vi12) & 0xFFFF

    # 0B68: ILW.x vi6, 0(vi1)
    vi6 = s16(u32(mem, vi1, 0))

    # 0B70: ILW.x vi5, 1(vi1)
    vi5 = s16(u32(mem, (vi1 + 1) & 0xFFFF, 0))

    # 0B78: IADDIU vi4, vi0, 16384
    vi4 = 16384
    # 0B80: IADDIU vi4, vi4, 16384 -> 32768 (-32768)
    vi4 = -32768

    # 0B88: LQ.xyzw vf12, 636(vi6)
    q12_addr = ((636 + vi6) * 16) & (dsz - 1)
    vf12 = list(struct.unpack_from("<4I", mem, q12_addr))

    # 0B90: LQ.xyzw vf2, 636(vi5)
    q2_addr = ((636 + vi5) * 16) & (dsz - 1)
    vf2 = list(struct.unpack_from("<4I", mem, q2_addr))

    # 0B98: ADDw.z vf12, vf0, vf12; IADD vi2, vi1, vi2
    vf12[2] = vf12[3]
    vi2 = (vi1 + vi2) & 0xFFFF

    # 0BA0: ADDw.z vf2, vf0, vf2; IADDIU vi2, vi2, 2
    vf2[2] = vf2[3]
    vi2 = (vi2 + 2) & 0xFFFF

    # 0BA8: MAX.xyzw vf3, vf12, vf12; IADDIU vi1, vi1, 2
    vf3 = list(vf12)
    vi1 = (vi1 + 2) & 0xFFFF

    # 0BB0: MUL.x vf0, vf0, vf0
    # Prologue pushes MAC at cycle0 + 18
    # In MUL.x vf0, vf0, vf0, result is 0.0, mac flags are 0
    # But wait, let's compute exact status and mac:
    status, mac_prologue = update_fmac_flags(
        status, [MUL, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], 8
    )

    # Initial MAC ring for loop contains entry ring plus the 0BB0 push at cycle0 + 18
    if rings and "mac" in rings:
        mac_ent = list(rings["mac"]["ent"])
        base = rings["mac"]["base"]
    else:
        mac_ent = []
        base = st["mac"]
    mac_ent.append((cycle0 + 18, mac_prologue))
    loop_rings = dict(mac=dict(base=base, ent=mac_ent))

    # 0BB8: ILW.x vi7, 0(vi1)
    vi7 = s16(u32(mem, vi1 & 0xFFFF, 0))

    # 0BC0: ILW.y vi8, -2(vi1)
    vi8 = s16(u32(mem, (vi1 - 2) & 0xFFFF, 1))

    # Create synthetic entry state for 0BC8 at cycle0 + 21
    loop_e = dict(
        st=dict(
            vi=[0] * 16,
            vf=[0] * 128,
            acc=list(st["acc"]),
            q=st["q"],
            status=status,
            mac=st["mac"],
            clip=st["clip"],
        ),
        mem=mem,
        cycle=cycle0 + 21,
    )
    # Populate vi
    loop_e["st"]["vi"] = list(vi)
    loop_e["st"]["vi"][1] = vi1
    loop_e["st"]["vi"][2] = vi2
    loop_e["st"]["vi"][3] = vi3
    loop_e["st"]["vi"][4] = vi4
    loop_e["st"]["vi"][5] = vi5
    loop_e["st"]["vi"][6] = vi6
    loop_e["st"]["vi"][7] = vi7
    loop_e["st"]["vi"][8] = vi8

    # Populate vf
    for r in range(32):
        loop_e["st"]["vf"][4 * r : 4 * r + 4] = list(vf[r])
    loop_e["st"]["vf"][4 * 1 : 4 * 1 + 4] = list(vf1)
    loop_e["st"]["vf"][4 * 2 : 4 * 2 + 4] = list(vf2)
    loop_e["st"]["vf"][4 * 3 : 4 * 3 + 4] = list(vf3)
    loop_e["st"]["vf"][4 * 4 : 4 * 4 + 4] = list(vf4)
    loop_e["st"]["vf"][4 * 11 : 4 * 11 + 4] = list(vf11)
    loop_e["st"]["vf"][4 * 12 : 4 * 12 + 4] = list(vf12)

    res = closed_form_0bc8(loop_e, loop_rings)
    if res is None:
        return None

    # Total cycles: prologue (21) + loop cycles (2 + 12n) = 23 + 12n
    n = (vi2 - vi1) & 0xFFFF
    res["cycles"] = 23 + 12 * n
    return res


def main():
    maxn = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    entries = (0x0BC8, 0x0B40)

    records_by_entry = collections.defaultdict(list)
    for rec in R.records("logs/vu1regions.bin"):
        if rec["region"] != 0:
            continue
        epc = rec["e"]["pc"]
        if epc in entries and len(records_by_entry[epc]) < maxn:
            records_by_entry[epc].append(rec)
        if all(len(records_by_entry[p]) >= maxn for p in entries):
            break

    print("=== Task GF: Independent Closed Forms of 0B40 / 0BC8 ===")

    for epc in entries:
        recs = records_by_entry[epc]
        tested = 0
        fields_compared = 0
        mismatches = 0
        unverified = 0

        for rec in recs:
            e, x = rec["e"], rec["x"]
            tested += 1

            if epc == 0x0BC8:
                pred = closed_form_0bc8(e, rec["rings"])
            else:
                pred = closed_form_0b40(e, rec["rings"])

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

            # 6. MAC ring state / visible MAC at exit
            fields_compared += 1
            if pred["mac"] != x["st"]["mac"]:
                mismatches += 1

            # 7. CLIP ring state / visible CLIP at exit
            fields_compared += 1
            if pred["clip"] != x["st"]["clip"]:
                mismatches += 1

            # 8. Memory diff (full bytes comparison against exit memory)
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


if __name__ == "__main__":
    main()
