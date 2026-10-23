# Ape Escape 3 (`SCUS_975.01`) Guest Memory Map & Overlap Audit

> **Status Tag Legend**:
> - `[CONFIRMED file:line]` / `[CONFIRMED log:line]`: Verified directly against disassembly, source code, binary headers, or run logs.
> - `[INFERRED: reason]`: Logical deduction from confirmed code or data structures.
> - `[UNKNOWN]`: Not yet determined from code or logs.

---

## 1. Executive Summary & Audit Scope

This document provides a comprehensive, verified accounting of the guest memory layout of *Ape Escape 3* (`SCUS_975.01`) running under `ps2xRuntime`.
The audit cross-examines:
1. Static ELF headers (`PT_LOAD` segments, sections, and entry points).
2. Runtime initialization parameters (`SetupThread`, `SetupHeap`, `.bss` clearing).
3. Dynamic game allocators (custom heap pool at `sub_0036E05C` and 64-slot region allocator at `sub_0031A408`).
4. Overwritten / reused buffers (the 63-sector `DATA.BIN` VFI index loaded into `0x00120000`).
5. SIF RPC / DMA buffers (FCFD slots in `.bss`, CID1 asset destination buffers, and the async SIF callback stack pool).
6. Hardware-reserved ranges (kernel reserve and 16 KB EE scratchpad RAM).

### Core Findings
1. **Latent High-Severity Overlap**: `ps2xRuntime` reserves async SIF callback stacks in `[0x01F00000, 0x01FA0000]` (`ps2_runtime.cpp:1116-1118, 2388`). However, the game's custom heap allocator (`sub_0036E05C:60-99`) configures its dynamic heap pool to span `0x00783000 .. 0x01FA0000` (`25,284,608` bytes = `24.11 MB`). At early boot, active allocations (`REGN` + `HEAP` = `~21.9 MB`) reach `~0x01C657D8`, leaving `~2.6 MB` of headroom. If stage/asset loading exceeds `23.49 MB`, the game allocator will allocate memory inside `[0x01F00000, 0x01FA0000]`, colliding with the async SIF callback stack `[CONFIRMED recomp_source/sub_0036E05C_0x36e05c.cpp:80-99, PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp:1116-1118, 2388]`.
2. **Main Thread Stack Headroom**: The main EE thread stack (`0x01FA0000 .. 0x02000000`, 384 KB) has exceptional headroom. Across hundreds of frames through the main loop, the lowest observed stack pointer is `0x01FFF380` (stack depth `3,200` bytes; `380.88 KB` of unused headroom) `[CONFIRMED logs/step3_rebuild2_err.log, logs/step3_rebuild2_out.log]`.
3. **Safety of `0x00120000` Overwrite**: The 63-sector (`129,024` bytes) `DATA.BIN` VFI index loaded into `0x00120000..0x0013F7FF` intentionally reuses once-only startup code. Constructor `sub_0013B098` executes exactly once during `__do_global_ctors_aux` prior to the read. An exhaustive scan of all 23,349 recompiled C++ files confirmed **zero memory read instructions** targeting `0x00120000..0x0013F7FF`. Jump tables and constants reside in `.rodata` (`0x006B8000..0x0072C040`), not `.text` `[CONFIRMED SCUS_975.01, recomp_source/sub_00428AB8_0x428ab8.cpp:60-120, logs/baseline.log:28-41]`.

---

## 2. Unified Master Guest Memory Map

