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


---

## 6. Handler 0x0840 (Point Specular Light, Image 86503d39) // PERF-V1M

- **Inputs**:
  - Command stream at `vi13` (2 qwords, advances `vi13 += 2`):
    - `cmd[0].xyz`: light position (world/input space).
    - `cmd[1].xyzw`: light RGBA color.
  - VU memory constants:
    - `982..985` (`.xyz`): 4x3 affine matrix transforming `cmd[0].xyz` to local light position $L$.
    - `989..991` (`.xyz`): 3x3 matrix transforming `1017.xyz` (view/half-vector offset) to $H_{\text{off}}$.
    - `1015.xyzw`: 4-term specular polynomial coefficients $(c_0, c_1, c_2, c_3)$.
    - `1011.x`: vertex buffer base `base`; `1011.w`: vertex count $N$.
  - Vertex streams: positions $P_j = \text{mem}[476 + \text{base} + j].xyz$, normals $N_j = \text{mem}[556 + \text{base} + j].xyz$, colors $C_j = \text{mem}[716 + \text{base} + j].xyzw$.
- **Math**:
  - For each vertex $j \in [0, N)$:
    - $d_j = \|L - P_j\|$, $\hat{l}_j = (L - P_j) / d_j$ (via `ERLENG`/`MFP`; `ESIN vf0` is an EFU stall dummy).
    - $\hat{h}_j = \text{normalize}(H_{\text{off}} + \hat{l}_j)$ (via `RSQRT`).
    - $s_j = N_j \cdot \hat{h}_j$, $\text{spec}_j = \max(0,\ c_0 s_j + c_1 s_j^2 + c_2 s_j^4 + c_3 s_j^8)$.
    - $C_j \mathrel{+}= \text{cmd}[1] \cdot (\text{spec}_j / d_j)$.
- **Outputs**: Updates `mem[716 + base + j].xyzw` in place for $j \in [0, N)$; no GIF packet emitted.

---

## 7. Handler 0x0CC0 (Diffuse Spotlight with Cone Cull, Image 86503d39) // PERF-V1M

- **Inputs**:
  - Command stream at `vi13` (4 qwords, advances `vi13 += 4`):
    - `cmd[0].xyz`: light position.
    - `cmd[1].xyzw`: light RGBA color.
    - `cmd[2].xyz`: spotlight forward direction (negated to $D = M_{3\times 3} (-\text{cmd}[2])$).
    - `cmd[3].xyzw`: `.x` = outer-cone cosine cutoff, `.y` = angular falloff scale, `.z` = $\cos^2(\text{bounding cone})$ for early-out, `.w` = bounding-sphere offset scale.
  - VU memory constants: `989..991` (3x3 matrix), `985.xyz` (translation for $L$), `1010.xyzw` (bounding-sphere center `.xyz` & radius `.w`), `1011.x` (`base`), `1011.w` ($N$).
  - Vertex streams: $P_j$ at `476 + base + j`, $N_j$ at `556 + base + j`, $C_j$ at `716 + base + j`.
- **Math**:
  - Bounding-sphere cone cull (`FMAND` on `Sx`, bit 7 of MAC flags):
    1. $\Delta = L - (\text{mem}[1010].xyz - D \cdot (\text{mem}[1010].w \cdot \text{cmd}[3].w))$. If $\Delta \cdot D < 0$, early exit (no stores).
    2. If $(\Delta \cdot D)^2 < \|\Delta\|^2 \cdot \text{cmd}[3].z$, early exit (no stores).
  - Otherwise, for each vertex $j \in [0, N)$:
    - $d_j = \|L - P_j\|$, $\hat{l}_j = (L - P_j) / d_j$ (via `RSQRT`).
    - $\text{spot}_j = \text{clamp}((\hat{l}_j \cdot D - \text{cmd}[3].x) \cdot \text{cmd}[3].y,\ 0,\ 1)$.
    - $\text{diff}_j = \text{clamp}(\hat{l}_j \cdot N_j,\ 0,\ 1)$.
    - $C_j \mathrel{+}= \text{cmd}[1] \cdot (\text{spot}_j \cdot \text{diff}_j / d_j)$.
