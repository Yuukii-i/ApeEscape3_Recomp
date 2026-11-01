# Task GF Report: Independent Closed Form of 0B40 / 0BC8 Packer Loop

## Executive Summary
Task GF developed and fully verified bit-exact independent closed forms for the VU1 packer loop (`0BC8`) and its prologue (`0B40`) without relying on `Model.run` or emulator execution.

The implementation was verified against real execution traces streamed from `logs/vu1regions.bin` (region 0) across all 60 records per entry, achieving **zero mismatches and zero unverified fields** across 18,600 verified field checks.

---

## Verification Results

Command:
```bash
python tools/vu1gen/hpack_check.py 60
```

Output:
```text
=== Task GF: Independent Closed Forms of 0B40 / 0BC8 ===
Entry 0x0BC8: records 60, fields compared 9300, mismatches 0, unverified 0
Entry 0x0B40: records 60, fields compared 9300, mismatches 0, unverified 0
```

### Verified Field Classes (Per Record)
Every tested record checks 155 fields across 10 distinct classes:
1. **VI registers** (16 fields): All 16 integer registers $vi_0..vi_{15}$, including loop induction $vi_1, vi_2$, bit masks $vi_3, vi_4$, loaded indices $vi_5, vi_6, vi_7, vi_8$, and MAC accumulator flag recipient $vi_9$.
2. **VF registers** (128 fields): All 32 vector float registers across all 4 lanes ($x, y, z, w$).
3. **ACC register** (4 fields): Accumulator registers across all 4 lanes ($x, y, z, w$).
4. **Q register** (1 field): Division/square root register.
5. **STATUS register** (1 field): Exact VU1 status register including sticky overflow, underflow, zero, and sign flags.
6. **MAC ring state / Exit MAC** (1 field): MAC flag visible at exit cycle.
7. **CLIP ring state / Exit CLIP** (1 field): Clipping flag visible at exit cycle.
8. **Memory Diff** (1 field): Complete byte-by-byte memory state after all integer stores (`ISW.x`).
9. **Cycles** (1 field): Total elapsed cycles ($2 + 12n$ for 0BC8, $23 + 12n$ for 0B40).
10. **PC** (1 field): Target dispatch PC ($0\text{x}0028$).

**Totals**: 60 records $\times$ 155 fields = 9,300 fields per entry $\times$ 2 entries = **18,600 fields compared, 0 mismatches, 0 unverified**.

---

## Key Technical Discoveries
1. **MAC Register Timing & Reader Sync**:
   `VU1State::mac` is only updated when a reader instruction (`FMAND`, `FMOR`, `FMEQ`) executes. In 0BC8 and 0B40, the last reader instruction is `FMAND vi9, vi3` at cycle $S_{n-1} + 1$. Subsequent FMAC operations push to the ring buffer, but no further reader instructions execute prior to returning to the dispatcher at 0028. Thus, `st.mac` at exit precisely preserves the MAC value observed during that final `FMAND`.
2. **Prologue Hazard Timing**:
   Block `0B40` contains 17 prologue pairs taking 21 issue cycles before dispatching iteration 0 of `0BC8`. The additional 4 cycles over 17 are due to load hazard stalls on `vf12` and `vf2`. Total cycles are mathematically invariant: $23 + 12n$.
3. **Cross Product Parallel Evaluation**:
   In `OPMSUB.xyz vf5, vf3, vf5`, vector lanes must be evaluated simultaneously or buffered, as lane $X$ is read in subsequent lane evaluations ($Y$ and $Z$).

---

## Deliverables
- [`tools/vu1gen/hpack_check.py`](file:///c:/ApeEscape3_Recomp/tools/vu1gen/hpack_check.py): Self-contained closed-form verifier.
- [`docs/VU1_PACKER_FORM.md`](file:///c:/ApeEscape3_Recomp/docs/VU1_PACKER_FORM.md): Comprehensive mathematical and architectural derivation.
- [`docs/REPORT_GF.md`](file:///c:/ApeEscape3_Recomp/docs/REPORT_GF.md): Acceptance and verification report.
