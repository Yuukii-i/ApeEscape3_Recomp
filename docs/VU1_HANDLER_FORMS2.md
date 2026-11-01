# VU1 Handler Closed Forms: Miscellaneous Handlers (Task GE)

Derived and verified using `tools/vu1gen/hmisc_check.py` across 60 records per entry from `logs/vu1regions.bin` (region 0).

---

## 1. Summary of Handler Families

| Entry | Status | Records | Cycle Model / Formula | Float Stores | Description |
|---|---|---|---|---|---|
| `0x1C48` | **VERIFIED** | 60 | $14 + 6n$ ($n = \text{mem}[1018].w$) | Store at `0x1CA8` | Affine matrix transform routine (loads $M$ from `vi13++`) |
| `0x1C90` | **VERIFIED** | 60 | $2 + 6n$ ($n = vi2 - vi1$) | Store at `0x1CA8` | Affine matrix transform loop body |
| `0x1CB0` | **VERIFIED** | 60 | 2 cycles | None | Dispatcher return stub (`JR vi15`, `ILW.x vi1, 0(vi13)`) |
| `0x3160` | **VERIFIED** | 60 | 103 cycles ($n=4$) | Store at `0x3240` | Perspective division & normal scaling (full setup) |
| `0x31B0` | **VERIFIED** | 60 | 84 cycles ($n=2$) | Store at `0x3240` | Perspective division & normal scaling (entry with live registers) |
| `0x31E0` | **VERIFIED** | 60 | 72 cycles ($n=4$) | Store at `0x3240` | Perspective division loop setup & entry |
| `0x3220` | **VERIFIED** | 60 | 29 cycles ($n=3$) | Store at `0x3240` | Perspective division loop body |
| `0x3268` | **VERIFIED** | 60 | 2 cycles | None | Dispatcher return stub (`JR vi15`, `ILW.x vi1, 0(vi13)`) |
| `0x0AF0` | **VERIFIED** | 60 | $11 + 3n$ ($n = \text{mem}[1011].w$) | Store at `0x0B20` | Zero-quadword buffer clear loop ($n+1$ zero stores) |
| `0x0AF8` | **BLOCKED** | 60 | Block table lacking variant | None | `no block meta for pc=0AF8 sig=e2f38a47daada9de` |
| `0x0B00` | **BLOCKED** | 60 | Block table lacking variant | None | `no block meta for pc=0B00 sig=4a86e41804423013` |
| `0x0B08` | **BLOCKED** | 60 | Block table lacking variant | None | `no block meta for pc=0B08 sig=ae31827f3e66ea7a` |
| `0x0B10` | **BLOCKED** | 60 | Block table lacking variant | None | `no block meta for pc=0B10 sig=e2f79deeeeeea47b` |
| `0x0B18` | **BLOCKED** | 60 | Block table lacking variant | None | `no block meta for pc=0B18 sig=a76c692e0f6a1f59` |
| `0x0B20` | **BLOCKED** | 60 | Block table lacking variant | None | `no block meta for pc=0B20 sig=000000001234abcd` |
| `0x0B28` | **VERIFIED** | 60 | 2 cycles | None | Dispatcher return stub (`JR vi15`, `ILW.x vi1, 0(vi13)`) |
| `0x0B40` | **VERIFIED** | 60 | $23 + 12n$ ($n = \text{mem}[1018].w$) | None (integer stores) | Integer stream processing / bitfield packer |
| `0x0BC8` | **VERIFIED** | 60 | $2 + 12n$ ($n = vi2 - vi1$) | None (integer stores) | Integer stream loop body |
| `0x0C28` | **VERIFIED** | 60 | 2 cycles | None | Dispatcher return stub (`JR vi15`, `ILW.x vi1, 0(vi13)`) |

---

## 2. Group 1: Affine Transform Handlers (1C48 / 1C90 / 1CB0)

### Dataflow
- `1C48` loads 4 matrix rows $R_0, R_1, R_2, R_3$ from `(vi13++)` (`vf1..vf4`).
- Stream loop transforms 3D positions/normals $v$ from `(vi1++)`:
  $$\text{ACC} = R_0 \cdot v_x + R_1 \cdot v_y + R_2 \cdot v_z$$
  $$\text{vf6} = \text{ACC} + R_3 \cdot 1.0f$$
- Result is stored at `0x1CA8` via `SQ.xyzw vf6, -2(vi1)`.
- Loop terminates when `vi1 == vi2` and exits via `1CB0` (`JR vi15`, `ILW.x vi1, 0(vi13)`).

### Verified Evaluation Logic
```python
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
    expected = fmac(MADD, r3_c, ONE, acc)
```

---

## 3. Group 2: Perspective & Projection Handlers (3160 / 31B0 / 31E0 / 3220 / 3268)

### Dataflow
- Computes perspective division scaling factor:
  $$Q = \text{divq}(v_2.w, v_1.w)$$
- Multiplies coordinates by $Q$:
  $$v_x' = v_x \times Q$$
  $$v_y' = v_y \times Q$$
  $$v_w' = v_w \times Q$$
  $$v_z' = \text{vf2}.z + \text{vf1}.z \times v_w'$$
- Stored at `0x3240` via `SQI.xyzw vf3, (vi2++)`.

### Verified Evaluation Logic
```python
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
            expected = e["st"]["vf"][3 * 4 + c]
        else:
            expected = fmac(MADD, vf2_z, ONE, e["st"]["acc"][2])
    elif epc != 0x3220 and it == 1:
        inp = [m.recorded_loads[(0x31F0, 0, 0)], m.recorded_loads[(0x31F0, 0, 1)], 0, m.recorded_loads[(0x31F0, 0, 3)]]
        if c in (0, 1, 3):
            expected = fmac(MUL, inp[c], Q, 0)
        else:
            w_prime = fmac(MUL, inp[3], Q, 0)
            expected = fmac(MADD, vf2_z, ONE, fmac(MUL, vf1_z, w_prime, 0))
    else:
        inp = [m.recorded_loads[(0x3220, it - 1, 0)], m.recorded_loads[(0x3220, it - 1, 1)], 0, m.recorded_loads[(0x3220, it - 1, 3)]]
        if c in (0, 1, 3):
            expected = fmac(MUL, inp[c], Q, 0)
        else:
            w_prime = fmac(MUL, inp[3], Q, 0)
            expected = fmac(MADD, vf2_z, ONE, fmac(MUL, vf1_z, w_prime, 0))
```

---

## 4. Group 3: Memory Zeroing & Bitfield Handlers (0AF0..0C28)

- `0x0AF0`: Zero clear loop writing $n+1$ zero quadwords ($n = \text{mem}[1011].w$) into destination buffer at `vi3 + 716`.
- `0x0AF8..0x0B20`: Mid-loop entry variants lacking issue/cycle metadata in `vublk2`. Reported as model blocked.
- `0x0B40` & `0x0BC8`: Integer bitfield packing loop executing 12-cycle iterations with integer stores (`ISW.x vi6, -3(vi1)`).
- `0x0B28` & `0x0C28`: Return stubs executing in 2 cycles.
