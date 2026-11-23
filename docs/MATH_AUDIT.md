# PS2 Arithmetic Layer Audit (EE FPU, VU0, MMI, Platform)

> Scope: Static audit of `PS2Recomp/ps2xRuntime/include/ps2_runtime_macros.h`, `PS2Recomp/ps2xRecomp/src/lib/*`, `PS2Recomp/ps2xRuntime/src/lib/*`, and build configuration (`CMakeLists.txt`, `PS2Recomp/ps2xRuntime/cmake/ReleaseMode.cmake`).
> Already fixed prior to this audit (not re-reported as open): VU0 `ps2x_vu0_flags` in `ee_gfx_decomp.cpp`, `SQRT.S` operand (`ft`), and `ps2_f2i_trunc` rounding toward zero with `0x7FFFFFFF`/`0x80000000` saturation (`ps2_runtime_macros.h:950-958`).

---

## 1. EE FPU (COP1)

### 1.1 `FPU_MAX_S` / `FPU_MIN_S` (`PS2Recomp/ps2xRecomp/src/lib/fpu_translator.cpp:96-99`)
- **Real hardware (PCSX2 / EE)**: EE FPU has no Inf/NaN; exponent `255` (`0x7F800000..0x7FFFFFFF`) is a valid finite number `>= 2^128` (`[CODE ps2_runtime_macros.h:151-155]`), and exponent `0` with nonzero mantissa is flushed to `0` (`[INFERRED]`). `MAX.S`/`MIN.S` compares PS2 floats by sign and magnitude (`[INFERRED]`).
- **Our code**: Emits `std::max(ctx->f[fs], ctx->f[ft])` and `std::min(ctx->f[fs], ctx->f[ft])` (`[CODE fpu_translator.cpp:96-99]`). Host `std::max`/`std::min` treats `0x7F800001..0x7FFFFFFF` as `NaN` (always returning the first operand `fs`) and does not flush denormal inputs (`exp == 0, mant != 0`) to zero (`[INFERRED]`).
- **Concrete input**: `fs = 0x7F800001` (PS2 huge positive, host `qNaN`), `ft = 0x7F800002` (larger PS2 positive, host `qNaN`) -> `FPU_MIN_S` returns `fs` instead of `fs`, and `FPU_MAX_S(0x3F800000, 0x7F800001)` returns `1.0f` instead of `0x7F800001` (`[INFERRED]`).

### 1.2 Denormal Inputs in `ps2_fadd` / `ps2_fsub` / `ps2_fmul` (`ps2_runtime_macros.h:158-159, 286-302`)
- **Real hardware**: Any operand with exponent `0` and nonzero mantissa is flushed to `+-0.0f` before the operation (`[INFERRED]`).
- **Our code**: `ps2_fadd`, `ps2_fsub`, `ps2_fmul` only check `ps2_fnormal(r)` on the *result* `r` (`[CODE ps2_runtime_macros.h:281-302]`). As documented in the comment (`[CODE ps2_runtime_macros.h:158-159]`), denormal operands participate with their tiny host values whenever `r` lands in normal range.
- **Concrete input**: `a = 0x00400000` (`2^-127`, PS2 `0.0f`), `b = 0x00400000` -> host `a + b = 0x00800000` (`2^-126`, normal), so `ps2_fnormal(r)` is `true` and `ps2_fadd` returns `2^-126` instead of `0.0f` (`[INFERRED]`).

### 1.3 `FPU_CEIL_W_S` / `FPU_FLOOR_W_S` / `*_L_S` Conversions (`ps2_runtime_macros.h:971-982`)
- **Real hardware**: `CVT.W.S`, `TRUNC.W.S`, `ROUND.W.S`, `CEIL.W.S`, `FLOOR.W.S` saturate out-of-range/overflow results to `0x7FFFFFFF` (positive) or `0x80000000` (negative) (`[CODE ps2_runtime_macros.h:950]`, `[INFERRED]`).
- **Our code**: `FPU_CVT_W_S`, `FPU_TRUNC_W_S`, `FPU_ROUND_W_S` use `ps2_f2i_trunc` with saturation (`[CODE ps2_runtime_macros.h:951-958, 975-976, 981]`), **but** `FPU_CEIL_W_S` (`L977`) and `FPU_FLOOR_W_S` (`L978`) use bare `(int32_t)ceilf((float)(a))` and `(int32_t)floorf((float)(a))` without saturation or exp-255 handling (`[CODE ps2_runtime_macros.h:977-978]`). `FPU_ROUND_L_S`/`TRUNC_L_S`/`CEIL_L_S`/`FLOOR_L_S`/`CVT_L_S` (`L971-974, 982`) also cast directly to `int64_t` without saturation (`[CODE ps2_runtime_macros.h:971-974, 982]`).
- **Concrete input**: `a = 1e20f` -> `FPU_CEIL_W_S(1e20f)` yields host UB / `0x80000000` on x86 instead of `0x7FFFFFFF` (`[INFERRED]`).