- **Outputs**: Updates `mem[716 + base + j].xyzw` in place for $j \in [0, N)$ when not culled; no GIF packet emitted.

---

## 8. Handler 0x1090 (Specular Spotlight, Image 86503d39) // PERF-V1M

- **Inputs**:
  - Command stream at `vi13` (4 qwords, advances `vi13 += 4`):
    - `cmd[0].xyz`: light position; `cmd[1].xyzw`: light RGBA color; `cmd[2].xyz`: spotlight direction; `cmd[3].xy`: cone cutoff & falloff scale.
  - VU memory constants: `989..991` (3x3 matrix), `985.xyz` (translation for $L$), `1017.xyz` (half-vector offset), `1015.xyzw` (4-term specular polynomial), `1011.x` (`base`), `1011.w` ($N$).
  - Vertex streams: $P_j$ at `476 + base + j`, $N_j$ at `556 + base + j`, $C_j$ at `716 + base + j`.
- **Math**:
  - For each vertex $j \in [0, N)$:
    - $d_j = \|L - P_j\|$, $\hat{l}_j = (L - P_j) / d_j$ (via `ERLENG`/`MFP`; `ESIN vf0` is an EFU stall dummy).
    - $\text{spot}_j = \min(1,\ \max(0,\ D \cdot \hat{l}_j - \text{cmd}[3].x) \cdot \text{cmd}[3].y)$ where $D = M_{3\times 3}(-\text{cmd}[2])$.
    - $\hat{h}_j = \text{normalize}(H_{\text{off}} + \hat{l}_j)$ (via `RSQRT`).
    - $x_j = (N_j \cdot \hat{h}_j) \cdot \text{spot}_j$, $\text{spec}_j = \max(0,\ c_0 x_j + c_1 x_j^2 + c_2 x_j^4 + c_3 x_j^8)$.
    - $C_j \mathrel{+}= \text{cmd}[1] \cdot (\text{spec}_j / d_j)$.
- **Outputs**: Updates `mem[716 + base + j].xyzw` in place for $j \in [0, N)$; no GIF packet emitted.

---

## 9. Handler 0x02E0 (4-Directional Specular Light, Image 86503d39) // PERF-V1N

- **Inputs**:
  - Command stream at `vi13` (7 qwords, advances `vi13 += 7`):
    - `cmd[0..2].xyzw`: 3x4 light-direction rows (4 directional lights packed across lanes `x, y, z, w`).
    - `cmd[3..6].xyzw`: 4x4 RGBA color matrix (one RGBA color per directional light).
  - VU memory constants: `986..988.xyz` (3x3 model-space transform), `1015.xyzw` (4-term specular polynomial $(c_0, c_1, c_2, c_3)$), `1011.x` (`base`), `1011.w` ($N$).
  - Vertex streams: normals $N_j = \text{mem}[556 + \text{base} + j].xyz$, colors $C_j = \text{mem}[716 + \text{base} + j].xyzw$.
  - (`02E0..0328` are dead prologue ops whose outputs are overwritten before any read or store.)
- **Math**:
  - Transform light directions: $L_x = \sum_{k=0}^2 \text{cmd}[k] \cdot \text{mem}[986][k]$, $L_y$ from `987`, $L_z$ from `988` (4-wide SIMD across the 4 lights).
  - For each vertex $j \in [0, N)$:
    - $d_j = L_x N_j.x + L_y N_j.y + L_z N_j.z$ (4 dot products in parallel).
    - $\text{spec}_j = \max(0,\ c_0 d_j + c_1 d_j^2 + c_2 d_j^4 + c_3 d_j^8)$ per lane.
    - $C_j \mathrel{+}= \sum_{i=0}^3 \text{cmd}[3 + i] \cdot \text{spec}_j[i]$.
- **Outputs**: Updates `mem[716 + base + j].xyzw` in place for $j \in [0, N)$; no GIF packet emitted.

