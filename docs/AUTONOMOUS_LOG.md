# Autonomous log (2026-11-09, user away)

Rules: Gemini 3.8 Flash Medium writes all code; I build/run/judge; every number below is from `tools\ab.ps1` through the pad replay at the shop (dev build, boost mode), noise (same exe twice): frame p50 +-0.05..0.25 ms, Vif1Worker +-0.15, GsWorker +-0.55.

## Baseline (dev build, GPU present on, LBR on): p50 18.6, p99 24.4, GameThread 10.0, Vif1Worker 14.4, GsWorker 13.3, PresentLatch 3.4, total 43.8 CPU-ms/frame.

## 1. Fast dev build (done)
Incremental 16-19 s (was ~85 s). Committed 1c9f63a.

## 2. Pad record/replay + ab.ps1 (done)
Replay by DBC poll count reaches the shop, `[bench] START` marks the end. One A/B of 2 rounds takes ~6 min unattended.

## 3. Step 4a, batched GS worker pop `PS2X_GS_BATCHPOP=1` (Task LD): KEPT
A/B gb1 (2 rounds each): GsWorker 13.33 -> 12.30 (-1.03, -7.7%), PresentLatch 3.38 -> 0.90, total 43.78 -> 39.91 CPU-ms/frame (-8.8%), Vif1Worker and GameThread unchanged, frame p50 18.73 -> 18.92 (noise).
Why p50 did not move: `[wait]` shows the EE waits at the VIF1 fence 2651 ms of a 6678 ms window (40%, once per frame) and the Vif1Worker is busy 87% of wall time. The Vif1Worker is the critical path, so only Vif1Worker reductions move the frame time now.

## 4. PERF-RS lean per-run VU1 overhead PS2X_VU1_LEAN=1 (Task LE): REFUTED, reverted
A/B ln1 (BATCHPOP on both sides): Vif1Worker 14.17 -> 14.27, frame p50 18.80 -> 18.52 (noise 0.4), total 39.46 -> 39.48. The explorer's ns estimates were too high: setup_ms is mostly the TSC probes themselves. Per-run overhead is not a lever. Edits reverted (git checkout).

Vif1Worker breakdown (profile run vp1, per second): fn=870 ms = vu1 runs 624 (native 469: hot blocks 204, skinFull 132, vertex 30, copy 15) + unpack 146 + direct 44 + other parse 56. Top unpack shapes: 0x65 (V2-16) 200k/s at 151 ns/call = 8 ns per vector (30 ms/s), 0x6C 19 ms, 0x74 15 ms, 0x64 10 ms, 0x78 9+5 ms. 19 vectors in 151 ns is ~2 GB/s, so SIMD fast paths are plausible: next cycle.

## 5. SIMD UNPACK fast path `PS2X_UNPACK_SIMD=1` (Task LF): verified, NO speed gain (kept off)
Verify run us1: 58.9M UNPACKs compared against the generic path, 0 mismatches. A/B us2 (2 rounds): Vif1Worker 14.56 -> 14.52 (noise 0.04), GsWorker 12.07 -> 11.61, frame p50 18.98 -> 20.02 (run-to-run noise on p50 up to 1 ms this time). UNPACK is not a lever. Lesson: the VIFSTAT/TSC probes cost ~40 ns per call, the same size as the work measured, so probe-based breakdowns over-attribute. Switched to the sampling profiler (PS2X_PROF_SAMPLE=1 PS2X_PROF_VU1WORKER=1 PS2X_PROF_GSWORKER=1, run ab.ps1 -Tag sp1, output lines [prof2] t=.. thread=..).

