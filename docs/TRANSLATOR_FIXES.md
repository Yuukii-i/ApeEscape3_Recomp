# R5900 & VU0 Translator Fixes Audit & Verification Report

## Executive Summary

This report documents the verification, fix implementation, and differential verification of three critical code generation bugs in `ps2xRecomp`:
1. **GPR Branch 64-bit Condition Test**: `BLEZ`, `BGTZ`, `BLTZ`, `BGEZ` (and their `-L` branch-likely variants) tested signed 32-bit `GPR_S32(ctx, rs)` instead of full 64-bit signed integer `GPR_S64(ctx, rs)`.
2. **Conditional Moves Semantics (`MOVZ` / `MOVN`)**: `MOVZ` and `MOVN` previously emitted `SET_GPR_VEC(ctx, rd, GPR_VEC(ctx, rs))`, overwriting the entire 128-bit register rather than updating only bits 0..63 (`SET_GPR_U64(ctx, rd, GPR_U64(ctx, rs))`) as specified by MIPS IV and R5900 architecture.
3. **VU0 Macro Memory Addressing & Register Protection**: VU0 macro load/store instructions (`VLQI`, `VSQI`, `VLQD`, `VSQD`, `VILWR`, `VISWR`) addressed low RDRAM (`0x00000000..0x00003FFC`) instead of VU0 data memory (`0x11004000..0x11004FFC`), and constant registers `$vf0` (hardwired to `(0,0,0,1)`) and `$vi0` (hardwired to `0`) were not write-protected against post-increment/pre-decrement and load destination writes.

Every diff between the baseline compilation output (`build/regen_before`) and post-fix compilation output (`build/regen_after`) across all 23,350 files was categorized and validated. Zero unexpected differences occurred.

---

## 1. Bug Verification & Root Cause Analysis