---

## 10. Handler 0x0628 (Point Diffuse Light + Live-In Prologue Stores, Image 86503d39) // PERF-V1N

- **Inputs**:
  - Live-in registers at entry (`0628..0638`): `vi4`, `vf11`, `vf12`, `vf13` (unconditionally stored before the light body).
  - Command stream at `vi13` (2 qwords, advances `vi13 += 2`): `cmd[0].xyz` (light position), `cmd[1].xyzw` (light RGBA color).
  - VU memory constants: `982..985.xyz` (4x3 affine matrix), `1011.x` (`base`), `1011.w` ($N$).
  - Vertex streams: positions $P_j$ at `476 + base + j`, normals $N_j$ at `556 + base + j`, colors $C_j$ at `716 + base + j`.
- **Math**:
  - Prologue (`0628..0638`): stores `vf11 -> 17(vi4)`, `vf12 -> 19(vi4)`, `vf13 -> 21(vi4)`. (Because `vu1FuncExec` does not receive entry `vi4/vf11..13`, `handler0628` returns `false` to fall back to the exact interpreter.)
  - Body (`0640..0830`): $L = M_{4\times 3} \cdot \text{cmd}[0]$; for each $j \in [0, N)$, $\Delta_j = L - P_j$, $q_j = \text{RSQRT}(1, \|\Delta_j\|^2)$, $C_j \mathrel{+}= \text{cmd}[1] \cdot (\max(0, \Delta_j \cdot N_j) \cdot q_j^2)$.
- **Outputs**: Stores `17(vi4)`, `19(vi4)`, `21(vi4)` and updates `mem[716 + base + j].xyzw`; no GIF packet emitted.

---

## 11. Handler 0x1720 (Quadratic-Falloff Point Light, Image 86503d39) // PERF-V1N

- **Inputs**:
  - Command stream at `vi13` (3 qwords, advances `vi13 += 3`):
    - `cmd[0].xyz`: light position; `cmd[1].xyzw`: light RGBA color; `cmd[2].xyzw`: $(a, b, c, \text{cap})$ quadratic distance falloff coefficients and clamp ceiling.
  - VU memory constants: `982..985.xyz` (4x3 affine matrix), `1011.x` (`base`), `1011.w` ($N$).
  - Vertex streams: positions $P_j$ at `476 + base + j`, colors $C_j$ at `716 + base + j`.
- **Math**:
  - $L = M_{4\times 3} \cdot \text{cmd}[0]$.
  - For each vertex $j \in [0, N)$:
    - $d_j^2 = \|L - P_j\|^2$, $d_j = \sqrt{d_j^2}$ (via `SQRT`).
    - $\text{atten}_j = \min(\text{cap},\ \max(0,\ a \cdot d_j^2 + b \cdot d_j + c))$.
    - $C_j \mathrel{+}= \text{cmd}[1] \cdot \text{atten}_j$.
- **Outputs**: Updates `mem[716 + base + j].xyzw` in place for $j \in [0, N)$; no GIF packet emitted.

---

## 12. Handler 0x1A68 (Spherical/Hemispherical UV Generator, Image 86503d39) // PERF-V1N

- **Inputs**:
  - Command stream at `vi13` (2 qwords, advances `vi13 += 2`):
    - `cmd[0].xyz`: light/projection center; `cmd[1].xyz`: reference axis direction.
  - VU memory constants: `982..985.xyz` (4x3 affine matrix for $L$), `989..991.xyz` (3x3 matrix for $V$), `1011.x` (`base`), `1011.w` ($N$).
  - Vertex streams: positions $P_j$ at `476 + base + j`, normals $N_j$ at `556 + base + j`, output UV stream at `796 + base + j`.
- **Math**:
  - $L = M_{4\times 3} \cdot \text{cmd}[0]$, $V = M_{3\times 3} \cdot \text{cmd}[1]$.
  - For each vertex $j \in [0, N)$:
    - $\hat{l}_j = (L - P_j) / \|L - P_j\|$ (via `RSQRT`).
    - $u_j = 0.5 + 0.5 \cdot (V \cdot N_j)$, $v_j = 0.5 + 0.5 \cdot (\hat{l}_j \cdot N_j)$, $q_j = 1.0$.
