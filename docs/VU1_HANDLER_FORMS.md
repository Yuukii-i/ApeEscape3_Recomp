# VU1 Handler Closed Forms: Matrix Setup and Lerp Handlers

Derived using `tools/vu1gen/hmat_prov.py` and strictly verified with `tools/vu1gen/hmat_check.py` across 40 records per entry from `logs/vu1regions.bin` (region 0).

Every store expression listed below is verified bit-for-bit against the VU1 hardware execution using the exact FMAC primitives (`lbprov._o["fmac"]`). There are **0 unverified stores** and **0 mismatches**.

---

## Primitives & Constants

All formulas use the Level B FMAC emulation primitives:
```python
fmac = P._o["fmac"]
ADD, SUB, MADD, MSUB, MUL = 0, 1, 2, 3, 4
HALF = 0x3F000000  # 0.5f in IEEE 754 float32
```

---

## 1. Handler 0x00A8 (Matrix Setup & Normal/Position Transform)

### Disassembly & Dataflow
- **00A8..0100**: Prologue loads constant matrices from VU data memory quadwords `980`, `998`, `999`, `1000`, `981`, `1001`, `979`, `978` (relative to `vi0`).
  Computes view-projection composite matrix rows $R_0, R_1, R_2, R_3$:
  - $R_0$ (`vf1` from qword 978):
    `fmac(MADD, m1000[c], m978[2], fmac(MADD, m999[c], m978[1], fmac(MUL, m998[c], m978[0], 0)))`
  - $R_1$ (`vf2` from qword 979):
    `fmac(MADD, m1000[c], m979[2], fmac(MADD, m999[c], m979[1], fmac(MUL, m998[c], m979[0], 0)))`
  - $R_2$ (`vf3` from qword 980):
    `fmac(MADD, m1000[c], m980[2], fmac(MADD, m999[c], m980[1], fmac(MUL, m998[c], m980[0], 0)))`
  - $R_3$ (`vf4` from qword 981):
    `fmac(MADD, m1001[c], m981[3], fmac(MADD, m1000[c], m981[2], fmac(MADD, m999[c], m981[1], fmac(MUL, m998[c], m981[0], 0))))`
- **00D8..00E0**: `ILW.x vi3, 1011(vi0)`, `ILW.w vi2, 1011(vi0)` (trip count $n = \text{mem}[1011].w$).
- **00F0..0150**: Sets up stream base pointers:
  - `vi5 = vi3 + 636` (output destination for transformed vertices)
  - `vi1 = vi3 + 476` (input stream of vertices/normals)
  - `vi7 = vi3 + 716` (output destination for zero quadwords)
  - `vi6 = vi5 + vi2` (loop termination pointer)
- **0158..0178**: Transformation loop (executed $n$ times).

### Evaluated Store Formulas (`tools/vu1gen/hmat_check.py`)

#### Store 1: `0x0158` (`SQI.xyzw vf31, (vi7++)`)
Status: **VERIFIED** (0 unverified)
```python
# vf31 is zeroed in prologue at 00A8 via SUB.xyzw vf31, vf0, vf0
expected = 0
```

#### Store 2: `0x0168` (`SQI.xyzw vf6, (vi5++)`)
Status: **VERIFIED** (0 unverified)
Software-pipelined matrix-vector multiplication $M \times v$:
```python
# Input vector staging:
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

# M * inp per lane c:
expected = fmac(MADD, r3_c, inp[3],
                fmac(MADD, r2_c, inp[2],
                     fmac(MADD, r1_c, inp[1],
                          fmac(MUL, r0_c, inp[0], 0))))
```

### Cycle Formula
Status: **VERIFIED**
$$\text{cycles} = 29 + 6 \times n$$
where $n = \text{mem}[1011].w$.

---

## 2. Handler 0x0158 (Loop Body of Matrix Transform)

### Disassembly & Dataflow
- Entry directly into loop body at `0x0158` with pre-configured matrix registers `vf1..vf4`, stream pointers `vi1`, `vi5`, `vi7`, and limit `vi6`.
- Trip count: $n = vi6 - vi5$.

### Evaluated Store Formulas (`tools/vu1gen/hmat_check.py`)

#### Store 1: `0x0158` (`SQI.xyzw vf31, (vi7++)`)
Status: **VERIFIED** (0 unverified)
```python
# Preserved from entry register state
expected = e["st"]["vf"][31 * 4 + c]
```

