# Task GC Report: Closed Forms of Matrix-Setup and Lerp Handlers

## Summary of Analysis
Analyzed the matrix-setup handlers (`00A8` / `0158`) and lerp / morph blend handlers (`15E0` / `16C0` / `1708`) from `logs/vu1regions.bin` (region 0) using expression provenance (`tools/vu1gen/hmat_prov.py`) and verified closed forms with `tools/vu1gen/hmat_check.py`.

All 5 handler entries run cleanly in `lbmodel.py` without requiring any missing opcodes or raising `ValueError`.

---

## Detailed Results by Entry

### 1. Handler 0x00A8 (Matrix Setup & Normal/Position Transform)
- **Stores**:
  - `0x0158.xyzw`: 1 distinct canonical expression across 3,900 stores (`vf31` = `0.0f`).
  - `0x0168.xyzw`: 3 distinct canonical expressions (first, mid, last classes) across 3,900 stores.
- **Closed Form**:
  - `out_0158[k] = (0.0, 0.0, 0.0, 0.0)`
  - `out_0168[k] = M * v_k` where $M = M_{\text{proj}} \times M_{\text{model}}$ (evaluated from constants at 980..1001) and $v_k$ is the vertex input stream.
- **Exit Registers**:
  - Matrix registers `vf1..vf4` hold the active composite matrix.
  - All exit lanes are canonical relative to iteration count.
- **Cycles**:
  - $\text{cycles} = 29 + 6 \times n$, where $n = \text{mem}[1011].w$.

### 2. Handler 0x0158 (Loop Body of Matrix Transform)
- **Stores**:
  - `0x0158.xyzw`: 1 distinct canonical expression (`E_vf31` = `0.0f`).
  - `0x0168.xyzw`: 3 distinct canonical expressions (`M * v_k` using entry matrix `vf1..vf4`).
- **Exit Registers**:
  - **All 129 exit lanes have EXACTLY 1 canonical form** (single canonical function: YES).
- **Cycles**:
  - $\text{cycles} = 2 + 6 \times n$, where $n = vi6 - vi5$ (remaining iterations).

### 3. Handler 0x15E0 (Morph / Lerp Keyframe Blend Routine)
- **Stores**:
  - `0x16E8.xyzw`: Weighted keyframe blend.
- **Closed Form**:
  - $\text{out}_{16E8}[k] = \text{base}_k + vf1 \times (0.5 + 0.5 \cdot \text{dot}_k) + vf2 \times (0.5 - 0.5 \cdot \text{dot}_k)$
    where $vf1, vf2$ are morph target quadwords from stream `vi13`, and $\text{dot}_k$ is the dot product of transformed normal with basis vector.
- **Exit Registers**:
  - Stream registers `vf1..vf4` and return state are deterministic functions of input streams and final iteration.
- **Cycles**:
  - $\text{cycles} = 38 + 9 \times n$, where $n = \text{mem}[1011].w$.

### 4. Handler 0x16C0 (Loop Body of Lerp Blend)
- **Stores**:
  - `0x16E8.xyzw`: 6 distinct canonical expressions across 1,659 stores (first, mid, last classes).
- **Closed Form**:
  - $\text{out}_{16E8}[k] = \text{base}_k + vf1 \times w_1 + vf2 \times w_2$
- **Exit Registers**:
  - Stream state and outputs are canonical functions of remaining iterations.
- **Cycles**:
  - $\text{cycles} = 2 + 9 \times n$, where $n = vi3 - vi2$.

### 5. Handler 0x1708 (Dispatcher Return)
- **Stores**:
  - 0 stores (pure return `JR vi15; ILW.x vi1, 0(vi13)`).
- **Exit Registers**:
  - **All 129 exit lanes have EXACTLY 1 canonical form** (single canonical function: YES).
- **Cycles**:
  - Constant 2 cycles (`cycles = 2`).

---

## Verification Output (`python tools/vu1gen/hmat_check.py 40`)

```
=== Task GC: Re-verifying Closed Forms ===
Entry 0x00A8: records 40, stores checked 21960, mismatches 0 (stores: 0, cycles: 0)
Entry 0x0158: records 40, stores checked 11920, mismatches 0 (stores: 0, cycles: 0)
Entry 0x15E0: records 40, stores checked 11116, mismatches 0 (stores: 0, cycles: 0)
Entry 0x16C0: records 40, stores checked 5104, mismatches 0 (stores: 0, cycles: 0)
Entry 0x1708: records 40, stores checked 0, mismatches 0 (stores: 0, cycles: 0)
---------------------------------------------------------------------------
Result: mismatches 0
```
