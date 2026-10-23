import os

task_n_section = """
## Task N: EE RDRAM Source Trace, VIF1 Direct Unpacking Fix, and Real MC Primitive Audit

### Part A: Now Loading Texture Corruption Root Cause & Fix (`tbp0=10752`)
- **A1 — Upload DMA Origin Identified**:
  - `[CONFIRMED logs/run_taskN_step2.log:275]`: The GS image upload originates from VIF1 DMA channel (`0x10009000`), executing chained DMA tags with `TTE=1`.
  - `[CONFIRMED logs/run_taskN_step2.log:275]`: Tag 4 (`tagAddr=0x00B86370`, `id=3` REF, `qwc=512`, `dataAddr=0x00D15A40`, `w2=0x00000000`, `w3=0x50000200`, `TTE=1`) transfers the texture payload directly from guest heap address `0x00D15A40`.
- **A2 & A3 — EE RDRAM Buffer Integrity Confirmed**:
  - `[CONFIRMED logs/run_taskN_step2.log:275]`: The raw EE RDRAM buffer at `0x00D15A40` is 100% clean and uncorrupted. Its first 8 bytes in RDRAM are `[0, 0, 0, 0, 0, 0, 0, 0]`. There is NO EE recomp-miscompilation.
- **A4 — Root Cause of 8-Byte Header & -2 Shift**:
  - `[CONFIRMED ps2_vif1_interpreter.cpp:310-345, logs/run_taskN_step2.log:275]`: In `ps2_vif1_interpreter.cpp`, `m_vif1PendingPath2ImageQwc != 0u` was intercepting the incoming data stream at the very top of `processVIF1Data` before decoding VIF commands.
  - In chained DMA with `TTE=1`, the DMA controller appends the tag's upper 64 bits (`w2=NOP` and `w3=VIF_DIRECT(512)`) to the buffer before the tag's payload.
  - Because `m_vif1PendingPath2ImageQwc` intercepted execution at `pos = 2488`, it treated `w2` and `w3` (`[0, 0, 0, 0, 0, 2, 0, 80]`) as raw image pixels!
  - This inserted 8 bytes of VIFcode header, shifted all pixel indices by 8 bytes (-2 words), and sliced off the last 8 bytes of the image payload.
  - Tag 5 (CLUT upload at `0x00D17A40`, 64 QWs) was similarly corrupted with its own 8-byte VIFcode header `[0, 0, 0, 0, 64, 0, 0, 80]`.
- **A5 — Decisive Fix & Metric Validation**:
  - `[CONFIRMED ps2_vif1_interpreter.cpp:513-545]`: Removed pending image quadword interception from the top of the while loop in `processVIF1Data`, handling pending image quadwords inside `VIF_DIRECT` where `w2` and `w3` are properly consumed as VIF commands.
  - `[CONFIRMED ps2xRuntime/src/lib/gs/gs_cpu_backend.cpp:808-812]`: Enabled standard 32-bit CSM1 CLUT swizzle by default in `LoadClutUnlocked`.
  - `[CONFIRMED tools/gs/cmp_tex.py]`:
    - Direct Mismatch: dropped from **52.87%** to **0.00% (0 / 8,192 px)**!
    - Best cyclic shift: **dx=0, dy=0** (0.00% mismatch).
    - 16x16 Block Mapping: 100% of blocks (0..7, 0..3) match their exact block coordinate with sum L1 diff = 0!

### Part B: Memory-Card Real Primitives Audit
- **B1 & B2 — Real Primitives Logged (idx 60..512)**:
  - `[CONFIRMED logs/run_taskN_step1.log:2643, logs/run_taskN_step2.log:275]`: Un-capped primitive logging from 64 to 512. Ticks 60..80 draw ONLY Primitive 62 (`rect=(192,352)-(320,416)`, Now Loading icon) and fullscreen fade-to-black quad passes (`rect=(0,0)-(512,448)`).
  - `[CONFIRMED logs/run_taskN_step1.log:2643]`: There is NO primitive drawing a wide box at `Y ~ 460..512`. Ape Escape 3 does NOT draw an error/prompt dialog because `sceMcGetInfo` returns synchronous success (`result=0`, 8192 KB free). The game immediately fades out to load game assets.
- **B3 & B4 — Tick 70 Blank Frame Explanation**:
  - `[CONFIRMED frames/frame_tick70.png, logs/run_taskN_step1.log:2643]`: The frame at tick 70 (`hash=0xefb69dc5`) is completely black because the screen reached `alpha=0` at tick 69. FNV-1a hash `0xefb69dc5` is simply the hash of an all-black (zeros) framebuffer.

### Part C: Console Stalls Silenced
- `[CONFIRMED ps2_runtime.cpp:1772-1815, logs/run_taskN_step1.log]`: Gated `vfprintf` guest logging behind `PS2X_TRACE_PRINTF=1` (default 0), redirecting fd 2 writes to `NUL`. Completely eliminated `[vfprintf:diag]`, `[guest-log]`, `SYNC:5101%`, and stuck EE diagnostic dumps during save-flag initialization.
"""

with open('docs/HANDOFF.md', 'r') as f:
    handoff = f.read()

# Update Working tree in HANDOFF.md
wt_marker = "## 3. Working Tree"
if wt_marker in handoff:
    prefix = handoff[:handoff.find(wt_marker)]
    new_wt = """## 3. Working Tree
- PS2Recomp HEAD: `122a8fcad0be13b72bd6d1b80cd010c27301d304`
- Uncommitted modified files:
  - `ps2xRuntime/src/lib/diag/DiagSampler.h`
  - `ps2xRuntime/src/lib/gs/gs_cpu_backend.cpp` (32-bit CSM1 CLUT swizzle enabled by default, direct dump hooks)
  - `ps2xRuntime/src/lib/gs/gs_frontend.cpp` (TEX2 CBP preservation fix)
  - `ps2xRuntime/src/lib/ps2_memory.cpp` (DMA VIF1 tag diagnostic logging)
  - `ps2xRuntime/src/lib/ps2_runtime.cpp` (vfprintf console stall gating, presenter dump hooks)
  - `ps2xRuntime/src/lib/ps2_vif1_interpreter.cpp` (VIF_DIRECT pending image quadword fix)

## 4. Next Actions
1. Advance past publisher logos (`debug/us/etc/publogo/publogo.pck.sz`) and implement MPEG/IPU decoding or bypass to reach the title screen.
2. Wire runtime gamepad/keyboard input into menu navigation state.
"""
    handoff = prefix + task_n_section + "\n" + new_wt

with open('docs/HANDOFF.md', 'w') as f:
    f.write(handoff)

with open('NOTES.md', 'a') as f:
    f.write("\n" + task_n_section + "\n")

print('Successfully updated docs/HANDOFF.md and NOTES.md!')