### 1.4 `FPU_C_*_S` Comparisons (`ps2_runtime_macros.h:983-998`, `fpu_translator.cpp:100-131`)
- **Real hardware**: Denormals (`exp == 0, mant != 0`) compare equal to `+-0.0f`; exponent `255` values are ordered finite numbers (never `NaN`) (`[INFERRED]`).
- **Our code**: Uses host `==`, `<`, `<=`, and `isnan()` (`[CODE ps2_runtime_macros.h:984-998]`). Host treats `0x7F800001` as `NaN` (`C_EQ_S` = false, `C_LT_S` = false, `C_UN_S` = true) and treats denormals as non-zero (`[INFERRED]`).
- **Concrete input**: `a = 0x00000001` (denormal), `b = 0.0f` -> `FPU_C_EQ_S(a, b)` returns `0` instead of `1`; `a = 0x7F800001`, `b = 1.0f` -> `FPU_C_LT_S(b, a)` returns `0` instead of `1` (`[INFERRED]`).

### 1.5 `FCR31` Sticky/Exception Flags (`fpu_translator.cpp:49-99`)
- **Real hardware**: EE FPU updates `FCR31` `O` (overflow), `U` (underflow), `I` (invalid, e.g. `0/0`, `sqrt(neg)`), `D` (div-by-zero), and sticky `SO`/`SU`/`SI`/`SD` bits (`[INFERRED]`).
- **Our code**: Only `COP1_S_DIV` touches `FCR31` (`if (ctx->f[ft] == 0.0f) ctx->fcr31 |= 0x100000;`, missing denormal `ft == 0` and `0/0` invalid flags) (`[CODE fpu_translator.cpp:57]`). `ADD.S`, `SUB.S`, `MUL.S`, `SQRT.S`, `RSQRT.S`, `MADD.S`, `MSUB.S` never update `FCR31` O/U/I/SO/SU/SI (`[CODE fpu_translator.cpp:49-95]`).
- **Concrete input**: `DIV.S` with `fs = 0.0f, ft = 0x00000001` (PS2 `0.0f`) -> `ctx->f[ft] == 0.0f` is false on host, so `DZ` (`0x100000`) is not set (`[INFERRED]`).

### 1.6 `MADD.S` / `MSUB.S` / `ACC` (`fpu_translator.cpp:83-95`)
- **Real hardware**: `MADD.S`/`MSUB.S` are **not** fused: `fs * ft` is rounded to single precision first, then added to/subtracted from `ACC` (`[INFERRED]`).
- **Our code**: Emits `FPU_ADD_S(ctx->f_acc, FPU_MUL_S(ctx->f[fs], ctx->f[ft]))` and `FPU_SET_ACC` (`[CODE fpu_translator.cpp:83-95]`). Product is rounded via `ps2_fmul` first, **subject to** the denormal-input gap in §1.2 and potential compiler FMA contraction if `/fp:fast` is active (`[INFERRED]`).
- **Concrete input**: `acc = 1.0f, fs = 0x00400000, ft = 2.0f` -> `ps2_fmul` produces `2^-126` instead of `0.0f` (`[INFERRED]`).