- **Outputs**: Updates `mem[796 + base + j].xyz` in place (preserving `.w`) for $j \in [0, N)$; no GIF packet emitted.

---

## 13. Handler 0x0198 (4-Directional Diffuse Light, Image 86503d39) // PERF-V1O

- **Inputs**:
  - Command stream at `vi13` (7 qwords, advances `vi13 += 7`):
    - `cmd[0..2].xyzw`: 3x4 light-direction rows (4 directional lights packed across lanes `x, y, z, w`).
    - `cmd[3..6].xyzw`: 4x4 RGBA color matrix (one RGBA color per directional light).
  - VU memory constants: `986..988.xyz` (3x3 model-space transform), `1011.x` (`base`), `1011.w` ($N$).
  - Vertex streams: normals $N_j = \text{mem}[556 + \text{base} + j].xyz$, colors $C_j = \text{mem}[716 + \text{base} + j].xyzw$.
  - (`0198..01C0` are dead prologue ops whose outputs are overwritten before any read or store.)
- **Math**:
  - Transform light directions: $L_x = \sum_{k=0}^2 \text{cmd}[k] \cdot \text{mem}[986][k]$, $L_y$ from `987`, $L_z$ from `988` (4-wide SIMD across the 4 lights).
  - For each vertex $j \in [0, N)$:
    - $d_j = L_x N_j.x + L_y N_j.y + L_z N_j.z$, $\text{diff}_j = \max(0, d_j)$ per lane.
    - $C_j \mathrel{+}= \sum_{i=0}^3 \text{cmd}[3 + i] \cdot \text{diff}_j[i]$.
- **Outputs**: Updates `mem[716 + base + j].xyzw` in place for $j \in [0, N)$; no GIF packet emitted.

---

## 14. Handler 0x0B38 (Triangle Strip Backface Cull, Image 86503d39) // PERF-V1O

- **Inputs**:
  - Command header at `top` (`-1(vi13)`): `.y` = winding sign multiplier `wind` (`LQ.y vf1, -1(vi13)`).
  - VU memory constants: `1018.z` (strip offset relative to `top`, so `stripBase = top + mem[1018].z`), `1018.w` (strip length $N$).
  - Index/flag strip: `mem[stripBase + k].x` (vertex index $\text{idx}_k$) and `mem[stripBase + k].y` (ADC/flag bits $f_k$) for $k \in [0, N + 2]$.
  - Transformed vertices: $V_i = \text{mem}[636 + i].xyw$ (`z` replaced by `w`).
- **Math**:
  - For each $k \in [0, N)$:
    - For $k = 0$, $S_x = 0$; for $k = 1$, $S_x = \text{signbit}(1.0 \cdot \text{wind})$; for $k \ge 2$, $S_x = \text{signbit}(\text{dot}(V_{\text{idx}_{k-2}} \times V_{\text{idx}_{k-1}}, V_{\text{idx}_k}) \cdot \text{wind})$.
    - $\text{adc}_k = (f_k + (S_x ? \text{0x80} : 0) + \text{0x7FFF}) \ \& \ \text{0x8000}$.
    - Updates `mem[stripBase + k].x` to $\text{idx}_k \mid \text{adc}_k$.
- **Outputs**: Updates `mem[stripBase + k].x` in place for $k \in [0, N)$; no GIF packet emitted.

---

## 15. Handler 0x1910 (Position Transform with Live-In `vf9`, Image 86503d39) // PERF-V1O

