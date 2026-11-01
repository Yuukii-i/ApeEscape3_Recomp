# Task GB Report: Closed Form of Dispatcher and Kick/Pointer Handlers

## Overview
Implemented the closed-form predictor `tools/vu1gen/h_kick.py` (following the architecture of `tools/vu1gen/h_copy.py`) to model the VU1 dispatcher loop and kick/pointer handlers:
- **0050**: final kick of quadword 1023 (0x3FF) and return to dispatcher
- **0060**: direct return to dispatcher
- **0070**: pointer adjustment `vi2 = vi2 - vi12`, `vi13 = vi2_old`, branch to 0188
- **0088**: `XGKICK vi13`, pointer advance `vi13 = vi13 + vi2`, return to dispatcher
- **0098**: direct return to dispatcher
- **0188**: direct return to dispatcher
- **Dispatcher (0008..0048)**: initialization via `XTOP vi12`, stream loop at 0028 jumping to `JR vi1` with delay-slot `ILW.y vi2, -1(vi13)`.

---

## Handler Semantics & Closed-Form Formulas

### 1. 0x0050 (Final Kick)
- **Microcode**:
  ```
  0050: IADDIU vi1, vi0, 1023
  0058: XGKICK vi1
  0060: JR vi15
  0068: ILW.x vi1, 0(vi13)
  ```
- **Closed Form**:
  - `XGKICK` address = 1023 (0x03FF).
  - Next command word: `vi1 = s16(u32(mem, vi13 & 0xFFFF, 0))`.
  - Exit PC = `(vi15 * 8) & 0x3FFF` = `0x0028` (40).
  - Fixed cycles: **4 cycles**.

### 2. 0x0060 (Return)
- **Microcode**:
  ```
  0060: JR vi15
  0068: ILW.x vi1, 0(vi13)
  ```
- **Closed Form**:
  - Next command word: `vi1 = s16(u32(mem, vi13 & 0xFFFF, 0))`.
  - Exit PC = `(vi15 * 8) & 0x3FFF` = `0x0028` (40).
  - Fixed cycles: **2 cycles**.

### 3. 0x0070 (Pointer Adjust & Jump to 0188)
- **Microcode**:
  ```
  0070: ISUB vi2, vi2, vi12
  0078: B 33 (-> 0188)
  0080: IADD vi13, vi2, vi12    ; delay slot: (vi2 - vi12) + vi12 = old vi2
  0188: JR vi15
  0190: ILW.x vi1, 0(vi13)
  ```
- **Closed Form**:
  - `new_vi2 = s16(vi[2] - vi[12])`.
  - `new_vi13 = s16(new_vi2 + vi[12])` (equals `s16(vi[2])`).
  - Next command word: `vi1 = s16(u32(mem, new_vi13 & 0xFFFF, 0))`.
  - Exit PC = `(vi15 * 8) & 0x3FFF` = `0x0028` (40).
  - Fixed cycles: **8 cycles** (6 cycles for 0070..0080 block + 2 cycles for 0188 block).

### 4. 0x0088 (XGKICK and Pointer Advance)
- **Microcode**:
  ```
  0088: XGKICK vi13
  0090: IADD vi13, vi13, vi2
  0098: JR vi15
  00A0: ILW.x vi1, 0(vi13)
  ```
- **Closed Form**:
  - `XGKICK` address = `vi[13] & 0xFFFF`.
  - `new_vi13 = s16(vi[13] + vi[2])`.
  - Next command word: `vi1 = s16(u32(mem, new_vi13 & 0xFFFF, 0))`.
  - Exit PC = `(vi15 * 8) & 0x3FFF` = `0x0028` (40).
  - Fixed cycles: **6 cycles** (1 cycle for 0088 + 3 cycles for 0090 + 2 cycles for 0098).

### 5. 0x0098 (Return)
- **Microcode**:
  ```
  0098: JR vi15
  00A0: ILW.x vi1, 0(vi13)
  ```
- **Closed Form**:
  - Next command word: `vi1 = s16(u32(mem, vi13 & 0xFFFF, 0))`.
  - Exit PC = `(vi15 * 8) & 0x3FFF` = `0x0028` (40).
  - Fixed cycles: **2 cycles**.

### 6. 0x0188 (Return)
- **Microcode**:
  ```
  0188: JR vi15
  0190: ILW.x vi1, 0(vi13)
  ```
- **Closed Form**:
  - Next command word: `vi1 = s16(u32(mem, vi13 & 0xFFFF, 0))`.
  - Exit PC = `(vi15 * 8) & 0x3FFF` = `0x0028` (40).
  - Fixed cycles: **2 cycles**.

---

## Verification Results (`python tools/vu1gen/h_kick.py`)

```
=== Task GB: Closed-Form Prediction Results ===
Entry PC   Checked    Bad VI     Bad PC     Bad Cyc    Formula / Cycles     XGKICK Addr    
------------------------------------------------------------------------------------------
0x0050     200        0          0          0          fixed 4              vi=1023 (act=[0])
0x0060     200        0          0          0          fixed 2              -              
0x0070     200        0          0          0          fixed 8              -              
0x0088     200        0          0          0          fixed 6              vi=1, 230 (act=[0, 1])
0x0098     200        0          0          0          fixed 2              -              
0x0188     200        0          0          0          fixed 2              -              
------------------------------------------------------------------------------------------
Total records checked: 1200, Total mismatches: 0
```

---

## Entry PC -> Exit PC Histogram

All routines return via `JR vi15`. Because `vi15` is initialized to 5 by the dispatcher at 0008, every entry jumps to `(5 * 8) = 0x0028`:

| Entry PC | Total Records | Exit PC | Count |
|---|---|---|---|
| `0x0050` | 200 | `0x0028` | 200 (100%) |
| `0x0060` | 200 | `0x0028` | 200 (100%) |
| `0x0070` | 200 | `0x0028` | 200 (100%) |
| `0x0088` | 200 | `0x0028` | 200 (100%) |
| `0x0098` | 200 | `0x0028` | 200 (100%) |
| `0x0188` | 200 | `0x0028` | 200 (100%) |

---

## Next Handler Targeted via `(vi1 * 8)`

Each handler loads the next command quadword code word into `vi1` in its delay slot (`ILW.x vi1, 0(vi13)`). Upon returning to `0x0028`, the dispatcher executes `JR vi1` to dispatch to the next handler:

| Entry PC | Next Handler PC `(vi1 * 8)` | Count | Role / Description |
|---|---|---|---|
| `0x0050` | `0x0000` | 200 | End of packet / halt (`vi1 == 0`) |
| `0x0060` | `0x0000` | 200 | End of packet / halt (`vi1 == 0`) |
| `0x0070` | `0x1EE0`<br>`0x1C48`<br>`0x1EF0` | 188<br>11<br>1 | Mesh vertex transformation / lighting pipeline routines |
| `0x0088` | `0x0C80`<br>`0x0050` | 122<br>78 | Next data packet copy stream (`0x0C80`) or final kick (`0x0050`) |
| `0x0098` | `0x0C80` | 200 | Next data packet copy stream (`0x0C80`) |
| `0x0188` | `0x1EE0`<br>`0x1C48`<br>`0x0000` | 157<br>25<br>18 | Mesh vertex transformation routines, or halt (`0x0000`) |
