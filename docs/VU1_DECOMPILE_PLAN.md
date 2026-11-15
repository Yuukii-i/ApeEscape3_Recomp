# VU1 decompile plan (2026-11-12): whole-program functional VU1 for the shop/gameplay image

## Why (measured, AUTONOMOUS_LOG 32-36)
- Frame = EE work until the per-frame VIF kick (~4.6 ms) + VIF job latency (~20.3 ms, silent). Job latency = Vu1Exec work.
  60 fps needs the job <= ~12 ms: about -8 ms of VU1 time per frame. CPU savings elsewhere do not move fps (PGO: -10% CPU, 0 fps).
- Vu1Exec is already heavily tuned (native kernels, generated hot blocks, closed-form XGKICK drain). Every remaining item is <= 5%
  except the skinning kernel; per-call fixed overhead ~1.1 us x ~2600 calls/frame.
- Splitting programs over two threads (DB1-DB3) is exact but slower: programs depend on their predecessor (constants, qword 1018,
  table 636-795) and per-program sync costs too much (log 34).
- Exact cycle/pipeline emulation is the cost. Program output never depends on inherited registers/flags (log 28) and the second
  instance proves outputs are a pure function of entry memory (log 33, PROBE-DC3). So a functional re-implementation that produces the
  same VU memory writes and GIF bytes is enough; cycle counts, pipeline state and exit registers are not observable outside VU1
  (exception: anything the EE reads back - check VIF1_STAT/TOP/ITOP only).

## Target
PS2X_VU1_FUNC=1: for the known code image(s), MSCAL runs a decompiled C++ program (one function per program image, the dispatcher +
command handlers as plain C++/AVX2 over VU memory) that writes the same memory and emits the same GIF packets. Unknown image or any
unhandled path -> today's exact path (fallback is per MSCAL, decided before running, so no partial state).

## Steps
1. Program map (probe): for image 86503d3905e35276 (and the others seen live: d6b2281aa7efd05a, 4279fa21...), count per MSCAL the
   command handlers entered (dispatcher JR vi1 targets) and the time per handler (rdtsc around native block/kernel runs keyed by
   handler entry pc). Output: handler pc, calls/frame, ms/frame, share. Decides the order of work.
2. Harness: corpus replay compares only memory + GIF (registers/flags/cycles ignored in FUNC mode) - add PS2X_VU1_REPLAY_FUNC=1.
   Make the replay use the same hot-block table as live (replay showed 6M noStart slow pairs that never happen live).
3. Decompile handlers in share order, each as a C++ function on (vuData, top, itop, input registers the dispatcher passes) ->
   writes + GIF bytes + the registers the dispatcher reads after JR back. Start: the 0158 matrix loop (vuH_14, 4.9%), skinning
   (1FE0, lbFull is already the closed form), vertex/clip machine (2440 + 28A0 trivial reject; real clipping 2900+ last), copy (0C80).
4. Dispatcher in C++ (TOP -> command list loop); a handler without a decompiled version -> whole MSCAL falls back.
5. GIF emission straight into the coalescing buffer (no m_xgkick.packet copy), one submit per program.
6. A/B per step (silent, shop + one gameplay level), screenshots, replay MISMATCHED(mem/gif)=0 on the shop corpus + a new gameplay corpus.

## Long-term goal this design must serve (user, 2026-11-12)
Final project objective: modern lighting at "PS3 level" (simple shadows, light shafts, bloom, depth of field; no ray/path tracing).
So the decompiled handlers must not be a black box that only reproduces GIF bytes. Keep the semantic layer visible:
- per handler: inputs as named data (object matrices, bone matrices, light/colour constants, vertex streams), outputs as
  world/view-space positions + normals + UV + colour BEFORE projection/packing, then a separate "pack to GIF" step;
- a hook where a modern renderer can take the geometry (per object/draw: transform, vertices, material = TEX0/ALPHA state) instead of
  the packed GS primitives.
What needs what: bloom, DoF and god rays are post-processes on the Vulkan GS output + its depth buffer (possible before the
decompile is finished); real shadows need the decompiled geometry path (re-render from the light, or shadow maps) plus the light
direction from the VU constants. Order stays: speed first (exact functional output), semantic hooks designed in from step 3 on.

## Risks
- Hidden readers of VU1 state outside VU1 (EE reads of VU1 memory via VIF/MFIR paths, XITOP/XTOP) -> check before step 4.
- Float exactness: VU float semantics (no denormals/inf, clamp) must be reproduced in the C++ (existing helpers in vu1_hot_ops.h).