Vif1Worker sampling profile (thread self time): idle wait 10%, processVIF1Data 9.5% + its lambda_5 6.6% (parse/unpack), vu1NativeRun 7.5%, lbFull 6.4%, lbVertex8R 5.3%, vuH_* hot blocks ~12%, memmove 3.8%, run::lambda_2 3.1%, vifStatOn 2.5% (!), progressXgkick 2.1%, flushPipelines 1.4%, resetScheduler 1.3%, memchr 0.8%, probe gates (isBhProbeEnabled, handleMovieHleMscal, isDcProbeEnabled, svOn, recordEpEvent) ~1.4%, NtWriteFile 0.4%. Probe-gate overhead is ~5% = ~0.7 ms/frame. Next: Task LG (hoist gates, no switch since behaviour is identical).

## 6. Probe-gate hoisting (Task LG): REFUTED, reverted (together with the unused SIMD unpack edits of LF)
A/B lg1 (4 runs, same exe): Vif1Worker 14.28-14.36 vs the earlier 14.17-14.56: no change. The profiler's vifStatOn 2.5% was symbol misattribution. Conclusion: micro-trims of <1% items cannot move Vif1Worker; the thread is at ~14.3 ms and needs either structural work (step 7 direct geometry) or the PGO acceptance build (-1.7 ms measured earlier).

## 7. The per-frame EE stall: found, candidate fix needs visual check
- Wait-site probe: the 7-9 ms/frame EE wait is a full VIF1 drain inside sceGsSyncPath (guest fn 0x404230, a stub). PS2X_SYNCPATH_ASYNC=1 alone does nothing (A/B sy1: p50 18.60 vs 18.62) because the lag path only covers ra 0x0051E290 (24 of every 120 calls); the other 96 calls come from guest ra 0x00284558 (~4/frame, probe [syncpath], env PS2X_SYNCPATH_LOG=1) and still drain.
- Task LI: `PS2X_SYNCPATH_SKIP_RA=0x284558` (needs PS2X_SYNCPATH_ASYNC=1) returns from those calls without waiting. A/B sk1 (A = ASYNC only, B = ASYNC + SKIP_RA, 2 rounds each): fps 51 -> 57, frame p50 18.38 -> 16.60 ms, but p99 28.98 -> 44.70 ms, and Vif1Worker/GsWorker CPU per second HALVED (7.7/6.7 vs 14.1/12.6 ms per 60 fps), GameThread 9.2 -> 12.4. Halved worker CPU at higher fps means work disappeared: possibly skipped draws or a different game state. NOT accepted until a screenshot shows the same picture. Next: Task LJ (tools/shot.ps1 screenshots at the shop spot, A vs B).

