# Task FR2: repeat the replayed function N times on the carried-over RAM and watch addresses (cpp only)
Budget: "[call N/12]", stop at 12. Edit ONLY ps2_runtime.cpp (ps2xFnReplay). No headers. DO NOT BUILD/RUN/COMMIT. Mark `// PROBE-FR2`.
Why: replaying the per-entity update fn 0x4DD63C(a0 = player entity 0x8B6FB0) once per frame on PCSX2's state should reproduce the game's frame-by-frame behaviour; in PCSX2 the ground-contact point at 0x8D95E4 (float) turns from -23 to +18 (rope hit) within ~10-60 frames; in ours it never does. We want to run the entity update N times in a row in ours (no other game systems) and see if/when it flips.
Do:
1. Env PS2X_FNREPLAY_REPEAT=<N> (default 1, clamp 1..100000). Loop N times: before EACH iteration re-apply the registers from the spec exactly as for iteration 1 (gpr/hi/lo/fcr31/fpr/vf/acc, pc, sp, ra) but DO NOT reload RAM (RAM carries over). Run the dispatch loop to completion (pc==ra && sp==entry sp) per iteration (same loop as now); if an iteration fails to complete log `[fnreplay] iter %u INCOMPLETE pc=.. sp=..` and stop.
2. Env PS2X_FNREPLAY_WATCH="0xA,0xB,..." (up to 16 addresses): after every iteration print one line `[fnreplay] iter %u w 0xA=%g 0xB=%g ...` (each as float read from guest RAM, also hex `(0x%08x)`).
3. Suppress the per-step/dcall/hist logs when REPEAT > 1 (keep only the first iteration's logs) so logs stay small.
4. Final RAM + regs written once after the last iteration as now.
Acceptance: compiles, no header edits. Reply <=3 lines.