### 1.7 `FPU_ABS_S` / `FPU_NEG_S` (`ps2_runtime_macros.h:968, 970`)
- **Real hardware**: Clears or flips bit 31 without altering exponent/mantissa (`[INFERRED]`).
- **Our code**: Uses `fabsf((float)(a))` and `(-(float)(a))` (`[CODE ps2_runtime_macros.h:968, 970]`), which is safe on SSE `andps`/`xorps` unless passed through x87 or libm where signaling NaNs (exp=255) could be quieted (`[INFERRED]`).
- **Concrete input**: `a = 0xFF800001` (PS2 negative exp-255) through a non-SSE `fabsf` call (`[INFERRED]`).

---

## 2. VU0 Macro-Mode (COP2) & Micro-Mode

### 2.1 `VFTOI0/4/12/15` & `VITOF0/4/12/15` (`vu_translation_helpers.cpp:730-763`)
- **Real hardware**: `VFTOI*` converts PS2 float to 32-bit signed integer with truncation and clamping/saturation on overflow, and respects `VF0` read-only (`rt == 0` cannot be written) (`[INFERRED]`).
- **Our code**: `translateVU_VFTOI` multiplies by `2^shift` via `_mm_mul_ps` and converts via `_mm_cvttps_epi32` with **no** saturation/clamping, **no** denormal/exp-255 handling, and **no** `inst.rt != 0` guard (`[CODE vu_translation_helpers.cpp:747-763]`). `translateVU_VITOF` also lacks an `inst.rt != 0` guard (`[CODE vu_translation_helpers.cpp:730-745]`).
- **Concrete input**: `VFTOI0 vf0, vf1` or `VFTOI0 vf2, vf1` with `vf1.x = 1e20f` -> x86 `_mm_cvttps_epi32` returns `0x80000000` (`INT32_MIN`) instead of `0x7FFFFFFF`, or corrupts `ctx->vu0_vf[0]` (`[INFERRED]`).

### 2.2 `VF0` Write-Guard Missing Across Macro-Mode Translators (`vu_translation_helpers.cpp:11-525`, `vu_translator.cpp:227-263`)
- **Real hardware**: `VF0` is hardwired to `(0.0, 0.0, 0.0, 1.0)`; instructions with `vfd == 0` update flags/ACC/nothing without modifying `VF0` (`[INFERRED]`).
- **Our code**: `translateVU_VADD`, `VSUB`, `VMUL`, `VMADD`, `VMSUB`, `VMINI`, `VMAX`, `VABS`, `VMOVE`, `VMR32`, `VMFIR`, `VITOF`, `VFTOI` all write `ctx->vu0_vf[vfd]` unconditionally (`[CODE vu_translation_helpers.cpp:19, 50, 209, 283, 461, 744, 762]`, `[CODE vu_translator.cpp:232, 243, 256]`).
- **Concrete input**: `VADD.xyzw vf0, vf1, vf2` -> overwrites `ctx->vu0_vf[0]`, corrupting subsequent `VF0.w` (`1.0f`) reads (`[INFERRED]`).

### 2.3 `VMAX` / `VMINI` / `_Field` (`vu_translation_helpers.cpp:236-272, 320-362, 453-465`)
- **Real hardware**: Compares PS2 floats where exponent `255` is finite and denormals are `0` (`[INFERRED]`).
- **Our code**: Uses raw `_mm_min_ps` / `_mm_max_ps` (`[CODE vu_translation_helpers.cpp:246, 265, 459]`). On SSE, if either operand has `exp == 255, mant != 0` (host `NaN`), `_mm_min_ps(a, b)` / `_mm_max_ps(a, b)` unconditionally returns `b`! Also `_mm_min_ps(+0.0f, -0.0f)` returns `-0.0f` (`[INFERRED]`).
- **Concrete input**: `VMAX vf3, vf1, vf2` with `vf1.x = 0x7F800001` (huge positive), `vf2.x = 1.0f` -> returns `1.0f` instead of `0x7F800001` (`[INFERRED]`).

### 2.4 `VCLIPw` (`vu_translator.cpp:264-282`)
- **Real hardware**: Compares `fs.{x,y,z}` against `+-|ft.w|` using PS2 float rules (`exp == 255` finite, `exp == 0` zero) and shifts 6 bits into `CLIP` (`[INFERRED]`).
- **Our code**: Uses raw `_mm_cmpgt_ps` / `_mm_cmplt_ps` (`[CODE vu_translator.cpp:274-275]`). Any `exp == 255` (`mant != 0`) operand yields `0` for both `gt` and `lt`, silently passing clip tests (`[INFERRED]`).
- **Concrete input**: `fs.x = 0x7F800001`, `ft.w = 1.0f` -> `gt_mask` bit 0 is `0` instead of `1` (`[INFERRED]`).

