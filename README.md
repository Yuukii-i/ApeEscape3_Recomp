# Ape Escape 3 (SCUS_975.01) Static Recompilation

A static recompiler port of the PlayStation 2 game Ape Escape 3 (SCUS_975.01) targeting modern PC platforms via PS2Recomp (ps2xRecomp, ps2xAnalyzer, and ps2xRuntime) with Raylib presentation[cite: 1, 4].

The project recompiles the original MIPS R5900 Emotion Engine executable into native C++ code (recomp_source/), supported by an HLE (High-Level Emulation) runtime for PS2 hardware components, kernel syscalls, and IOP services[cite: 1, 4].

---

## Current Status Overview

The recompiled executable successfully passes crt0 startup, initializes the cooperative scheduler and memory heaps, clears BSS, registers configuration stubs, mounts disc paths, and enters the game's main loop (sub_001037E8)[cite: 1, 2].

- Execution Progress: Reaches main loop; currently blocked at the end-of-frame wait loop[cite: 2, 4].
- Display Pipeline: Core GIF arbiter (Paths 1, 2, 3), GS rasterizer, and Raylib frame presentation are structurally connected, but the output displays a black screen pending interrupt and file-streaming unblocks[cite: 4].
- 3D Subsystem: Full dual-pipeline VU1 micro-mode interpreter (16 KB micro / 16 KB data) is implemented and connected to GIF Path 1 via XGKICK, enabling native 3D geometry rendering once the frame pipeline unblocks[cite: 4].

---

## What Has Been Completed

### Kernel & Startup
- crt0 and BSS Setup: The startup loop entry issue was identified and resolved via PS2X_HAS_RECOMPILED_GAME=1 guard flags, allowing clean single-pass execution of crt0[cite: 1].
- Memory Subsystems: Main RDRAM (32 MB), Scratchpad (16 KB at 0x70000000), thread stacks, and heap boundaries are active[cite: 1, 4].
- Config Stubs Loader: config.toml runtime stub resolver binds 202 recognized stubs without overriding recompiled guest functions[cite: 1].
- Calling Conventions: Proper 8-byte stack slot alignment for variadic argument lists (va_list) has been implemented to match EABI64 conventions[cite: 1].

### Hardware & Graphics Pipeline
- GIF Arbiter: Complete PATH1 > PATH2 > PATH3 priority scheduling supporting PACKED, REGLIST, and IMAGE modes[cite: 4].
- VU1 Micro-Mode Interpreter: Dual-pipeline execution (upper vector float SIMD and lower integer/branch/EFU/XGKICK) active in runtime[cite: 4].
- GS Rasterizer Backend: Full software rasterizer handling primitives (POINT through SPRITE), texture/CLUT formats (PSMCT32, PSMT8/4, etc.), alpha testing, Z testing, and scissoring[cite: 4].
- Presentation Loop: Raylib-backed renderFrame resolving display registers (PMODE, DISPFB, DISPLAY) and uploading active VRAM pages[cite: 4].

### Disc & IOP Infrastructure
- Disc & VFI Indexing: The DATA.BIN layout at ISO LSN 3576 is reverse-engineered[cite: 1]. The initial 63 sectors (129,024 bytes) comprise a VFI index holding 3,994 file entries and 266 directory records[cite: 1].
- SIF / RPC Communication: Handshakes for SETSREG (0x80000001) and initial module loading are implemented[cite: 1].
- Controller Handshake: Minimal HLE handlers for DBC services (0x80001300, 131C/E/F) are bound, allowing sceDbcInit to pass[cite: 1, 4].
- Virtual Memory Card: Directory-backed virtual memory card emulation (mcman / mcserv) is present in the runtime[cite: 4].

---

## Current Blockers & Active Work

### 1. Frame Wait Loop Unblocking (Active)
- Behavior: At the end of the frame, sub_00284534 spins at 0x284540..0x284558 checking *(int32_t*)0x00649DE4[cite: 1, 4].
- Root Cause: 0x00649DE4 is updated by the INTC cause 5 (VIF1) interrupt handler sub_002843D4 upon observing VIF1_MARK == 0x2000[cite: 1, 4].
- Solution Underway:
  - Add an environment-gated frame-dump diagnostic (PS2X_DUMP_FRAMES) to verify frame contents during execution.
  - Wire VIF1_MARK register reading at 0x10003C30 and route INTC cause 5 through EeScheduler[cite: 2, 4].
  - Implement FBRST clear/reset semantics according to hardware specification.

