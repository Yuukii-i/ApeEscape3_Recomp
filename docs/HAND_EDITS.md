# Ape Escape 3 (`SCUS_975.01`) Recompiler Hand-Edit Inventory & Migration Plan

> **Status Tag Legend**:
> - `[CONFIRMED file:line]` / `[CONFIRMED log:line]`: Verified directly against source files, binary headers, git history, or execution logs.
> - `[INFERRED: reason]`: Logical deduction from confirmed code or data structures.
> - `[UNKNOWN]`: Not yet determined from code or logs.

---

## 1. Executive Summary & Purpose

During early bootstrap and milestone progress on the Ape Escape 3 static recompiler project, several files in `recomp_source/` and the nested `PS2Recomp/` engine were manually edited to add diagnostic logging, bypass unknown hardware stalls, or fix recompiler emitter gaps.

However, editing files inside `recomp_source/` makes the recompiler output **non-reproducible**: any future run of `ps2_recomp.exe` will unconditionally overwrite `recomp_source/` and erase all manual edits.

This document provides a complete hunk-by-hunk inventory of:
1. Every modification captured in [`recomp_hand_edits.patch`](file:///c:/ApeEscape3_Recomp/recomp_hand_edits.patch) (18 files).
2. The current state of those files in [`recomp_source/`](file:///c:/ApeEscape3_Recomp/recomp_source).
3. The uncommitted modifications in the nested [`PS2Recomp/`](file:///c:/ApeEscape3_Recomp/PS2Recomp) repository (6 files).
4. Concrete disposition for every hunk: whether it is still needed, and where it must permanently live (runtime override, translator fix, or deletion).

---

## 2. Inventory of Hand Edits in `recomp_hand_edits.patch` & `recomp_source/`

### 2.1 Category A: Early Boot & `crt0` Diagnostic Logging

#### 1. `sub_00100134_0x100134.cpp` (Entry Point / `crt0`)
- **Hunk 1 (`@@ -6,17 +6,37 @@`)**:
  - **Lines Added**: `#include "trace_logger.h"`, `static bool has_booted = false;`, `fprintf(stderr, "[crt0] entry #%d (sub_00100134)\n", ++s_crt0_entry_count);`, and flight-recorder dump trigger if `has_booted` is true.
  - **Purpose**: Detect whether `crt0` was being re-entered infinitely (the original "restart loop" investigation).
  - **Still Needed?**: **NO** `[CONFIRMED NOTES.md:21, logs/baseline.log:21]`.
    - The restart loop was caused by `-Wl,--allow-multiple-definition` discarding the recompiled function table, which was resolved by defining `PS2X_HAS_RECOMPILED_GAME=1` in [`CMakeLists.txt:71`](file:///c:/ApeEscape3_Recomp/CMakeLists.txt#L71). `crt0` only executes once (`entry #1`).
  - **Destination**: **DELETE**. If entry logging is desired, it belongs in [`PS2Runtime::loadELF`](file:///c:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp) before invoking the guest entry point.
- **Hunk 2 (`@@ -89,5 +109,8 @@`)**:
  - **Lines Added**: `has_booted = true; push_trace("crt0: leaving 0x100134 -> 0x100190");`.
  - **Purpose**: Record flight recorder milestone leaving entry function.
  - **Still Needed?**: **NO**.
  - **Destination**: **DELETE**.

#### 2. `sub_00100190_0x100190.cpp` (`crt0` Phase 2)
- **Hunk 1 (`@@ -11,9 +11,13 @@`)**:
  - **Lines Added**: `fprintf(stderr, "[crt0] start sub_00100190\n"); fflush(stderr);`.
  - **Purpose**: Trace progression through `crt0` jump blocks.
  - **Still Needed?**: **NO**.
  - **Destination**: **DELETE**.

#### 3. `sub_00100210_0x100210.cpp` (`crt0` Startup & Syscall Dispatch)
- **Hunks 1–9 (`@@ -11,9 +11,13 @@`, `@@ -236,6 +240,8 @@`, `@@ -294,6 +300,8 @@`, `@@ -340,6 +348,8 @@`, `@@ -405,8 +415,12 @@`, `@@ -434,8 +448,12 @@`, `@@ -450,6 +468,7 @@`, `@@ -517,6 +536,7 @@`, `@@ -572,6 +592,9 @@`)**:
  - **Lines Added**: Milestones printing after `.bss` clear loops, before/after `syscall 0x3C` (`SetupThread`), before/after `syscall 0x3D` (`SetupHeap`), after `FlushCache`, after constructors, and right before `jal main` (`0x10036C`).
  - **Purpose**: Debugging stack and heap initialization parameters.
  - **Still Needed?**: **NO** `[CONFIRMED PS2Recomp/ps2xRuntime/src/lib/Kernel/Stubs/System.cpp:250-380]`.
    - `SetupThread` and `SetupHeap` are already logged cleanly with parameter dumps directly in `System.cpp:276, 350`.
  - **Destination**: **DELETE**.

---

### 2.2 Category B: Main Loop & Subsystem Tracing (`push_trace`)

#### 4. `sub_001037E8_0x1037e8.cpp` (`main` Function)
- **Hunks 1–10 (`@@ -6,17 +6,24 @@` through `@@ -635,6 +650,7 @@`)**:
  - **Lines Added**: `fprintf(stderr, "[main] first line of main (sub_001037E8)\n");` placed above `switch (ctx->pc)` and multiple `push_trace` calls across inner subsystem calls.
  - **Purpose**: Track execution progress inside the game's top-level loop.
  - **Still Needed?**: **NO (Actively harmful)** `[CONFIRMED NOTES.md:33, logs/baseline.log:688]`.
    - Because the print was placed above `switch (ctx->pc)`, every time a function inside `main` yields and resumes via `EeScheduler`, the message prints again, generating thousands of redundant log lines.
  - **Destination**: **DELETE**.

#### 5. Subsystem Helper Tracing Functions
- **`sub_00101298_0x101298.cpp`**: `push_trace("func_101298");`
- **`sub_00159728_0x159728.cpp`**: `push_trace("func_159728 (path parse)");`
- **`sub_0015993C_0x15993c.cpp`**: `push_trace("func_15993C");`
- **`sub_00159AAC_0x159aac.cpp`**: `push_trace("func_159AAC");`
- **`sub_00159B68_0x159b68.cpp`**: `push_trace("func_159B68 (boot medium check)");`
- **`sub_00159BEC_0x159bec.cpp`**: `push_trace("func_159BEC (language init)");`
- **`sub_0015B720_0x15b720.cpp`**: `push_trace("func_15B720 (system init)");`
- **Purpose**: Trace function call sequence during early game loop initialization.
- **Still Needed?**: **NO**.
- **Destination**: **DELETE**.

#### 6. `trace_logger.cpp` & `trace_logger.h`
- **Lines Added**: 39-line circular memory buffer (`g_trace_buffer[1024][128]`) and 17-line C header.
- **Purpose**: Temporary in-memory circular trace buffer.
- **Still Needed?**: **NO**.
- **Destination**: **DELETE**. If runtime tracing is desired, it belongs in `ps2_log.h` or `EeScheduler` under an env flag.

---

### 2.3 Category C: Hardcoded Return-0 Stubs (Already Migrated to Runtime!)

#### 7. `sub_003703D4_0x3703d4.cpp` (Sound Group 2 Readiness Check)
- **Hunk (`@@ -17,104 +18,14 @@`)**:
  - In `recomp_hand_edits.patch`, 100 lines of original MIPS instruction logic were stripped and replaced with `SET_GPR_S32(ctx, 2, 0); return;`.
  - **Current Status in `recomp_source/`**: **ALREADY RESTORED** to clean recompiled code `[CONFIRMED recomp_source/sub_003703D4_0x3703d4.cpp:1-85]`.
  - **Where it lives now**: Handled cleanly at runtime in [`ps2_runtime.cpp:1141-1145`](file:///c:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp#L1141-L1145) via:
    ```cpp
    runtime.replaceFunction(0x3703D4u, [](uint8_t *, R5900Context *ctx, PS2Runtime *) {
        ctx->r[2].d[0] = 0;
    });
    ```
  - **Still Needed in `recomp_source/`?**: **NO**.

#### 8. `sub_0040F968_0x40f968.cpp` / `0x40FAE0` (SCE IPU Idle Check)
- **Hunk (`@@ -520,9 +521,10 @@`)**:
  - In `recomp_hand_edits.patch`, `label_40fae0` was forced to return `0`.
  - **Current Status in `recomp_source/`**: **ALREADY RESTORED** to clean recompiled code.
  - **Where it lives now**: Handled cleanly at runtime in [`ps2_runtime.cpp:1146-1147`](file:///c:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp#L1146-L1147) via:
    ```cpp
    runtime.replaceFunction(0x40FAE0u, [](uint8_t *, R5900Context *ctx, PS2Runtime *) {
        setReturnS32(ctx, 0);
    });
    ```
  - **Still Needed in `recomp_source/`?**: **NO**.

#### 9. `sub_0040FC48_0x40fc48.cpp` (`_sceMpegWaitIpuIdle64`), `sub_0040FFD8_0x40ffd8.cpp` (`_waitIpuIdle`), `sub_00412108_0x412108.cpp` (`_waitIpuIdle`)
- **Hunks**: Stripped recompiled logic and forced `setReturnS32(ctx, 0);`.
- **Current Status in `recomp_source/`**: **ALREADY RESTORED** to clean recompiled code.
- **Where it lives now**: Handled in [`IPU.cpp`](file:///c:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/Kernel/Stubs/IPU.cpp) and [`MPEG.cpp`](file:///c:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/Kernel/Stubs/MPEG.cpp) HLE implementations, with `IPU_CTRL` (`0x10002010`) returning idle `0x40000000`.
- **Still Needed in `recomp_source/`?**: **NO**.

---

## 3. Inventory of Uncommitted Working-Tree Edits in `PS2Recomp/`

The nested repository [`PS2Recomp/`](file:///c:/ApeEscape3_Recomp/PS2Recomp) has 6 modified working-tree files:

| File | Exact Hunk | Purpose & Rationale | Permanent Location & Status |
| :--- | :--- | :--- | :--- |
| [`ps2xRuntime/src/lib/Kernel/Stubs/GS.cpp`](file:///c:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/Kernel/Stubs/GS.cpp#L1222) | `+ runtime->drainCompletedDmacHandlers(rdram);` in `sceGsSyncPath` | Drains pending INTC/DMAC interrupt handlers when synchronization points are reached, preventing interrupt stalls | **PERMANENT RUNTIME FIX**. Commit to `PS2Recomp` fork. |
| [`ps2xRuntime/src/lib/Kernel/Stubs/IPU.cpp`](file:///c:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/Kernel/Stubs/IPU.cpp#L9-L44) | Removed hardcoded addresses (`IQVAL_BASE 0x1721e0`, `VQVAL_BASE 0x172230`, `SETD4_CHCR_ENTRY 0x126428`) from other games (Jak/Katamari) | Cleans up incorrect cross-game residue that clobbered memory on Ape Escape 3 | **PERMANENT HLE FIX**. Commit to `PS2Recomp` fork. |
| [`ps2xRuntime/src/lib/Kernel/Stubs/MPEG.cpp`](file:///c:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/Kernel/Stubs/MPEG.cpp#L15-L60) | Removed cross-game hardcoded hooks (`0x170b00`, `0x16b0d0`) | Prevents dispatching to unaligned addresses or foreign game routines | **PERMANENT HLE FIX**. Commit to `PS2Recomp` fork. |
| [`ps2xRuntime/src/lib/ps2_memory.cpp`](file:///c:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/ps2_memory.cpp#L125-L165) | Added `readIORegister` and `writeIORegister` cases for `0x10003C30` (`VIF1_MARK`) | Emulates hardware VIF1 MARK register read/write operations | **PERMANENT HARDWARE MMIO FIX**. Commit to `PS2Recomp` fork. |
| [`ps2xRuntime/src/lib/ps2_runtime.cpp`](file:///c:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp#L2740-L2810) | Added INTC cause 5 queueing/draining and `PS2X_DUMP_FRAMES` diagnostic frame dump | Connects VIF1 interrupt notifications to the guest interrupt handler table and captures rendered frame PNGs | **PERMANENT RUNTIME FEATURE**. Commit to `PS2Recomp` fork. |
| [`ps2xRuntime/src/lib/ps2_vif1_interpreter.cpp`](file:///c:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/ps2_vif1_interpreter.cpp#L180-L195) | Trigger INTC cause 5 interrupt when `VIF1_MARK == 0x2000` | Unblocks the game's end-of-frame wait loop in `sub_00284534` without memory poking | **PERMANENT CORE INTERPRETER FIX**. Commit to `PS2Recomp` fork. |

---

## 4. Regeneration Impact Assessment

If `recomp_source/` is regenerated today using `ps2_recomp.exe config.toml`:
1. **Zero functional regression**:
   - Stubs for `0x3703D4`, `0x40FAE0`, `0x428F50`, and `0x42F2D0` are registered dynamically via `runtime.replaceFunction` at runtime in `ps2_runtime.cpp`.
   - Missing stubs from `config.toml` are registered via `registerConfigStubs` in `ps2_runtime.cpp`.
   - IPU / MPEG stubs are handled by HLE in `IPU.cpp` and `MPEG.cpp`.
2. **Loss of debug noise only**:
   - The redundant `[crt0]` and `[main]` console prints will disappear.
   - The obsolete `push_trace` calls and `trace_logger.cpp` will be cleaned up.
3. **Conclusion**:
   - `recomp_source/` can be safely regenerated once a clean baseline is confirmed via `scripts/regen_dryrun.ps1`.