### 2.5 Macro-Mode `MAC` / `Status` Flags Not Updated (`vu_translation_helpers.cpp:11-728`)
- **Real hardware**: Macro-mode upper vector ops (`VADD`, `VSUB`, `VMUL`, `VMADD`, `VMSUB`, `VADDA`, `VMADDA`, `VOPMULA`, `VOPMSUB`, etc.) update VU0 `MAC` flags and `Status` flags (Z/S/U/O and sticky bits) (`[INFERRED]`).
- **Our code**: None of the `translateVU_*` emitters in `vu_translation_helpers.cpp` call `ps2x_vu0_flags` or update `ctx->vu0_mac_flags` / `ctx->vu0_status` (`[CODE vu_translation_helpers.cpp:11-728]`). (Only hand-decomp functions in `ee_gfx_decomp.cpp` call `ps2x_vu0_flags`, e.g. `[CODE ee_gfx_decomp.cpp:845]`.)
- **Concrete input**: `VMUL vf1, vf2, vf3` followed by `CFC2 t0, vi17` (`VU0_CR_MAC`) -> reads stale `ctx->vu0_mac_flags` (`[INFERRED]`).

### 2.6 `VDIV` / `VSQRT` / `VRSQRT` / `VWAITQ` Timing & External Helpers (`vu_translation_helpers.cpp:71-96`, `vu_translator.cpp:217-218`, `ps2_runtime_macros.h:384-385, 1088-1089`)
- **Real hardware**: `VDIV`/`VSQRT` take 7 cycles and `VRSQRT` takes 13 cycles; reading `Q` before `VWAITQ` reads the *previous* `Q`. `Q` ops also clamp to `+-0x7F7FFFFF` (`[INFERRED]`).
- **Our code**: Macro-mode writes `ctx->vu0_q = ps2x_vu0_div/sqrt/rsqrt(...)` immediately and emits `VWAITQ` as a comment (`[CODE vu_translation_helpers.cpp:78, 85, 95]`, `[CODE vu_translator.cpp:218]`). **Could not verify** the bodies of `ps2x_vu0_div`, `ps2x_vu0_sqrt`, `ps2x_vu0_rsqrt`, `ps2x_vu0_flags` (declared `extern "C"` in `[CODE ee_gfx_decomp.cpp:22-25]`; definitions not found in `PS2Recomp/ps2xRuntime`). Meanwhile, `PS2_VDIV`, `PS2_VMULQ`, `PS2_VSQRT`, `PS2_VRSQRT` in `ps2_runtime_macros.h:384-385, 1088-1089` use raw `_mm_div_ps`, `_mm_mul_ps`, `sqrtf`, `1.0f / sqrtf` without PS2 clamping/abs (`[CODE ps2_runtime_macros.h:384-385, 1088-1089]`).
- **Concrete input**: `VDIV` followed immediately by `VMULq` (reading old `Q`) before `VWAITQ` -> uses the new `Q` instead of the old `Q` (`[INFERRED]`).

### 2.7 `PS2_VADD` / `PS2_VSUB` / `PS2_VMUL` Clamping (`+-0x7FFFFFFF` vs `+-0x7F7FFFFF`) & Denormal Inputs (`ps2_runtime_macros.h:330-378`)
- **Real hardware (PCSX2 VU0)**: VU0 clamps overflow to `+-0x7F7FFFFF` (whereas EE FPU clamps to `+-0x7FFFFFFF`) and flushes denormal inputs to zero (`[INFERRED]`).
- **Our code**: `ps2_vadd`/`ps2_vsub`/`ps2_vmul` flush denormal *results* (`rexp == 0`) (`[CODE ps2_runtime_macros.h:361-362]`), but do **not** flush denormal *inputs*, and `ps2_vslow` delegates to `ps2_fadd_slow`/`ps2_fsub_slow`/`ps2_fmul_slow` which clamp to `+-0x7FFFFFFF` (`[CODE ps2_runtime_macros.h:167, 194, 330-351]`).
- **Concrete input**: `PS2_VADD(0x00400000, 0x00400000)` -> returns `0x00800000` instead of `0.0f`; `PS2_VMUL(0x7F000000, 16.0f)` -> returns `0x7FFFFFFF` instead of `0x7F7FFFFF` (`[INFERRED]`).

