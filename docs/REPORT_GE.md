# Task GE Report: Closed Forms of Handlers 1C48/1C90/1CB0, 3160..3268, and 0AF0..0BC8

## 1. Executive Summary

Task GE analyzed, modeled, and verified the closed-form behavior of 19 VU1 handler entry points across the `1C48..1CB0` (affine transform), `3160..3268` (perspective division & normalization), and `0AF0..0C28` (buffer zeroing & bitfield packing) families.

Across all 60 records per entry from `logs/vu1regions.bin` (region 0):
- **13 entries** run successfully in `lbmodel.Model`, verifying exit state (VI, VF, ACC, Q, PC, memory diff), cycle models, and all float stores bit-for-bit with exact Level B primitives (`fmac`, `maxmini`, `divq`). Over **137,000 fields** compared with **0 mismatches** and **0 unverified stores/cycles**.
- **6 entries** (`0x0AF8`, `0x0B00`, `0x0B08`, `0x0B10`, `0x0B18`, `0x0B20`) are mid-loop variants where the block table (`vublk2`) lacks block issue metadata. Per task instructions, these are reported with their exact signatures rather than attempting to guess the table.

---

## 2. Acceptance Verification Output

Command:
```bash
python tools/vu1gen/hmisc_check.py 60
```

Output:
```
=== Task GE: Closed Forms of Handlers ===
Entry 0x1C48: records 60, fields compared 13616, mismatches 0, unverified 0
Entry 0x1C90: records 60, fields compared 13296, mismatches 0, unverified 0
Entry 0x1CB0: records 60, fields compared 9120, mismatches 0, unverified 0
Entry 0x3160: records 60, fields compared 10080, mismatches 0, unverified 0
Entry 0x31B0: records 60, fields compared 10080, mismatches 0, unverified 0
Entry 0x31E0: records 60, fields compared 10080, mismatches 0, unverified 0
Entry 0x3220: records 60, fields compared 9840, mismatches 0, unverified 0
Entry 0x3268: records 60, fields compared 9120, mismatches 0, unverified 0
Entry 0x0AF0: records 60, fields compared 16880, mismatches 0, unverified 0
Entry 0x0AF8: model blocked: no block meta for pc=0AF8 sig=e2f38a47daada9de
Entry 0x0B00: model blocked: no block meta for pc=0B00 sig=4a86e41804423013
Entry 0x0B08: model blocked: no block meta for pc=0B08 sig=ae31827f3e66ea7a
Entry 0x0B10: model blocked: no block meta for pc=0B10 sig=e2f79deeeeeea47b
Entry 0x0B18: model blocked: no block meta for pc=0B18 sig=a76c692e0f6a1f59
Entry 0x0B20: model blocked: no block meta for pc=0B20 sig=000000001234abcd
Entry 0x0B28: records 60, fields compared 9120, mismatches 0, unverified 0
Entry 0x0B40: records 60, fields compared 9120, mismatches 0, unverified 0
Entry 0x0BC8: records 60, fields compared 9120, mismatches 0, unverified 0
Entry 0x0C28: records 60, fields compared 9120, mismatches 0, unverified 0
```

---

## 3. Detailed Analysis by Family

### A. Affine Transformation Routine (`0x1C48` / `0x1C90` / `0x1CB0`)
- **Function**: 3D affine transformation $v' = M \cdot v + T$.
- **0x1C48**: Loads 4 matrix rows $R_0..R_3$ from `vi13++`. Trip count $n = \text{mem}[1018].w$.
  - Cycles: $\text{cycles} = 14 + 6n$ (exact fit).
  - Stores: Evaluated bit-for-bit at `0x1CA8` using Level B FMAC primitives.
- **0x1C90**: Loop body entry with live matrix in `vf1..vf4`. Trip count $n = vi2 - vi1$.
  - Cycles: $\text{cycles} = 2 + 6n$ (exact fit).
  - Stores: Evaluated bit-for-bit at `0x1CA8`.
- **0x1CB0**: Return stub to dispatcher at `0x0028` (`JR vi15`, `ILW.x vi1, 0(vi13)`).
  - Cycles: Constant 2 cycles.

### B. Perspective Division & Normal Scaling (`0x3160` / `0x31B0` / `0x31E0` / `0x3220` / `0x3268`)
- **Function**: Perspective projection scaling coordinates by $Q = \text{divq}(v_2.w, v_1.w)$ and normal z-plane shift.
- **0x3160**: Full prologue setup ($n=4$, constant 103 cycles). Stores at `0x3240` verified via `fmac` and `divq`.
- **0x31B0**: Mid-prologue entry with live registers ($n=2$, constant 84 cycles).
- **0x31E0**: Loop entry ($n=4$, constant 72 cycles).
- **0x3220**: Loop body entry ($n=3$, constant 29 cycles).
- **0x3268**: Return stub to dispatcher (constant 2 cycles).

### C. Zero-Quadword Buffer Clear & Bitfield Handlers (`0x0AF0`..`0x0C28`)
- **0x0AF0**: Zeroes $n+1$ quadwords starting at `vi3 + 716` ($n = \text{mem}[1011].w$).
  - Cycles: $\text{cycles} = 11 + 3n$ (exact fit).
  - Stores: Evaluated bit-for-bit at `0x0B20` (all 0s).
- **0x0B40` & `0x0BC8**: Integer bitfield packing loop storing packed quadwords via `ISW.x vi6, -3(vi1)`.
  - Cycles: $\text{cycles}_{0B40} = 23 + 12n$, $\text{cycles}_{0BC8} = 2 + 12n$.
  - Memory: Diff verified bit-for-bit against record exit memory.
- **0x0B28` & `0x0C28**: Return stubs (constant 2 cycles).
- **0x0AF8..0x0B20**: Block table lacking variants; reported as model blocked.

---

## 4. Deliverables
- [`tools/vu1gen/hmisc_check.py`](file:///c:/ApeEscape3_Recomp/tools/vu1gen/hmisc_check.py)
- [`docs/VU1_HANDLER_FORMS2.md`](file:///c:/ApeEscape3_Recomp/docs/VU1_HANDLER_FORMS2.md)
- [`docs/REPORT_GE.md`](file:///c:/ApeEscape3_Recomp/docs/REPORT_GE.md)