- **Inputs**:
  - Live-in register at entry: `vf9` (loaded at `1908` in `1900`'s delay slot, not by `1910`).
  - Command header `.y`: `vi2` (base of 4x3 transform matrix $T$ at `0(vi2)..3(vi2).xyz`).
  - VU memory constants: `978..981.xyzw` (4x4 matrix $B$), `1011.x` (`base`), `1011.w` ($N$).
  - Vertex stream: positions $P_j = \text{mem}[476 + \text{base} + j].xyz$.
- **Math**:
  - Computes $M = B \cdot T$ (using live-in `vf9` for row 0 of $T$) and transforms $P_j$ to `mem[796 + base + j].xyz` (preserving `.w`).
  - Because `vu1FuncExec` does not receive entry `vf9`, `handler1910` returns `false` to fall back to the exact interpreter.
- **Outputs**: Updates `mem[796 + base + j].xyz` in place (via fallback); no GIF packet emitted.

---

## 16. Handler 0x1CD8 (Projective UV Transform, Image 86503d39) // PERF-V1O

- **Inputs**:
  - Command header `.y`: `vi2` (base of 4x3 matrix $T$ at `0(vi2)..3(vi2).xyz`).
  - VU memory constants: `978..981.xyzw` (4x4 matrix $B$), `1011.x` (`base`), `1011.w` ($N$).
  - Vertex streams: positions $P_j = \text{mem}[476 + \text{base} + j].xyz$, UVs $(u_j, v_j, q_j) = \text{mem}[796 + \text{base} + j].xyz$.
- **Math**:
  - $M = B \cdot T$ (4x3 matrix in `.xyz`).
  - For each vertex $j \in [0, N)$:
    - $(x', y', w') = M \cdot (P_j, 1)$.
    - $(u'_j, v'_j, q'_j) = (u_j w' + x' q_j,\ v_j w' + y' q_j,\ w' q_j)$.
- **Outputs**: Updates `mem[796 + base + j].xyz` in place (preserving `.w`) for $j \in [0, N)$; no GIF packet emitted.

---

## 17. Handler 0x32A0 (Silhouette Shadow-Volume Extrusion, Image 86503d39) // PERF-V1O

- **Inputs**:
  - Command stream at `vi13` (1 qword, advances `vi13 += 1`): `cmd[0].xyz` = light position, `cmd[0].w` = extrusion scale.
  - VU memory constants: `989..991.xyz` (3x3 matrix) + `985.xyz` (translation) for $L = M_{4\times 3} \cdot \text{cmd}[0]$, `1011.x` (`base`), `1011.w` ($N$).
  - Vertex streams: positions $P_j = \text{mem}[476 + \text{base} + j].xyz$, normals $N_j = \text{mem}[556 + \text{base} + j].xyz$.
- **Math**:
  - For each vertex $j \in [0, N)$:
    - $\Delta_j = L - P_j$, $\hat{l}_j = \Delta_j / \|\Delta_j\|$ (via `RSQRT`).
    - $\text{dot}_j = N_j \cdot \Delta_j$; `FMAND` tests `Zx | Sx` (`0x88`) on $\text{dot}_j$ to form `vi2` $\in \{0, \text{0x8}, \text{0x80}, \text{0x88}\}$.
    - $\text{scale}_j = (\text{vi2} / 16.0) \cdot \text{cmd}[0].w$ (`ITOF4` + `MUL.w`), $P_j.\text{xyz} \mathrel{+}= \hat{l}_j \cdot \text{scale}_j$.
- **Outputs**: Updates `mem[476 + base + j].xyz` in place (preserving `.w`) for $j \in [0, N)$; no GIF packet emitted.

---

## 18. Handler 0x0560 (Scale+Bias Stream with Live-In `vi4, vf15..18`, Image 86503d39) // PERF-V1P

- **Inputs**:
  - Live-in registers at entry (`0560..0578`): `vi4`, `vf15`, `vf16`, `vf17`, `vf18` (falls back if not valid in `R`).
  - Command stream at `vi13` (2 qwords, advances `vi13 += 2`): `cmd[0].xyzw` (scale), `cmd[1].xyzw` (bias).
  - VU memory constants: `1018.y` (offset relative to `top`), `1018.w` (count $N \ge 2$).
- **Math**:
  - Prologue stores `vf15..18` to `18(vi4), 20(vi4), 22(vi4), 24(vi4)`.
  - For each $k \in [0, N)$: $\text{mem}[\text{top} + \text{off} + k] = \text{cmd}[1] + \text{mem}[\text{top} + \text{off} + k] \cdot \text{cmd}[0]$.
- **Outputs**: Stores `18(vi4)..24(vi4)` and updates `mem[top + off + k].xyzw` in place; no GIF packet emitted.

---

## 19. Handler 0x0AE0 (Zero-Fill Color Stream, Image 86503d39) // PERF-V1P

- **Inputs**:
  - VU memory constants: `1011.x` (`base`), `1011.w` ($N$).
- **Math**:
  - Entry before `0AF0` (`0AE0..0AE8` are dead `ACC` / `vf15.x` ops). Zeroes $N + 1$ qwords (`0..N`) at `716 + base`, and sets `vi4 = 716 + base + N`.
- **Outputs**: Zeroes `mem[716 + base + j].xyzw` for $j \in [0, N]$; no GIF packet emitted.

---

## 20. Handler 0x0C38 (Live-In Spill + Copy Loop, Image 86503d39) // PERF-V1P

- **Inputs**:
  - Live-in registers at entry (`0C38..0C78`): `vi4`, `vi3`, `vf11..14`, `I` (not tracked in `R`, so `handler0C38` falls back to the exact interpreter).
- **Math**:
  - Clamps/converts `vf11..14` with `I`, loads `vf1..4`, stores `vf11, vf12` to `9(vi4), 11(vi4)`, then falls into the `0C80` copy loop.
- **Outputs**: Updates `9(vi4), 11(vi4)` and copies command payload to `vi3..vi2` (via fallback); no GIF packet emitted.

---

## 21. Handler 0x1CC0 (Projective UV Transform on Normals, Image 86503d39) // PERF-V1P

- **Inputs**:
  - Command header `.y`: `vi2` (base of 4x3 matrix $T$ at `0(vi2)..3(vi2).xyz`).
  - VU memory constants: `986..988.xyz` (3x3 matrix $B$, with row 3 = `vf0` = $(0, 0, 0, 1)$), `1011.x` (`base`), `1011.w` ($N$).
  - Vertex streams: normals $N_j = \text{mem}[556 + \text{base} + j].xyz$, UVs $(u_j, v_j, q_j) = \text{mem}[796 + \text{base} + j].xyz$.
- **Math**:
  - Shares the `1CD8` loop (`1CF0..1E38`) with $M = B \cdot T$ and $(x', y', w') = M \cdot (N_j, 1)$, $(u'_j, v'_j, q'_j) = (u_j w' + x' q_j,\ v_j w' + y' q_j,\ w' q_j)$, and sets `vi4 = 796 + base + N`.
- **Outputs**: Updates `mem[796 + base + j].xyz` in place (preserving `.w`) for $j \in [0, N)$; no GIF packet emitted.

---

## 22. Handler 0x1E50 (Normal-Extruded Position Offset, Image 86503d39) // PERF-V1P

- **Inputs**:
  - Command word at `0(vi13).yzw` (does not advance `vi13`).
  - VU memory constants: `1011.x` (`base`), `1011.w` ($N$).
  - Vertex streams: positions $P_j = \text{mem}[476 + \text{base} + j].xyz$, normals $N_j = \text{mem}[556 + \text{base} + j].xyz$.
- **Math**:
  - For each $j \in [0, N]$ ($N + 1$ vertices): $P_j.\text{xyz} \mathrel{+}= N_j.\text{xyz} \cdot \text{cmd}.\text{yzw}$.
- **Outputs**: Updates `mem[476 + base + j].xyz` in place (preserving `.w`) for $j \in [0, N]$; no GIF packet emitted.

---

## 23. Handlers 0x2E20 & 0x2E88 (`clipPolygon` Subroutines, Image 86503d39) // PERF-V1P

- **Inputs**:
  - Internal subroutines of `clipPolygon` (`2900..2F68`) reading live-in clipper registers (`vi7/8/9/11/12/14`, `vf1/2/17..27`); `2E20` calls `BAL 14` (`2EC8..2F60`) and returns via `JR vi15`, `2E88` branches to `2D50` (`IBEQ vi11, vi0, -40`) and returns via `JR vi12` / `JR vi1`.
- **Math**:
  - Not standalone command handlers; when entered without valid live-in clipper state in `R`, both fall back to the exact interpreter.
- **Outputs**: Clip buffer writes (via fallback); no GIF packet emitted.

---

## 24. Updated Live-In Handlers 0x0628 & 0x1910 (Image 86503d39) // PERF-V1P

- **`0x0628`**: Now executes using `R.vi[4]` and `R.vf[11..13]` whenever `R.viValid` bit 4 and `R.vfValid` bits 11..13 are set (e.g., after `0AF0+0198`, `0AE0+0198`, `32A0+0198`, `1CC0+0198`, `1CD8+0198`); falls back otherwise.
- **`0x1910`**: Now executes using `R.vf[9]` (populated in `handler1900` from `0(vi2).xyz`) whenever `R.vfValid` bit 9 is set (e.g., after `1900`); transforms `mem[476 + base + j].xyz` by `(978..981) * T` into `mem[796 + base + j].xyz` (preserving `.w`) and sets `R.vi[4] = 476`; falls back if `vf9` is not valid.


---

## 25. Task V1Q Entry Analysis & Final Live-In Completion (`0x0560`, `0x0C38`, `0x2E20`, `0x2E88`) // PERF-V1Q

- **`0x0560` — (a) Command (`JR vi1`)**:
  - **Live-ins**: `vi4` (set by `0AF0`/`0AE0`/`0B40`/`0CC0`/`1900`/`1910`/`1CC0`/`1CD8`/`32A0`) and `vf15..18` (only `02E0` leaves clean `vf15 = d_{n+2}^8`, `vf16 = max(poly4Spec(d_{n+1}), 0)`, `vf17 = d_{n+2}^2`, `vf18 = d_{n+2}^4` at `0520..0538`; `1090` clobbers `vf15..19` with scratch).
  - **Implementation**: `handler02E0` now populates `R.vf[15..18]` and sets `R.vfValid` bits `15..18`, enabling `handler0560` natively (e.g. `0AF0+02E0+0560`); `handler0560` also sets `R.I = 0.5f`, `R.iValid = true` (`05A0`).
- **`0x0C38` — (a) Command (`JR vi1`)**:
  - **Live-ins**: `I` (set by `0560`/`15E0`/`1A68` to `0.5f`, `3160` to `1.0f`, `1EE0`/`1EF0` to `255.0f`), `vi4`, and `vf11..14` (e.g. `0198`, where `02A8` leaves `vf14 = lastCol`).
  - **Implementation**: Added `R.I` / `R.iValid` tracking to `Regs` and the `I`-writing handlers, added `R.vf[14]` to `handler0198`, and implemented `handler0C38` (`MINIi` on `vf12..14`, `FTOI0` on `vf11..14`, `SQ vf11/12 -> 9/11(vi4)`, followed by the `0C80` copy loop).
- **`0x2E20` & `0x2E88` — (b) Internal `clipPolygon` (`2900..2F68`) Subroutines**:
  - **Call sites**: `2A50..2C68` call `BAL -> 2DB8` (edge loop containing `2E20..2E80` vertex-emit / `BAL 14 -> 2EC8`); `2DD8` sets `vi15 = 1489` (`0x2E88/8`) so `2E40`/`2E78` (`JR vi15`) enter `2E88` (wrap-around `JR vi12`, or `IBEQ vi11, vi0, -40 -> 2D50` all-clipped exit), while `2E50` calls `BAL 14 -> 2EC8..2F68` (returning via `JR vi1` to `2E60`). Neither is ever dispatched via `JR vi1`, and both are already covered by `clipPolygon` inside `handler1EE0`.