### 2.8 `VOPMULA` / `VOPMSUB` & `dest_mask == 0` (`vu_translation_helpers.cpp:391-407, 718-728`)
- **Real hardware**: `VOPMULA` writes `ACC.{x,y,z}` (not `w`), `VOPMSUB` computes `ACC - (fs.yzx * ft.zxy)`. When `dest_mask == 0`, no `VF` lane is written (`[INFERRED]`).
- **Our code**: `VOPMULA` and `VOPMSUB` use `PS2_VMUL` and `PS2_VSUB` (inheriting §2.7 denormal-input behavior) (`[CODE vu_translation_helpers.cpp:397-402, 723-726]`). When `dest_mask == 0`, `_mm_set_epi32(0,0,0,0)` leaves `ctx->vu0_vf[vfd]` untouched, which is safe for register contents (`[CODE vu_translation_helpers.cpp:208-209]`).
- **Concrete input**: Cross product where `fs.y = 0x00400000, ft.z = 2.0f` -> `mul_res` is non-zero (`[INFERRED]`).

---

## 3. Integer / MMI

### 3.1 `PMADDW` / `PMSUBW` / `PMULTW` / `PMADDUW` (`mmi_translation_helpers.cpp:304-361`)
- **Real hardware**:
  - `PMADDW`/`PMSUBW`/`PMULTW` perform **signed** 32x32->64 multiplications on even words (`rs[0]*rt[0]` and `rs[2]*rt[2]`—or word pairs per EE manual) into **two independent** 64-bit accumulators `(hi, lo)` and `(hi1, lo1)`, and write both 64-bit results into the 128-bit `rd` (`[INFERRED]`).
- **Our code**:
  - Uses `_mm_mul_epu32` (**unsigned** 32x32->64!) even for signed `PMADDW`, `PMSUBW`, and `PMULTW` (`[CODE mmi_translation_helpers.cpp:306-307, 321-322, 336-337]`).
  - Sums all 4 lane products into a **single** 64-bit `acc`, writes only `ctx->lo`/`ctx->hi` (ignoring `ctx->lo1`/`ctx->hi1`), and writes `SET_GPR_U64(ctx, rd, acc)` (upper 64 bits of `rd` untouched) (`[CODE mmi_translation_helpers.cpp:308-315, 323-330, 338-345, 353-360]`).
- **Concrete input**: `PMULTW rd, rs, rt` with `rs[0] = -1 (0xFFFFFFFF)`, `rt[0] = 2`, `rs[2] = 3, rt[2] = 4` -> produces unsigned `0x1FFFFFFFE + 12` in `lo/hi` instead of `-2` in `lo/hi` and `12` in `lo1/hi1` (`[INFERRED]`).

### 3.2 `PMADDH` / `PMSUBH` / `PMULTH` / `PHMADH` / `PHMSBH` (`mmi_translation_helpers.cpp:385-484`)
- **Real hardware**: `PMADDH`/`PMSUBH`/`PMULTH` accumulate 4 independent 32-bit products across `lo`, `hi`, `lo1`, `hi1` (each holding two 32-bit values in `[31:0]` and `[63:32]` or paired) and write all 128 bits of `rd` (`[INFERRED]`). `PHMADH`/`PHMSBH` perform full 16x16->32 signed multiply-add/sub per 32-bit word (`[INFERRED]`).
- **Our code**:
  - `PMADDH`/`PMSUBH`/`PMULTH` sum all 4 `_mm_madd_epi16` results into a **single** 64-bit `acc` (`lo`/`hi`) and call `SET_GPR_U64(ctx, rd, acc)`, ignoring `lo1`/`hi1` and upper 64 bits of `rd` (`[CODE mmi_translation_helpers.cpp:388-397, 423-432, 475-483]`).
  - `PHMADH`/`PHMSBH` use `_mm_mullo_epi16` and `_mm_add_epi16`/`_mm_sub_epi16` (16-bit wrapping, discarding bits 16..31 of each product!) and collapse all 4 words into one scalar `acc` (`[CODE mmi_translation_helpers.cpp:404-417, 438-451]`).