### Bug 1: 32-bit Truncation in R5900 Conditional Branches
- **File**: [`PS2Recomp/ps2xRecomp/src/lib/control_flow_emitter.cpp`](file:///c:/ApeEscape3_Recomp/PS2Recomp/ps2xRecomp/src/lib/control_flow_emitter.cpp#L407-L425)
- **Specification**: In MIPS IV and the Sony Toshiba EE R5900 Core manual, `BLEZ`, `BGTZ`, `BLTZ`, and `BGEZ` evaluate the sign of the full 64-bit GPR value:
  - `BLEZ`: `GPR[rs] <= 0` (signed 64-bit comparison)
  - `BGTZ`: `GPR[rs] > 0` (signed 64-bit comparison)
  - `BLTZ`: `GPR[rs] < 0` (signed 64-bit comparison)
  - `BGEZ`: `GPR[rs] >= 0` (signed 64-bit comparison)
- **Defect**: The emitter called `GPR_S32(ctx, rs)`, casting the register to `int32_t` and dropping bits 32..63. If a 64-bit value had sign bit 0 in bit 31 but was negative in bit 63 (or vice versa), the branch decision was evaluated incorrectly.
- **Fix**: Replaced `GPR_S32(ctx, ...)` with `GPR_S64(ctx, ...)`.

### Bug 2: 128-bit Overwrite on Conditional Moves (`MOVZ` / `MOVN`)
- **File**: [`PS2Recomp/ps2xRecomp/src/lib/special_translator.cpp`](file:///c:/ApeEscape3_Recomp/PS2Recomp/ps2xRecomp/src/lib/special_translator.cpp#L123-L126)
- **Specification**: Per EE Core Architecture Manual section 3.2 ("GPR Architecture and Instruction Set"), MIPS IV integer instructions operate on the lower 64 bits of GPRs. `MOVZ` and `MOVN` conditionally copy bits 0..63 from `rs` into `rd`, leaving bits 64..127 of `rd` unchanged.
- **Defect**: The emitter previously emitted:
  ```cpp
  if (GPR_U64(ctx, rt) == 0) SET_GPR_VEC(ctx, rd, GPR_VEC(ctx, rs));
  ```
  `SET_GPR_VEC` overwrites the entire 128-bit vector register `ctx->r[rd]`, corrupting upper SIMD/MMI data when integer code conditionally moves values into registers used elsewhere for 128-bit operations.
- **Fix**: Replaced `SET_GPR_VEC` / `GPR_VEC` with `SET_GPR_U64` / `GPR_U64`:
  ```cpp
  if (GPR_U64(ctx, rt) == 0) SET_GPR_U64(ctx, rd, GPR_U64(ctx, rs));
  ```

### Bug 3: VU0 Macro Memory Base & Register Write-Protection
- **File**: [`PS2Recomp/ps2xRecomp/src/lib/vu_translation_helpers.cpp`](file:///c:/ApeEscape3_Recomp/PS2Recomp/ps2xRecomp/src/lib/vu_translation_helpers.cpp#L114-L125) and lines 770-835.
- **Specification**:
  - VU0 Data Memory resides at physical base `0x11004000` with size `4 KB` (0x1000 bytes, 256 quadwords / 1024 words) `[CONFIRMED PS2Recomp/ps2xRuntime/include/runtime/ps2_memory.h:38-40]`.
  - VU0 Macro memory operations index VU0 memory, not RDRAM.
  - Constant register `$vi0` is hardwired to 0. Post-increment (`VLQI`/`VSQI`) and pre-decrement (`VLQD`/`VSQD`) on `$vi0` must not alter `$vi0`. Load destination (`VILWR`) into `$vi0` must not modify `$vi0`.
  - Constant vector register `$vf0` is hardwired to `(0.0f, 0.0f, 0.0f, 1.0f)`. Vector loads (`VLQI`/`VLQD`) into `$vf0` must not modify `$vf0`.
- **Defect**:
  - The translator emitted addresses with base `0x00000000`, causing VU0 loads and stores to read and corrupt low RDRAM memory (`0x00000000..0x00003FFC`).
  - Quadword indexing used mask `0x3FF` (16 KB, VU1 size) instead of `0xFF` (4 KB, VU0 size).
  - Writing to `$vi0` was executed whenever `vis == 0` (corrupting `$vi0` from 0 to 1 on `vlqi.xyzw $vf16, ($vi0++)`).
- **Fix**:
  - `VILWR`/`VISWR`: Base `0x11004000u | (((uint32_t)ctx->vi[vis] << 2) & 0xFFCu)`. Write-protect `$vi0` when `inst.rt == 0`.
  - `VLQI`/`VSQI`/`VLQD`/`VSQD`: Base `0x11004000u | (((uint32_t)(ctx->vi[vis] & 0xFF)) << 4)`. Write-protect `$vi0` when `vis == 0`. Write-protect `$vf0` when `inst.rt == 0`.

---

## 2. Verification Methodology & Build Statistics

1. **Baseline Generation (`build/regen_before`)**:
   - Built with unmodified `ps2_recomp.exe` targeting `build/temp_config_before.toml` (`output = "build/regen_before"`).
   - Generated 23,348 function `.cpp` files and `ps2_recompiled_functions.h` from `SCUS_975.01`.
2. **Recompiler Standalone Rebuild**:
   - Configured `PS2Recomp/build` with Ninja (`-DPS2X_BUILD_RECOMP=ON`).
   - Recompiled `ps2_recomp.exe` in 4.2 seconds after editing the 3 translator files.
3. **Post-Fix Generation (`build/regen_after`)**:
   - Ran newly built `ps2_recomp.exe` targeting `build/temp_config_after.toml` (`output = "build/regen_after"`).
   - Generated identical 23,348 function `.cpp` files and `ps2_recompiled_functions.h`.
4. **Differential Analysis Script (`build/diff_stats.py`)**:
   - Compared all 23,350 files line by line using Python unified diff.

### Summary Statistics
| Metric | Value |
|---|---|
| Total Files Compared | 23,350 |
| Identical Files | 20,383 |
| Total Files Changed | 2,967 |
| **Bug 1 Changes (Branch `GPR_S64`)** | **2,227 files** |
| **Bug 2 Changes (`MOVZ`/`MOVN` `SET_GPR_U64`)** | **1,085 files** |
| **Bug 3 Changes (VU0 Memory `0x11004000` & Reg Protect)** | **1 file** (`sub_003BA2A0_0x3ba2a0.cpp`) |
| **Other Unexpected Differences** | **0 files** |

*(Note: Some files contain both branch and MOVZ/MOVN instructions, hence sum of bug counts exceeds total changed files).*

---

## 3. Sample Diffs per Bug

### Bug 1 Samples: 64-bit Branch Condition (`GPR_S64`)

#### Sample 1.1: `entry_43ac38_0x43ad78.cpp`
```diff
@@ -356,5 +356,5 @@
     ctx->pc = 0x43AD38u;
     {
-        const bool branch_taken_0x43ad38 = (GPR_S32(ctx, 2) >= 0);
+        const bool branch_taken_0x43ad38 = (GPR_S64(ctx, 2) >= 0);
         ctx->pc = 0x43AD3Cu;
         ctx->in_delay_slot = true;
```

#### Sample 1.2: `entry_43ad78_0x43ae68.cpp`
```diff
@@ -245,5 +245,5 @@
     ctx->pc = 0x43AE2Cu;
     {
-        const bool branch_taken_0x43ae2c = (GPR_S32(ctx, 2) >= 0);
+        const bool branch_taken_0x43ae2c = (GPR_S64(ctx, 2) >= 0);
         ctx->pc = 0x43AE30u;
         ctx->in_delay_slot = true;
```

#### Sample 1.3: `entry_43e6b0_0x43e8b8.cpp`
```diff
@@ -85,5 +85,5 @@
     ctx->pc = 0x43E6E8u;
     {
-        const bool branch_taken_0x43e6e8 = (GPR_S32(ctx, 2) < 0);
+        const bool branch_taken_0x43e6e8 = (GPR_S64(ctx, 2) < 0);
         ctx->pc = 0x43E6ECu;
         ctx->in_delay_slot = true;
@@ -510,5 +510,5 @@
     ctx->pc = 0x43E874u;
     {
-        const bool branch_taken_0x43e874 = (GPR_S32(ctx, 2) >= 0);
+        const bool branch_taken_0x43e874 = (GPR_S64(ctx, 2) >= 0);
         if (branch_taken_0x43e874) {
             ctx->pc = 0x43E878u;
```

#### Sample 1.4: `entry_43e8b8_0x43e948.cpp`
```diff
@@ -58,5 +58,5 @@
     ctx->pc = 0x43E8D0u;
     {
-        const bool branch_taken_0x43e8d0 = (GPR_S32(ctx, 2) < 0);
+        const bool branch_taken_0x43e8d0 = (GPR_S64(ctx, 2) < 0);
         ctx->pc = 0x43E8D4u;
         ctx->in_delay_slot = true;
```

#### Sample 1.5: `entry_43e948_0x43e9e8.cpp`
```diff
@@ -56,5 +56,5 @@
     ctx->pc = 0x43E95Cu;
     {
-        const bool branch_taken_0x43e95c = (GPR_S32(ctx, 2) < 0);
+        const bool branch_taken_0x43e95c = (GPR_S64(ctx, 2) < 0);
         ctx->pc = 0x43E960u;
         ctx->in_delay_slot = true;
```

---

### Bug 2 Samples: 64-bit Integer Moves (`MOVZ` / `MOVN`)

#### Sample 2.1: `sub_00100518_0x100518.cpp`
```diff
@@ -32,5 +32,5 @@
     // 0x100524: 0xf200a  movz        $a0, $zero, $t7
     ctx->pc = 0x100524u;
-    if (GPR_U64(ctx, 15) == 0) SET_GPR_VEC(ctx, 4, GPR_VEC(ctx, 0));
+    if (GPR_U64(ctx, 15) == 0) SET_GPR_U64(ctx, 4, GPR_U64(ctx, 0));
     // 0x100528: 0x3e00008  jr          $ra
     ctx->pc = 0x100528u;
```

#### Sample 2.2: `sub_001005A4_0x1005a4.cpp`
```diff
@@ -94,5 +94,5 @@
         ctx->branch_pc = 0x1005D0u;
         // 0x1005d4: 0x1cf100a  movz        $v0, $t6, $t7 (Delay Slot)
-        if (GPR_U64(ctx, 15) == 0) SET_GPR_VEC(ctx, 2, GPR_VEC(ctx, 14));
+        if (GPR_U64(ctx, 15) == 0) SET_GPR_U64(ctx, 2, GPR_U64(ctx, 14));
         ctx->in_delay_slot = false;
         ctx->pc = jumpTarget;
```

#### Sample 2.3: `sub_00100600_0x100600.cpp`
```diff
@@ -82,5 +82,5 @@
         ctx->branch_pc = 0x100630u;
         // 0x100634: 0x1af100a  movz        $v0, $t5, $t7 (Delay Slot)
-        if (GPR_U64(ctx, 15) == 0) SET_GPR_VEC(ctx, 2, GPR_VEC(ctx, 13));
+        if (GPR_U64(ctx, 15) == 0) SET_GPR_U64(ctx, 2, GPR_U64(ctx, 13));
         ctx->in_delay_slot = false;
         if (branch_taken_0x100630) {
```

#### Sample 2.4: `sub_00100B24_0x100b24.cpp`
```diff
@@ -75,5 +75,5 @@
         ctx->branch_pc = 0x100B4Cu;
         // 0x100b50: 0xcf100b  movn        $v0, $a2, $t7 (Delay Slot)
-        if (GPR_U64(ctx, 15) != 0) SET_GPR_VEC(ctx, 2, GPR_VEC(ctx, 6));
+        if (GPR_U64(ctx, 15) != 0) SET_GPR_U64(ctx, 2, GPR_U64(ctx, 6));
         ctx->in_delay_slot = false;
         ctx->pc = jumpTarget;
```

#### Sample 2.5: `sub_00100B64_0x100b64.cpp`
```diff
@@ -97,5 +97,5 @@
     // 0x100ba4: 0xcf100a  movz        $v0, $a2, $t7
     ctx->pc = 0x100ba4u;
-    if (GPR_U64(ctx, 15) == 0) SET_GPR_VEC(ctx, 2, GPR_VEC(ctx, 6));
+    if (GPR_U64(ctx, 15) == 0) SET_GPR_U64(ctx, 2, GPR_U64(ctx, 6));
  label_100ba8:
     // 0x100ba8: 0x3e00008  jr          $ra
```

---

### Bug 3 Sample: VU0 Macro Memory Base & Register Protection

#### Sample 3.1: `sub_003BA2A0_0x3ba2a0.cpp`
```diff
@@ -318,5 +318,5 @@
     // 0x3ba3dc: 0x4be0837d  vsqi.xyzw   $vf16, ($vi0++)
     ctx->pc = 0x3ba3dcu;
-    { uint32_t addr = ((uint32_t)(ctx->vi[16] & 0x3FF)) << 4; __m128i old_val = READ128(addr); __m128 res = _mm_blendv_ps(_mm_castsi128_ps(old_val), ctx->vu0_vf[0], _mm_castsi128_ps(_mm_set_epi32(-1, -1, -1, -1))); WRITE128(addr, _mm_castps_si128(res)); ctx->vi[16] = (ctx->vi[16] + 1) & 0x3FF; }
+    { uint32_t addr = 0x11004000u | (((uint32_t)(ctx->vi[16] & 0xFF)) << 4); __m128i old_val = READ128(addr); __m128 res = _mm_blendv_ps(_mm_castsi128_ps(old_val), ctx->vu0_vf[0], _mm_castsi128_ps(_mm_set_epi32(-1, -1, -1, -1))); WRITE128(addr, _mm_castps_si128(res)); ctx->vi[16] = (ctx->vi[16] + 1) & 0x3FF; }
     // 0x3ba3e0: 0x8e2d0000  lw          $t5, 0x0($s1)
     ctx->pc = 0x3ba3e0u;
@@ -564,5 +564,5 @@
     // 0x3ba4f0: 0x4bf0037c  vlqi.xyzw   $vf16, ($vi0++)
     ctx->pc = 0x3ba4f0u;
-    { uint32_t addr = ((uint32_t)(ctx->vi[0] & 0x3FF)) << 4; __m128 res = _mm_castsi128_ps(READ128(addr)); __m128i mask = _mm_set_epi32(-1, -1, -1, -1); ctx->vu0_vf[16] = _mm_blendv_ps(ctx->vu0_vf[16], res, _mm_castsi128_ps(mask)); ctx->vi[0] = (ctx->vi[0] + 1) & 0x3FF; }
+    { uint32_t addr = 0x11004000u | (((uint32_t)(ctx->vi[0] & 0xFF)) << 4); __m128 res = _mm_castsi128_ps(READ128(addr)); __m128i mask = _mm_set_epi32(-1, -1, -1, -1); ctx->vu0_vf[16] = _mm_blendv_ps(ctx->vu0_vf[16], res, _mm_castsi128_ps(mask)); }
     // 0x3ba4f4: 0x2410ff80  addiu       $s0, $zero, -0x80
     ctx->pc = 0x3ba4f4u;
```

**Key Evidence in Sample 3.1**:
- At `0x3ba3dc`: `vsqi.xyzw $vf16, ($vi0++)` writes to `0x11004000u | (((uint32_t)(ctx->vi[16] & 0xFF)) << 4)` rather than low RDRAM `((ctx->vi[16] & 0x3FF)) << 4`.
- At `0x3ba4f0`: `vlqi.xyzw $vf16, ($vi0++)` reads from `0x11004000u` and **omits** `ctx->vi[0] = (ctx->vi[0] + 1) & 0x3FF;`, preserving `$vi0 == 0`.

---

## 4. Application to `recomp_source/` (Policy Note)

Per working guidelines:
- `recomp_source/` was NOT modified during this task.
- The regenerated post-fix code is stored in `build/regen_after/`.
- Applying the updated code to `recomp_source/` is a user decision. To apply it, copy files from `build/regen_after/` into `recomp_source/` or run `ps2_recomp.exe` with `output = "recomp_source"`.