### 2. File Streaming Implementation (CID1 / file3.irx)
- Current State: SIF command CID1 returns a dummy status without reading actual sectors from DATA.BIN (zero bytes loaded)[cite: 1].
- Required Work: Implement sector reads from ISO LSN 3576 + start_sector into guest RDRAM, and populate the 64-byte stat response packet expected by the EE handler at 0x1DCEE0[cite: 1, 2].

### 3. Removal of Foreign-Game Hacks in MPEG/IPU
- Issue: Legacy code in MPEG.cpp writes hardcoded values to guest memory addresses (0x1717BC..0x171904 and 0x1209F8), which overlap Ape Escape 3 executable code and the VFI index buffer[cite: 1, 4].
- Required Work: Strip all hardcoded addresses from MPEG.cpp and clean up IPU sync handling before FMV routines execute[cite: 1, 2].

### 4. Code Generation & Translator Corrections (ps2xRecomp)
- Branch Sign Evaluation: Change REGIMM branches (BLTZ, BGEZ, BLEZ, BGTZ) in control_flow_emitter.cpp to evaluate 64-bit signed integers (GPR_S64) instead of 32-bit (GPR_S32)[cite: 2, 4].
- Conditional Moves: Fix MOVZ/MOVN in special_translator.cpp to preserve upper 64 bits[cite: 2, 4].
- VU0 Macro Addressing: Fix emitVuMemByteAddress in vu_translation_helpers.cpp to offset addresses by 0x11004000 (VU0 data memory) instead of reading low RDRAM (0x0000..0x3FF0)[cite: 2, 4].
- FPU Truncation: Update FPU_CVT_W_S to use truncf instead of nearbyintf to match standard R5900 COP1 behavior[cite: 2, 4].

### 5. Input & Audio Subsystem Wiring
- DBC Controller Input: Disassemble dbcman.irx / ds1o.irx to identify the DMA receive buffer and pipe live keyboard/gamepad state from PS2PadBackend[cite: 2, 4].
- SG2 Audio HLE: Replace the manual override on 0x3703D4 by implementing the completion callback for SoundGroup2 (sg2iopm1.irx, RPC 0x80001800), invoking sub_003703D0 to clear the busy flag[cite: 1, 2].

---

## Upcoming Work Roadmap

| Step | Topic | Target Files | Builds Required |
| :--- | :--- | :--- | :--- |
| 1 | Remove foreign-game hacks in MPEG/IPU | Kernel/Stubs/MPEG.cpp, IPU.cpp[cite: 5] | ps2EntryRunner (small)[cite: 5] |
| 2 | CID1/file3 and VFI spec plus lister tool | docs/, tools/vfi/[cite: 5] | No[cite: 5] |
| 3 | DBC (input) and SG2 (audio) protocol specs | docs/[cite: 5] | No[cite: 5] |
| 4 | Memory-map audit | docs/[cite: 5] | No[cite: 5] |
| 5 | Repo hygiene, regeneration safety, build/run scripts | scripts/, docs/[cite: 5] | No[cite: 5] |
| 6 | Translator bug fixes with before/after diff | ps2xRecomp sources only[cite: 5] | ps2xRecomp only[cite: 5] |

---

## Directory Structure

- build/ : CMake and Ninja build artifacts.
- docs/ : Architectural audits, capability documents, and review logs[cite: 1].
- recomp_source/ : Auto-generated C++ code emitted by ps2xRecomp from the game ELF[cite: 1].
- tools/ : Reverse engineering, IRX extraction, disassembly, and analysis scripts[cite: 1].
- PS2Recomp/ : The core recompiler suite (ps2xRecomp, ps2xAnalyzer, ps2xRuntime) tracked as a submodule[cite: 1].
- CMakeLists.txt : Root build script compiling the runtime together with the recompiled game code[cite: 1].
- config.toml : Recompiler configuration specifying entry ELF, stubs, and function mappings[cite: 1].
- NOTES.md : Master knowledge base of verified system facts, memory maps, and protocol layouts[cite: 1].
- PLAN.md : Sequential roadmap, milestone requirements, and task backlog[cite: 1, 2].

---

## Building and Running

Prerequisites: CMake, Ninja, and a compatible C++20 compiler (Clang/MSVC).

Configure and build:
cmake -B build -G Ninja
cmake --build build --target ps2EntryRunner

Run the executable:
.\build\PS2Recomp\ps2xRuntime\ps2EntryRunner.exe SCUS_975.01

The runner resolves the game disc via command-line path, the PS2X_ISO environment variable, or an ApeEscape3.iso located in the working directory[cite: 1].