| Address Range (Guest) | Size (Bytes / Human) | Owner / Purpose | Allocation Mechanism & Initialization | Status & Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `0x00000000..0x000FFFFF` | `1,048,576 B` (`1 MB`) | PS2 Kernel Reserve / Hardware Exception Vectors | Hardware architected; guest user code starts at `0x00100000` | `[CONFIRMED SCUS_975.01]` |
| `0x00100000..0x00628257` | `5,407,320 B` (`5.16 MB`) | `[1] .text` (Executable MIPS machine code) | ELF `PT_LOAD` segment 0; entry point `0x00100134` (`crt0`) | `[CONFIRMED SCUS_975.01:PH0, SH1]` |
| `0x00120000..0x0013F7FF` | `129,024 B` (`63 sectors`) | **VFI Index Buffer** (Overwrites discarded `.text` startup routines) | Overwritten at runtime by `sceCdRead(3576, 63, 0x00120000)`. Sreg 26 sent to IOP as VFI base | `[CONFIRMED logs/baseline.log:38-49, PS2Recomp/ps2xRuntime/src/lib/Kernel/Stubs/CD.cpp:1228-1275]` |
| `0x00628260..0x0062E65F` | `25,600 B` (`25.0 KB`) | `[2] .vutext` (Embedded VU1 microprograms) | ELF `PT_LOAD` segment 0 | `[CONFIRMED SCUS_975.01:PH0, SH2]` |
| `0x0062E660..0x0062E8A3` | `580 B` (`0x244`) | `[3] .ctors` (Global static C++ constructors table) | ELF `PT_LOAD` segment 0; iterated by `sub_00428AB8` at boot | `[CONFIRMED SCUS_975.01:PH0, SH3, recomp_source/sub_00428AB8_0x428ab8.cpp:60-86]` |
| `0x0062E8A4..0x0062E957` | `180 B` (`0xB4`) | `[4] .dtors` (Global static C++ destructors table) | ELF `PT_LOAD` segment 0 | `[CONFIRMED SCUS_975.01:PH0, SH4]` |
| `0x0062E958..0x0062E96F` | `24 B` (`0x18`) | `[5] .reginfo` (MIPS runtime register info) | ELF `PT_LOAD` segment 0; specifies `$gp = 0x00734070` | `[CONFIRMED SCUS_975.01:PH0, SH5]` |
| `0x0062E980..0x006B7F8F` | `562,704 B` (`549.5 KB`) | `[6] .data` (Initialized writable global data) | ELF `PT_LOAD` segment 0 | `[CONFIRMED SCUS_975.01:PH0, SH6]` |
| `0x006B8000..0x0072C03F` | `475,200 B` (`464.1 KB`) | `[9] .rodata` (Constants, strings, C++ VTables, switch jump tables) | ELF `PT_LOAD` segment 0 | `[CONFIRMED SCUS_975.01:PH0, SH9]` |
| `0x0072C080..0x0072C5CF` | `1,360 B` (`1.3 KB`) | `[10] .sdata` (Small initialized data accessed via `$gp`) | ELF `PT_LOAD` segment 0 | `[CONFIRMED SCUS_975.01:PH0, SH10]` |
| `0x0072C600..0x0072D663` | `4,196 B` (`4.1 KB`) | `[11] .sbss` (Small uninitialized data accessed via `$gp`) | ELF `PT_LOAD` segment 0; zero-cleared by `sub_00100210:35-85` | `[CONFIRMED SCUS_975.01:PH0, SH11, recomp_source/sub_00100210_0x100210.cpp:35-85]` |
| `0x0072D680..0x0077290F` | `283,280 B` (`276.6 KB`) | `[12] .bss` (Global uninitialized data) | ELF `PT_LOAD` segment 0; zero-cleared by `sub_00100210:35-85` | `[CONFIRMED SCUS_975.01:PH0, SH12, recomp_source/sub_00100210_0x100210.cpp:35-85]` |
| `0x00771798..0x007718BB` | `304 B` (`0x130`) | `file3.irx` Instance 0 Table (includes 16 FCFD slots at `0x007717CC..0x007718BC`) | Statically allocated in `.bss`; registered by `sub_001DA880` | `[CONFIRMED recomp_source/sub_001DA880_0x1da880.cpp:175-210]` |
| `0x00771B88..0x00771CBB` | `304 B` (`0x130`) | `file3.irx` Instance 1 Table (includes 16 FCFD slots at `0x00771BBC..0x00771CBC`) | Statically allocated in `.bss`; registered by `sub_001DA880` | `[CONFIRMED recomp_source/sub_001DA880_0x1da880.cpp:175-210, logs/baseline.log:82-104]` |
| `0x00772910..0x0078290F` | `65,536 B` (`64 KB`) | Newlib / C Runtime Heap Pool | Initialized by `SetupHeap(0x00772910, 0x10000)` (`syscall 0x3D`) in `sub_00100210:115` | `[CONFIRMED recomp_source/sub_00100210_0x100210.cpp:115, PS2Recomp/ps2xRuntime/src/lib/Kernel/Stubs/System.cpp:336-380]` |
| `0x00782910..0x00782FFF` | `1,776 B` (`0x6F0`) | Alignment Gap / Safety Padding | Unused gap between Newlib heap end and 4KB page-aligned custom heap pool base | `[CONFIRMED recomp_source/sub_0036E05C_0x36e05c.cpp:28-50]` |
| `0x00783000..0x01FA0000` | `25,284,608 B` (`24.11 MB` = `0x0181D000`) | **Game Custom Dynamic Memory Pool** (Heap + Region Allocator + CID1 buffers) | Initialized by `sub_0036E05C` (`HeapBase = 0x00783000`, `HeapSize = 0x0181D000`). Sub-allocated by `sub_0036EDAC` | `[CONFIRMED recomp_source/sub_0036E05C_0x36e05c.cpp:28-99, recomp_source/sub_0036E22C_0x36e22c.cpp:197-290]` |
| `0x00783000..0x0078307F` | `128 B` (`0x80`) | Game Heap Pool Master Header | Initialized by `sub_0036E294` (`magic = 0x7531`) | `[CONFIRMED recomp_source/sub_0036E22C_0x36e22c.cpp:201-290]` |
| `0x00783080..0x007834BF` | `1,088 B` (`0x440`) | Region Allocator Control Table & 64 Descriptors | Allocated via `sub_0036EDAC` by `sub_0031A408:48-71` (stored at `0x00696FC0`); managed by thread `0x0031A3E8` | `[CONFIRMED recomp_source/sub_0031A408_0x31a408.cpp:48-85, recomp_source/sub_0010105C_0x10105c.cpp:28-98]` |
| `0x0079120C..0x00793D5B` | `~11 KB` | CID1 Stat Buffers (`debug/us/etc/font/*.apefnt`, `*.ttxbin`) | Dynamically allocated inside game heap pool; logged in `CID1:srcExtra` | `[CONFIRMED logs/step3_rebuild2_err.log:82-104]` |
| `0x00A0E480..0x00A114BF` | `~20 KB` | CID1 Font File Payload Buffers (`seurat_20x20.apefnt`, `limited_jis.apefnt`, etc.) | Dynamically allocated inside game heap pool; logged in `CID1:srcExtra` | `[CONFIRMED logs/step3_rebuild2_err.log:87, 96, 104]` |
| `0x010F1080..0x010F147F` | `1 KB` | CID1 Directory Buffers (`debug/us/static`, `debug/us/startup`) | Dynamically allocated inside game heap pool; logged in `CID1:srcExtra` | `[CONFIRMED logs/step3_rebuild2_err.log:309, 313]` |
| `0x018F5EC0..` | Dynamic | Primary Font Data Buffer (Observed in asset loader) | Dynamically allocated inside game heap pool | `[CONFIRMED NOTES.md:264, PLAN.md:30]` |
| `0x01F00000..0x01FA0000` | `655,360 B` (`640 KB`) | **ps2xRuntime Async SIF Callback Stack Pool** | Configured in `ps2_runtime.cpp:1116-1118`; sub-allocated downwards from `0x01FA0000` by `reserveAsyncCallbackStack` | `[CONFIRMED PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp:1116-1118, 2372-2413, logs/baseline.log:25]` |
| `0x01FA0000..0x02000000` | `393,216 B` (`384 KB` = `0x60000`) | **Main EE Thread Stack** | Configured by `SetupThread(..., stack_base=0x01FA0000, stack_size=0x60000)` (`syscall 0x3C`); initial `$sp = 0x02000000` | `[CONFIRMED recomp_source/sub_00100210_0x100210.cpp:92-105, PS2Recomp/ps2xRuntime/src/lib/Kernel/Stubs/System.cpp:250-334]` |
| `0x70000000..0x70003FFF` | `16,384 B` (`16 KB`) | **EE Scratchpad RAM (SPR)** | Dedicated fast internal memory (`m_scratchpad`) | `[CONFIRMED PS2Recomp/ps2xRuntime/src/lib/ps2_memory.cpp:378-383]` |

