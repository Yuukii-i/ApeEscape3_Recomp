# Task GD: Real Store Verification for 00A8 / 0158 / 15E0 / 16C0

## 1. Executive Summary

Task GD replaced all placeholder `pass` verification logic in `tools/vu1gen/hmat_check.py` with exact, bit-for-bit closed-form evaluations executed using the hardware FMAC emulation primitives (`lbprov._o["fmac"]`). 

Expected values are computed strictly from:
- Entry memory (`e["mem"]`) for constant quadwords and prologue data
- Entry register state (`e["st"]["vf"]`)
- Logged load words (`m.recorded_loads[(pc, iteration, lane)]`)
- FMAC arithmetic operations

**Results Across 40 Records Per Handler (200 Records Total):**
- **Stores executed**: 50,100
- **Stores verified**: 50,100 (100%)
- **Stores unverified**: 0
- **Mismatches**: 0 (0 store mismatches, 0 cycle mismatches)

---

## 2. Handler Closed Forms & Software-Pipelining Solutions

### A. Matrix Setup & Transform Handlers (`0x00A8` & `0x0158`)
- **Store `0x0158` (`SQI vf31, (vi7++)`)**:
  - `00A8`: Zeroed in prologue at `00A8` via `SUB.xyzw vf31, vf0, vf0` $\to$ `expected = 0`.
  - `0158`: Live register from entry state $\to$ `expected = e["st"]["vf"][31 * 4 + c]`.
- **Store `0x0168` (`SQI vf6, (vi5++)`)**:
  - Pipelined matrix-vector multiplication $M \times v$ using Level B fused FMAC operations:
    $$\text{ACC} = R_0 \cdot v_x$$
    $$\text{ACC} = \text{ACC} + R_1 \cdot v_y$$
    $$\text{ACC} = \text{ACC} + R_2 \cdot v_z$$
    $$\text{vf6} = \text{ACC} + R_3 \cdot v_w$$
  - In `00A8`, matrix rows $R_0..R_3$ are evaluated from constant memory quadwords `978..1001`. Input vector $v$ staging accounts for the 2-iteration software pipeline lag:
    - Iteration 1: $v$ loaded at `0120` (`vf25`)
    - Iteration 2: $v$ loaded at `0138` (`vf5`)
    - Iteration $\ge 3$: $v_{xy}$ loaded at `0160` (it - 2), $v_{zw}$ loaded at `0170` (it - 2).
  - In `0158`, matrix rows $R_0..R_3$ come from entry registers `vf1..vf4`. Iteration 1 writes entry `vf6`, iteration 2 transforms entry `vf5`, and iterations $\ge 3$ transform vectors loaded at (it - 2).

### B. Keyframe Lerp & Blend Handlers (`0x15E0` & `0x16C0`)
- **Store `0x16E8` (`SQI vf7, (vi2++)`)**:
  - Evaluates polynomial spline weight dot product:
    $$\text{dot} = (T_x \cdot S_x + T_y \cdot S_y) + T_z \cdot S_z$$
  - Evaluates blend weights:
    $$w_1 = \text{fmac}(\text{MADD}, \text{dot}, 0.5f, 0.5f) = 0.5 + 0.5 \times \text{dot}$$
    $$w_2 = \text{fmac}(\text{MSUB}, \text{dot}, 0.5f, 0.5f) = 0.5 - 0.5 \times \text{dot}$$
  - Blends keyframe targets onto base vertex:
    $$\text{ACC} = \text{base} + \text{kf}_1 \times w_1$$
    $$\text{result} = \text{ACC} + \text{kf}_2 \times w_2$$
  - In `15E0`: Transformed weight vector $T = M_{\text{basis}} \times W$ is evaluated from loads at `15E0` and `15E8..1600`. Base vertices and spline basis vectors $S$ are streamed across the ramp-up and loop iterations.
  - In `16C0`: Iteration 1 stores entry `vf7`. Iterations 2..5 consume staged pipeline registers (`vf8`, `vf5`, `vf6`, `vf4`, `vf11`). Iterations $\ge 6$ evaluate $S$ from stream loads at `1700` (it - 5).

---

## 3. Acceptance Verification Run

Command:
```bash
python tools/vu1gen/hmat_check.py 40
```

Output:
```
=== Task GD: Exact Closed-Form Store Verification ===
Entry 0x00A8: records 40, stores verified 21960, stores unverified 0, mismatches 0 (stores: 0, cycles: 0)
Entry 0x0158: records 40, stores verified 11920, stores unverified 0, mismatches 0 (stores: 0, cycles: 0)
Entry 0x15E0: records 40, stores verified 11116, stores unverified 0, mismatches 0 (stores: 0, cycles: 0)
Entry 0x16C0: records 40, stores verified 5104, stores unverified 0, mismatches 0 (stores: 0, cycles: 0)
Entry 0x1708: records 40, stores verified 0, stores unverified 0, mismatches 0 (stores: 0, cycles: 0)
---------------------------------------------------------------------------
Result: ALL VERIFIED (0 mismatches, 0 unverified)
```

---

## 4. Documentation Updates

- `docs/VU1_HANDLER_FORMS.md` completely updated with the verbatim python evaluation functions copied directly from `tools/vu1gen/hmat_check.py`.
- No `pass` branches remain anywhere in the verification pipeline.
- 0 unverified stores across all records.