- **Concrete input**: `PHMADH` with `rs = [200, 200, ...], rt = [200, 200, ...]` -> `200*200 = 40000` overflows 16-bit `_mm_mullo_epi16` to `-25536` (`[INFERRED]`).

### 3.3 `PMULTUW` & `PMTHI` / `PMTLO` (`mmi_translation_helpers.cpp:529-539, 586-595`)
- **Real hardware**: `PMULTUW` updates both `(lo, hi)` (from word 0) and `(lo1, hi1)` (from word 2) (`[INFERRED]`). `PMTHI`/`PMTLO` write `hi`/`lo` from `rs[63:0]` and `hi1`/`lo1` from `rs[127:64]` (`[INFERRED]`).
- **Our code**: `PMULTUW` only updates `ctx->lo`/`ctx->hi` from `res0` (`[CODE mmi_translation_helpers.cpp:536]`). `PMTHI`/`PMTLO` only write `ctx->hi = GPR_U32(ctx, rs)` / `ctx->lo = GPR_U32(ctx, rs)`, dropping upper 32 bits and `hi1`/`lo1` (`[CODE mmi_translation_helpers.cpp:588, 594]`).
- **Concrete input**: `PMTHI rs` followed by `PMFHL.LW rd` -> `hi1` has stale value (`[INFERRED]`).

### 3.4 `PADDUH` / `PSUBUH` Missing Saturation (`mmi_translation_helpers.cpp:107-110`)
- **Real hardware**: `PADDUH` / `PSUBUH` saturate unsigned 16-bit lanes to `0xFFFF` / `0x0000` (`[INFERRED]`).
- **Our code**: Uses wrapping `_mm_add_epi16` / `_mm_sub_epi16` instead of `_mm_adds_epu16` / `_mm_subs_epu16` (`[CODE mmi_translation_helpers.cpp:108, 110]`). (`PADDSH`/`PSUBSH`/`PADDSB`/`PSUBSB`/`PADDUB`/`PSUBUB`/`PADDSW`/`PSUBSW` use saturating paths `[CODE mmi_translation_helpers.cpp:41-60, 113-116]`.)
- **Concrete input**: `PADDUH` with `0xFFFF + 1` -> wraps to `0x0000` instead of saturating to `0xFFFF` (`[INFERRED]`).

### 3.5 `PDIVBW` Missing `INT32_MIN / -1` Guard (`mmi_translation_helpers.cpp:487-511`)
- **Real hardware**: `INT32_MIN / -1` yields quotient `INT32_MIN` and remainder `0` without trapping (`[INFERRED]`).
- **Our code**: `DIV`, `DIV1`, `PDIVW` all guard `divisor == -1 && dividend == INT32_MIN` and `divisor == 0` (`[CODE special_translator.cpp:71-84]`, `[CODE mmi_translator.cpp:49-60]`, `[CODE mmi_translation_helpers.cpp:367-372]`). However, `PDIVBW` only checks `div != 0` and executes `rsWords[i] / div` directly, which traps (`SIGFPE`/x86 `#DE`) on `INT32_MIN / -1` (`[CODE mmi_translation_helpers.cpp:499-504]`).
- **Concrete input**: `PDIVBW` with `rs[0] = 0x80000000, rt[0] = -1` -> hardware exception/crash (`[INFERRED]`).

### 3.6 `PMFHL.SLW` (`ps2_runtime_macros.h:905-914`)
- **Real hardware**: `PMFHL.SLW` extracts signed 32-bit saturated words from `((hi << 32) | lo)` shifted right by 16 (`[INFERRED]`).
- **Our code**: `ps2_pmfhl_slw` casts `prod0 >> 16` and `prod0 >> 48` via `static_cast<int32_t>` without clamping to `[INT32_MIN, INT32_MAX]` (`[CODE ps2_runtime_macros.h:905-914]`).
- **Concrete input**: `prod0 = 0x0001000000000000LL` -> wraps instead of saturating to `0x7FFFFFFF` (`[INFERRED]`).