---

## 3. Pairwise Overlap & Conflict Analysis

### 3.1 Conflict A: `ps2xRuntime` Async SIF Stack vs Game Dynamic Heap Pool
- **Region A**: `ps2xRuntime` Async SIF Callback Stack Pool (`0x01F00000 .. 0x01FA0000`, 640 KB).
- **Region B**: Game Custom Dynamic Memory Pool (`0x00783000 .. 0x01FA0000`, 24.11 MB).
- **Audit Finding**: **Direct Latent Architectural Overlap**.
  - The runtime sets `m_asyncCallbackStackFloor = 0x01F00000` and `m_asyncCallbackStackTop = 0x01FA0000` (`ps2_runtime.cpp:1117-1118`).
  - The game initializes its heap pool at `sub_0036E05C:80-99` using `0x01FA0000 - 0x00783000 = 0x0181D000`, reserving the entire space up to `0x01FA0000` for its own heap blocks.
  - Active heap usage at boot/title: `REGN:19,432,576` bytes + `HEAP:2,466,808` bytes = `21,899,384` bytes (`0x14E27D8` bytes).
  - Upper bound of current allocations: `0x00783000 + 0x14E27D8 = ~0x01C657D8`.
  - Current safety headroom: `0x01F00000 - 0x01C657D8 = 0x29A828` (`~2.60 MB`).