#### Store 2: `0x0168` (`SQI.xyzw vf6, (vi5++)`)
Status: **VERIFIED** (0 unverified)
```python
if it == 1:
    # First iteration writes live entry vf6
    expected = e["st"]["vf"][6 * 4 + c]
else:
    r0_c = e["st"]["vf"][1 * 4 + c]
    r1_c = e["st"]["vf"][2 * 4 + c]
    r2_c = e["st"]["vf"][3 * 4 + c]
    r3_c = e["st"]["vf"][4 * 4 + c]

    if it == 2:
        inp = [e["st"]["vf"][5 * 4 + lc] for lc in range(4)]
    else:
        inp = [
            m.recorded_loads[(0x0160, it - 2, 0)],
            m.recorded_loads[(0x0160, it - 2, 1)],
            m.recorded_loads[(0x0170, it - 2, 2)],
            m.recorded_loads[(0x0170, it - 2, 3)],
        ]

    expected = fmac(MADD, r3_c, inp[3],
                    fmac(MADD, r2_c, inp[2],
                         fmac(MADD, r1_c, inp[1],
                              fmac(MUL, r0_c, inp[0], 0))))
```

### Cycle Formula
Status: **VERIFIED**
$$\text{cycles} = 2 + 6 \times n$$
where $n = (vi6 - vi5) \ \& \ \text{0xFFFF}$.

---

## 3. Handler 0x15E0 (Morph / Lerp Keyframe Blend Routine)

### Disassembly & Dataflow
- **15E0..1600**: Loads morph weights $W$ from `0(vi13)` and basis matrix rows $B_0, B_1, B_2$ from quadwords `989..991`.
- **1608..1618**: Computes transformed weight vector $T = B \times W$:
  $$T_c = \text{fmac}(\text{MADD}, B_2[c], W[2], \text{fmac}(\text{MADD}, B_1[c], W[1], \text{fmac}(\text{MUL}, B_0[c], W[0], 0)))$$
- **1678..1688**: Loads keyframe vectors `kf1` from `1(vi13)`, `kf2` from `2(vi13)`.
- Base vertex $\text{base}_c$ and spline basis vector $S$ are streamed across iterations.
- Blend weights:
  $$\text{dot} = (T_x \cdot S_x + T_y \cdot S_y) + T_z \cdot S_z$$
  $$w_1 = \text{fmac}(\text{MADD}, \text{dot}, 0.5f, 0.5f) = 0.5 + 0.5 \times \text{dot}$$
  $$w_2 = \text{fmac}(\text{MSUB}, \text{dot}, 0.5f, 0.5f) = 0.5 - 0.5 \times \text{dot}$$
- Linear combination:
  $$\text{result}_c = \text{base}_c + \text{kf}_1[c] \times w_1 + \text{kf}_2[c] \times w_2$$

### Evaluated Store Formulas (`tools/vu1gen/hmat_check.py`)

#### Store: `0x16E8` (`SQI.xyzw vf7, (vi2++)`)
Status: **VERIFIED** (0 unverified)
```python
W = [m.recorded_loads[(0x15E0, 0, lc)] for lc in range(3)]
B0 = [m.recorded_loads[(0x15E8, 0, lc)] for lc in range(3)]
B1 = [m.recorded_loads[(0x15F8, 0, lc)] for lc in range(3)]
B2 = [m.recorded_loads[(0x1600, 0, lc)] for lc in range(3)]

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
expected = fmac(MADD, kf2_c, w2, acc)
```

### Cycle Formula
Status: **VERIFIED**
$$\text{cycles} = 38 + 9 \times n$$
where $n = \text{mem}[1011].w$.

---

## 4. Handler 0x16C0 (Loop Body of Lerp Blend)

### Disassembly & Dataflow
- Entry directly into lerp loop body at `0x16C0` with pre-computed weights and keyframes `vf1`, `vf2`.
- Trip count: $n = vi3 - vi2$.

### Evaluated Store Formulas (`tools/vu1gen/hmat_check.py`)

#### Store: `0x16E8` (`SQI.xyzw vf7, (vi2++)`)
Status: **VERIFIED** (0 unverified)
```python
st_vf = e["st"]["vf"]
if it == 1:
    expected = st_vf[7 * 4 + c]
else:
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
    expected = fmac(MADD, vf2_c, w2, acc)
```

### Cycle Formula
Status: **VERIFIED**
$$\text{cycles} = 2 + 9 \times n$$
where $n = (vi3 - vi2) \ \& \ \text{0xFFFF}$.

---

## 5. Handler 0x1708 (Return Stub)

- Stores: None (0 stores executed).
- Cycles: Constant 2 cycles (`JR vi15` + delay slot).
- Status: **VERIFIED**

---

## Summary of Verification Results

| Handler | Records Tested | Stores Executed | Stores Verified | Stores Unverified | Store Mismatches | Cycle Mismatches |
|---|---|---|---|---|---|---|
| `0x00A8` | 40 | 21,960 | 21,960 | 0 | 0 | 0 |
| `0x0158` | 40 | 11,920 | 11,920 | 0 | 0 | 0 |
| `0x15E0` | 40 | 11,116 | 11,116 | 0 | 0 | 0 |
| `0x16C0` | 40 | 5,104 | 5,104 | 0 | 0 | 0 |
| `0x1708` | 40 | 0 | 0 | 0 | 0 | 0 |
| **Total** | **200** | **50,100** | **50,100** | **0** | **0** | **0** |