### 3.7 Lane Ordering (`PCPY*`, `PEXT*`, `PPAC*`), 128-bit Shifts, `QFSRV`, Second Pipe
- `PS2_PEXTLW`/`UW`/`LH`/`UH`/`LB`/`UB` (`ps2_runtime_macros.h:130-135`), `PS2_PPACW`/`H`/`B` (`L800-827`), `PS2_PCPYLD` (`L1082`), `translatePCPYUD` (`mmi_translation_helpers.cpp:553-558`), `translatePCPYH` (`L569-575`): lane orders place `rt` in low and `rs` in high (matching EE `PEXTL`/`PCPYLD` etc.).
- 128-bit shifts `PSLLH`/`PSRLH`/`PSRAH`/`PSLLW`/`PSRLW`/`PSRAW` (`mmi_translator.cpp:110-121`) and `PS2_PSLLVW`/`PSRLVW`/`PSRAVW` (`ps2_runtime_macros.h:837-882`) mask shift count by `0x1F` for word shifts.
- `QFSRV` (`mmi_translation_helpers.cpp:598-606`, `ps2_runtime_macros.h:1002-1081`): masks `ctx->sa & 0x7F` (`0..127`).
- Second pipe `MFHI1`/`MFLO1`/`MULT1`/`MULTU1`/`DIV1`/`DIVU1`/`MADD1`/`MADDU1` (`mmi_translator.cpp:28-99`): properly use `ctx->hi1`/`ctx->lo1` (note `MSUB1`/`MSUBU1` are not in the switch).

---

## 4. Compiler / Platform Risks

### 4.1 `/fp:fast` Enabled on `ps2xRuntime` & `ps2EntryRunner` (`PS2Recomp/ps2xRuntime/cmake/ReleaseMode.cmake:27`)
- `recomp_source` intentionally omits `/fp:fast` (`[CODE CMakeLists.txt:63-64]`), **but** `EnableFastReleaseMode` applies `/fp:fast` to `ps2xRuntime` and `ps2EntryRunner` (`[CODE ReleaseMode.cmake:13-33]`).
- Under `/fp:fast`, MSVC can assume no `NaN`/`Inf`, fold `isnan()` checks, reorder `a + b + c`, and contract `a * b + c` into FMA (`vfmadd`, single rounding). This directly affects `ee_gfx_decomp.cpp`, `vu0_fast.inc`, and any inline `ps2_f*`/`ps2_v*` helpers compiled inside `ps2xRuntime` (`[INFERRED]`).

### 4.2 `/arch:AVX2` FMA Contraction (`CMakeLists.txt:64`, `ReleaseMode.cmake:29`)
- Both `recomp_source` and `ps2xRuntime` compile with `/arch:AVX2` in Release (`[CODE CMakeLists.txt:64]`, `[CODE ReleaseMode.cmake:29]`). On Clang/GCC (`-ffp-contract=on` default) or MSVC `/fp:fast`, inlined `PS2_VMUL` + `PS2_VADD` or `FPU_MUL_S` + `FPU_ADD_S` could contract to FMA (`[INFERRED]`). (`vu0_fast.inc:1292` explicitly notes avoiding FMA to match double-precision `mul` then `add/sub`.)

### 4.3 MXCSR Rounding Mode / FTZ / DAZ Not Set Globally (`ps2_runtime.cpp`, `main.cpp`)
- No `_MM_SET_FLUSH_ZERO_MODE`, `_MM_SET_DENORMALS_ZERO_MODE`, or `fesetround` calls were found in `ps2_runtime.cpp` or `main.cpp` (`[CODE ps2_runtime.cpp]`).
- Thus host MXCSR defaults to round-to-nearest-even (`RC=00`), FTZ=0, DAZ=0 for EE FPU and VU0 macro-mode, meaning denormal operands are not flushed to 0 in hardware SSE ops, and `vu0_fast.inc:1340` assumes `MXCSR RC=11b` (`[CODE vu0_fast.inc:1340]`).