- **Severity**: **HIGH (Latent Critical Risk)**.
  - As soon as a full gameplay level, cutscene, or stage dataset is loaded into the heap, total dynamic allocations exceeding `23.49 MB` will cause the game allocator to hand out pointers in `[0x01F00000, 0x01FA0000]`.
  - When an async SIF command callback fires, `reserveAsyncCallbackStack` will allocate stack frames in `[0x01F9C000..0x01FA0000]` and `[0x01F98000..0x01F9C000]`, directly corrupting game asset data or stack memory.
- **Cheapest Runtime Detection Check**:
  - Gated under `PS2X_AUDIT_MEMORY=1`.
  - In `sub_0036EDAC` (heap allocate) or `ps2TraceGuestWrite`: if a guest write or allocation address falls in `[0x01F00000, 0x01FA0000]`, print an immediate alert to `stderr`:
    ```cpp
    if (vaddr >= 0x01F00000u && vaddr < 0x01FA0000u) {
        std::fprintf(stderr, "[FATAL:MEMORY_COLLISION] Game heap write into async stack pool: 0x%08x\n", vaddr);
        std::fflush(stderr);
    }
    ```

---

### 3.2 Conflict B: Main EE Thread Stack Headroom
- **Region A**: Main EE Thread Stack (`0x01FA0000 .. 0x02000000`, 384 KB).
- **Audit Finding**: **No Overlap; Abundant Headroom**.
  - Initial `$sp` is `0x02000000`. The stack grows strictly downwards towards `0x01FA0000`.
  - Across all execution logs (`baseline.log`, `step1_err.log`, `step3_rebuild2_err.log` covering 300+ main loop iterations):
    - Initial stack pointer: `sp = 0x01FFFFE0` (32 bytes used).
    - `crt0` stack pointer: `sp = 0x01FFFF40` (192 bytes used).
    - Main loop stack pointer: `sp = 0x01FFF5B0` (2,640 bytes used).
    - Deepest observed stack frame: `sp = 0x01FFF380` (3,200 bytes used).
  - Headroom remaining before reaching stack floor `0x01FA0000`: **`380.88 KB`** (`389,000` bytes, or **99.17%** of stack space free).
- **Severity**: **NONE (Healthy)**.
- **Cheapest Runtime Detection Check**:
  - Gated under `PS2X_AUDIT_MEMORY=1`.
  - Inside `dispatchGuestBranch` / function entry:
    ```cpp
    if (ctx->r[29].u32[0] < 0x01FA0000u && ctx->r[29].u32[0] >= 0x01F00000u) {
        std::fprintf(stderr, "[STACK OVERFLOW] Main stack pointer crossed floor: sp=0x%08x\n", ctx->r[29].u32[0]);
    }
    ```

---

### 3.3 Conflict C: `0x00120000..0x0013F7FF` Overwrite vs Post-Boot Constant/Data Reads
- **Region A**: `DATA.BIN` VFI Index Buffer (`0x00120000 .. 0x0013F7FF`, 63 sectors = `129,024` bytes).
- **Region B**: ELF `.text` code section (`0x00100000 .. 0x00628258`).
- **Audit Finding**: **Safe Intentional Memory Reuse; Zero Collisions**.
  - 217 recompiled functions have nominal entry addresses within `0x00120000..0x0013F7FF`.
  - Execution tracking in `logs/baseline.log:28-29`:
    - `[region-0x120000:branch] First branch into 0x120000..0x13F800 at targetPc=0x0013b098 from sourcePc=0x00428ae8 (total hits: 1)`
    - `[region-0x120000] First execution in 0x120000..0x13F800 at pc=0x0013b04c (total hits: 1)`
    - Only `sub_0013B098` executes once via global constructor table `.ctors` before disc reads occur.
    - Subsequent executions in `0x00120000..0x0013F800`: **0 hits** across the entire lifecycle.
  - Read access scan:
    - Searched all 23,349 recompiled C++ source files for memory read macros (`READ_MEMORY_*`, `FAST_READ*`, pointer arithmetic) referencing `0x00120000..0x0013F7FF`. **Result: 0 hits**.
    - Searched all files for base register loads (`lui 0x12`, `lui 0x13`). **Result: 0 hits** (only disassembly comments).
    - Switch jump tables and constants are located in `.rodata` (`0x006B8000..0x0072C040`), completely outside `.text`.
  - Only `file3.irx` accesses `0x00120000` via DMA (`sreg26 = 0x120000`), treating it exclusively as the VFI table.