## 8. SKIP_RA: screenshots and per-frame work (tools\shot.ps1, Task LJ): NOT ACCEPTED, needs the user's eyes
- Screenshots at the shop spot (logs\shot_base0_1.png, shot_ctrl0_1.png, shot_skip0_1.png): all three show the same street, HUD, labels, character, no missing geometry. Fps in the window title: baseline 51, SKIP_RA 58.
- But per frame the skip build does ~43% LESS guest work: [vifstat] mscal 311k/s at 50 fps (6200/frame) vs 198k/s at 55-56 fps (3550/frame), unpack 1.47M/s vs 0.94M/s, VIF calls/s 49 vs 66. Worker CPU per frame halves (Vif1 14.06 -> 9.04, Gs 12.01 -> 7.60), EE rises 9.2 -> 12.4, p50 20.0 -> 16.7, p99 gets worse (29 -> 44 ms).
- Possible explanations (none verified): (a) the guest retries or repeats submissions while it finds the path busy, which the drain used to hide, (b) invisible work is skipped, (c) the replay ends in a different game state (the replay's end state depends on timing; ctrl and skip show the hero at different spots). Visible result looks right, but this must be checked in play (shadows, particles, effects, minimap) before it can become default.
- Rule going forward: A/B comparisons are valid only between runs that do the same work per frame; use [vifstat] mscal per frame as the fingerprint (PS2X_VIFSTAT=1, line in .out).
- State: PS2X_SYNCPATH_ASYNC=1 PS2X_SYNCPATH_SKIP_RA=0x284558 stay OFF by default.

## 9. SKIP_RA explained: REFUTED (it halves the real render rate)
Per-program VU1 calls per displayed frame (sk3, PS2X_VU1_TSC=1): skinFull 185k/s at 49 fps = 3777/frame (A) vs 111.6k/s at 59 fps = 1891/frame (B); pc 0158 687 vs 347; pc 0028 17.4k vs 8.8k; every program ~0.5x per flip, and in absolute terms B does 60% of A's work per second. So with the drain skipped the game renders a NEW scene only about every other flip (~30 unique frames/s) while the runtime flips at 59/s. The 16.7 ms p50 and the halved worker CPU are an artifact of half-rate rendering, not a speed-up. The game's frame pacing depends on those syncs. Do not use PS2X_SYNCPATH_SKIP_RA (kept in code, off by default, documented as refuted). Lesson: p50 alone can be fooled; always check the per-frame work fingerprint ([vifstat] mscal/frame or ge vu1 calls/frame) alongside it.

What the investigation did establish: frame time = EE time (~10 ms) + the non-overlapped tail of the Vif1Worker; the game syncs 4x per frame (guest ra 0x00284558) plus once at the frame swap (ra 0x0051E290), so EE and Vif1Worker only partly overlap. Reducing either thread's time still helps the frame roughly 1:1.

## 10. Dev vs release vs PGO (shop, boost): PGO reaches a locked 60 fps median
- Dev build vs release (no PGO) build, A/B rel1: frame p50 18.60 vs 18.88, Vif1Worker 14.25 vs 14.30, GsWorker 12.61 vs 12.52: NO difference. LTCG/whole-program gives nothing, so the 10-20 s dev builds are valid for every A/B (the open question from cycle 1 is closed).
- PGO (GEN link 67 s, trained by replaying the pad script and 90 s in the shop, closed normally; USE link 87 s). A/B pgo1 (dev vs PGO): frame p50 18.98 -> 16.70 (locked 60), p99 24.85 -> 24.25, [fps] 53 -> 60, same work per frame (ge vu1 calls/frame 6310 vs 6270). Vif1Worker busy wall per frame 16.5 -> 14.4 ms, EE vif1_fence wait 7.5 -> 5.7 ms/frame. Per-frame CPU columns in ab.ps1 are divided by a FIXED 60 fps, so A's 53 fps run looks cheaper than it is; true per-frame Vif1Worker CPU: A ~16.1 ms, B ~14.3 ms.
- Caveat: this PGO profile was trained ONLY on boot + shop (the replay), so the acceptance build must be retrained over shop + levels (user step). Exes: build\PS2Recomp\ps2xRuntime\ps2EntryRunner_pgo.exe (USE), _pgogen.exe (GEN), ps2EntryRunner.exe (release), _dev.exe (dev). The build folder is currently configured PS2X_PGO=USE, DEV_BUILD=OFF: tools\build_dev.bat resets to dev.
- Remaining vs the plan: p99 24 ms (target 17.5), silent mode, Part B CPU total (~41 CPU-ms/frame vs 25).

## 11. Lean dispatchGuestBranch `PS2X_DISPATCH_LEAN=1` (Task LL): KEPT (small)
ab.ps1 now uses the real fps for ms/frame (tool fix LK) and warns when A and B do different work per frame. A/B dl1 (2 rounds, dev build): GameThread 11.69 -> 11.29 ms/frame (-0.4), total 46.28 -> 45.49 CPU-ms/frame, work per frame equal (vu1/frame 6498 vs 6303, within 3%), p50 19.08 vs 19.27 (noise). True per-frame numbers at 51 fps (dev, no PGO): GameThread 11.7, Vif1Worker 16.9, GsWorker 14.4, total 46.3. Next: Task LM = default ON for lean dispatch plus PS2X_ACCT_BATCH (batching accountCycles, ~3% of EE samples).