### 4.4 Host `libm` & x87 vs SSE
- `PS2_VSQRT`/`PS2_VRSQRT` (`ps2_runtime_macros.h:1088-1089`) and `FPU_CEIL_W_S`/`FPU_FLOOR_W_S` (`L977-978`) call host `sqrtf`/`ceilf`/`floorf`, which return `NaN` on negative/exp-255 inputs (`[CODE ps2_runtime_macros.h:977-978, 1088-1089]`).
- On x86-64 Windows/Linux ABI, scalar FP uses SSE (`xmm`), not x87 (`vu0_fast.inc:1242` asserts `sizeof(long double) == sizeof(double)` on MSVC), avoiding 80-bit x87 excess-precision drift (`[INFERRED]`).

### 4.5 Unverified Items
- Bodies of `ps2x_vu0_div`, `ps2x_vu0_sqrt`, `ps2x_vu0_rsqrt`, `ps2x_vu0_flags` (declared `extern "C"` in `ee_gfx_decomp.cpp:22-25`, not found in `PS2Recomp/ps2xRuntime`).
- Whether `tools/build_clang_recomp.bat` (referenced in `CMakeLists.txt:37`) passes `-ffp-contract=fast` or `-ffast-math`.
- Generated `recomp_source/*.cpp` files were not scanned for post-generation patches.

---

## Top 10 Suspects for Physics / Skinning Instability

| Rank | Suspect | Area | Likelihood | Effort | How to test |
|---|---|---|---|---|---|
| 1 | `VFTOI*` missing saturation & `VF0` write-guard (`vu_translation_helpers.cpp:747-763`) | VU0 | High | Low | Unit test `VFTOI0` with `1e20f` (expect `0x7FFFFFFF`, not `0x80000000`) and `rt=0` |
| 2 | `VF0` write-guard missing in `VADD`/`VMUL`/`VMADD`/etc. (`vu_translation_helpers.cpp:11-525`) | VU0 | High | Low | Grep `recomp_source/` for `vu0_vf[0] =` (outside init); assert `vf0 == {0,0,0,1}` |
| 3 | `PMADDW`/`PMULTW` unsigned `_mm_mul_epu32` + collapsed single `acc` (`mmi_translation_helpers.cpp:304-361`) | MMI | High | Medium | Test negative `int32` inputs and check `lo1`/`hi1` + 128-bit `rd` against PCSX2 |
| 4 | `PMADDH`/`PHMADH`/`PMULTH` collapsed single `acc` & 16-bit wrap (`mmi_translation_helpers.cpp:385-484`) | MMI | High | Medium | Test 8x `int16` dot-product with products > 32767 and verify 4x 32-bit lanes |
| 5 | `/fp:fast` on `ps2xRuntime` (`ReleaseMode.cmake:27`) | Platform | Medium | Low | Build `ps2xRuntime` with `/fp:precise` and A/B test rope/mesh physics |
| 6 | `VMAX`/`VMINI` & `FPU_MAX_S`/`MIN_S` fail on exp-255 / `-0.0` (`vu_translation_helpers.cpp:236-272`, `fpu_translator.cpp:96-99`) | VU0 / FPU | Medium | Low | Test `0x7F800001` vs `1.0f` and `-0.0f` vs `+0.0f` |
| 7 | `VCLIPw` fails on exp-255 (`vu_translator.cpp:264-282`) | VU0 | Medium | Low | Test `VCLIPw` with `fs.x = 0x7F800001`, `ft.w = 1.0f` |
| 8 | Macro-mode VU0 ops never update `MAC`/`Status` flags (`vu_translation_helpers.cpp:11-728`) | VU0 | Medium | Medium | Grep `recomp_source/` for `vu0_mac_flags` / `vu0_status` reads after macro ops |
| 9 | Denormal inputs not flushed in `ps2_f*`/`ps2_v*` fast paths (`ps2_runtime_macros.h:286-302, 355-378`) | FPU / VU0 | Low-Med | Low | Enable MXCSR `DAZ`+`FTZ` or test `0x00400000 + 0x00400000` |
| 10 | `VDIV`/`VSQRT`/`VRSQRT` immediate `Q` write & `VWAITQ` no-op (`vu_translation_helpers.cpp:71-96`) | VU0 | Low-Med | Medium | Scan `recomp_source/` for `Q` reads between `VDIV`/`VRSQRT` and `VWAITQ` |