- **Severity**: **NONE / LOW (Harmless)**.
- **Cheapest Runtime Detection Check**:
  - Gated under `PS2X_AUDIT_MEMORY=1`.
  - In `PS2Runtime::Read32`:
    ```cpp
    if (vaddr >= 0x00120000u && vaddr < 0x0013F800u && m_vfiLoaded) {
        std::fprintf(stderr, "[WARN:0x120000_READ] Guest read from VFI index buffer at pc=0x%08x addr=0x%08x\n", ctx->pc, vaddr);
    }
    ```

---

### 3.4 Conflict D: Newlib Heap vs Game Custom Heap
- **Region A**: Newlib C runtime heap (`0x00772910 .. 0x00782910`, 64 KB).
- **Region B**: Game Custom Heap Pool (`0x00783000 .. 0x01FA0000`, 24.11 MB).
- **Audit Finding**: **No Overlap; Clean Separation**.
  - `SetupHeap(0x00772910, 0x10000)` defines the Newlib heap limit as `0x00782910` (`System.cpp:336-380`).
  - `sub_0036E05C:28-50` takes `0x0077390F + 0x10000 = 0x0078390F` and page-aligns it with `& ~0xFFF` to start the game heap pool at `0x00783000`.
  - The regions are separated by a `1,776-byte` (`0x6F0`) unmapped alignment gap (`0x00782910 .. 0x00783000`).
- **Severity**: **NONE**.

---

### 3.5 Conflict E: FCFD Slots & CID1 Buffers vs Other Subsystems
- **Region A**: FCFD control slots:
  - Instance 0: `0x007717CC .. 0x007718BC` (16 slots * 16 bytes = 256 bytes).
  - Instance 1: `0x00771BBC .. 0x00771CBC` (16 slots * 16 bytes = 256 bytes).
- **Region B**: Static `.bss` section (`0x0072D680 .. 0x00772910`).
- **Audit Finding**: **Valid Placement; No Overlap**.
  - Both tables are statically allocated within `.bss` (`0x00771798` and `0x00771B88`), comfortably below the end of `.bss` at `0x00772910`.
- **Severity**: **NONE**.

---

## 4. Summary Table of Risks & Recommendations

| Potential Conflict | Tested Address Range | Overlap Status | Severity | Recommended Fix / Mitigation |
| :--- | :--- | :--- | :--- | :--- |
| **Async SIF Stack vs Game Heap Pool** | `0x01F00000..0x01FA0000` | **CONFIRMED LATENT OVERLAP** (Headroom ~2.6 MB at boot; will collide on heavy levels) | **HIGH** | Relocate the async SIF stack pool out of guest RDRAM or move it to a dedicated non-heap area (e.g., above `0x01FA0000` in the unused 380 KB of main thread stack headroom). |
| **Main Thread Stack Growth** | `0x01FA0000..0x02000000` | **CONFIRMED NO OVERLAP** (Deepest frame depth 3,200 B; 380.88 KB headroom) | **NONE** | No action required. Main thread stack usage is minimal. |
| **`0x00120000` VFI Index Read** | `0x00120000..0x0013F7FF` | **CONFIRMED HARMLESS OVERWRITE** (Only 1 constructor before read; 0 memory reads post-boot) | **NONE** | Maintain current behavior. Recompiled functions run from C++ function table, not RDRAM. |
| **Newlib Heap vs Game Heap** | `0x00772910..0x00783000` | **CONFIRMED NO OVERLAP** (1,776 B padding gap separates them) | **NONE** | No action required. |
| **FCFD Slots in `.bss`** | `0x007717CC..0x00771CBC` | **CONFIRMED VALID PLACEMENT** (Within static `.bss` section) | **NONE** | No action required. |
| **CID1 Destination Buffers** | `0x0079120C..0x018F5EC0` | **CONFIRMED ALLOCATED FROM GAME HEAP** | **NONE** | Subject to overall game heap pool headroom. |
