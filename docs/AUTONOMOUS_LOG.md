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

## 12. Batched accountCycles `PS2X_ACCT_BATCH=1` (Task LM): KEPT (opt-in), lean dispatch now default ON
First A/B (ac1) was VOID: the build had failed (unique_ptr vs raw pointer), both sides ran the old exe. ab.ps1 runs now only after a BUILD OK. A/B ac2 (dev, 2 rounds, lean dispatch on both sides): GameThread 11.63 -> 10.94 ms/frame (-0.69), MainLoop 1.33 -> 1.12, total 46.33 -> 44.69 CPU-ms/frame (-1.6), same work per frame (vu1/frame 6449 vs 6471), fps 52.5 both, frame p50 18.65 both. Risk: timer/IO reads that bypass PS2Runtime::LoadN/StoreN can see EE time up to 256 cycles (~1 us) stale; flush points: accountCycles itself, all special-address LoadN/StoreN. Default stays OFF until someone looks at FMV/audio.
What this tells us: EE CPU savings (-1.1 ms with lean + batch) do NOT change the dev build's frame time (52.5 fps either way): the frame is limited by the Vif1Worker (16.3 ms/frame CPU = 86% busy at 52 fps; PGO brings it to ~14.3 ms/frame and 60 fps). The earlier model 'frame = EE + tail' is wrong, the worker is the critical path. Remaining lever for p50/p99: Vif1Worker CPU per frame (VU1 native 48% of its samples: vertex kernels lbFull+lbVertex8R+lb8Op+lbFmac ~14%, hot blocks ~12%, run()/pipelines ~12%; VIF parse+unpack 16%; memmove 4%; GIF handoff ~4%). Micro-trims no longer move it; structural options: step 7 direct geometry, or GPU vertex transform (needs user approval, see plan step 10).

## 13. The tail (p99) is real, and both workers are saturated in late frames (Task LN: PS2X_FT2=1)
- [ft2] (measured where the frame is produced, gs_frontend ft2OnPresent) agrees with the main-loop [ft]: p99 22.7-24.8 vs 23.5-26.0 ms (dev build, shop, 52 fps). The tail is NOT measurement jitter.
- [hitch] lines in the shop (frames >22 ms, delta per frame): ee_wait 7-9 ms, Vif1Worker busy 16.5-19 ms, GsWorker busy 17-20 ms, present_hold 0.5 ms, one fence per frame. So heavy frames saturate BOTH workers; the GsWorker is as critical as the Vif1Worker (not only the Vif1Worker, as step 3 assumed).
- GsWorker sampling profile (dev, non-idle share): GSMem::UploadStream 13.3% (~2.9 ms/frame), GSVulkanBackend::gpuDraw 11.5%, GS::refreshDrawBatch 6.4%, GS::flushPendingDraws 5.5%, processGIFPacket 4.7% + vertexKick 4.4% + writeRegisterPacked 2.6%, pagesForRect 1.9%, vector<GSRunPrim> emplace 1.8%, memmove 1.5%, std::minmax sorting 1.1%. Next: plan step 4c (cheaper uploads) and 4d (draw merging) on the GS side.

## 14. GS upload swizzle fast path `PS2X_UPLOAD_FAST` (Tasks LO/LP/LQ/LR): KEPT, default ON (verified bit-exact)
- PS2X_UPLOAD_STAT showed where the time was: format 4 (8-bit textures) moves ~630 MB per 5 s (~2.4 MB and ~81 transfers per frame), 660 ms per 5 s window = ~2.5 ms/frame; formats 0/1/6 are small. Gemini added row-hoisted fast paths for kinds 1/5/6/7/8/10 and a table-driven 16x16-block path for T8 (StreamT8, table built from the existing PageTableP8 and self-checked at startup).
- Verification: PS2X_UPLOAD_VERIFY compares the fast result with the old code on a snapshot of the touched pages. The first version crashed (a leftover 4 MB memcpy from a buffer holding only the covered pages) and was too slow; fixed, plus PS2X_UPLOAD_VERIFY_EVERY=64 sampling. Result: 9,472 sampled verifications (~600k uploads covered), 0 mismatches, 0 whole-VRAM fallbacks.
- A/B up3 (2 rounds, dev): GsWorker 15.14 -> 13.47 ms/frame (-1.66, -11%), p99 25.18 -> 23.43, total 47.48 -> 44.41 CPU-ms/frame, fps 52.5 -> 53.5, same work/frame. kind 4: 662 -> 372 ms per 5 s window.
- PS2X_GS_BATCHPOP and PS2X_UPLOAD_FAST are now default ON (set to 0 to disable). PS2X_ACCT_BATCH stays opt-in.
- New GsWorker profile (sp2, non-idle): gpuDraw 14.1%, StreamT8Groups 7.4% (was UploadStream 13.3%), refreshDrawBatch 6.2%, vertexKick 5.9%, flushPendingDraws 5.8%, processGIFPacket 4.9%, pagesForRect 2.9%, writeRegisterPacked 2.0%, plus a 10.8% Vulkan wait. Next: per-primitive work in gpuDraw (state-only parts could be cached per run) and the Vulkan wait.

## 15. gpuDraw per-run hoisting `PS2X_GPUDRAW_RUN` (Task LT): verified exact, NO speed gain, reverted
Verify: 3.5M prims compared (state words, flags, rows, verdict), 0 mismatches. A/B gd2 (2 rounds): GsWorker 13.97 -> 14.31, Vif 16.69 -> 16.84, fps 50.8 -> 51.2: nothing (noise ~0.5). The ~45 per-prim state stores were not the cost; the profile's gpuDraw self time is geometry/page-set/vertex work. Edits reverted (git checkout). GPU waits: [vk] stats show only 137 syncs per 3840 presents (present 41, transfer 96), but ~1.8 queue submits per frame each wait on a fence (flush() = submit + vkWaitForFences, line ~1608): that is the 10.8% ZwWaitForMultipleObjects on the GsWorker (wall time, not CPU). Fixing it needs ring double-buffering (resetRings reuses prims_/clut/staging): bigger redesign, not attempted unattended.

## 16. Scheduling hints `PS2X_SCHED=1` (Task LU): no measurable effect, stays OFF
Process ABOVE_NORMAL + power-throttling opt-out + timeBeginPeriod(1), and ABOVE_NORMAL + throttling opt-out on GameThread/Vif1Worker/GsWorker. A/B sc1 (2 rounds, dev): frame p50 19.95 -> 19.52, Vif1Worker 17.09 -> 16.88, GsWorker 13.87 -> 13.96, fps 50.0 -> 50.5, [ft2] p99 24.8-25.9 vs 23.7-25.8 (noise). The tail is not OS scheduling. (Note: this session's machine state ran ~50 fps in dev vs ~53 earlier; compare only within one A/B.)

## Session end state (user returned)
See the final report in the conversation. Kept and default ON: lean dispatch, batched GS pop, upload swizzle fast path. Opt-in: PS2X_ACCT_BATCH, PS2X_SYNCPATH_*, PS2X_SCHED, PS2X_UPLOAD_VERIFY, PS2X_FT2, PS2X_UPLOAD_STAT, PS2X_SYNCPATH_LOG. Refuted and reverted: LEAN per-run trims, SIMD unpack, probe-gate hoisting, gpuDraw hoisting.

## 17. GS lean vertexKick (Task LW): KEPT, default ON; UNPACK cache (Task LX): REFUTED and removed; hoisted statics kept
- PS2X_GIFSTAT showed one dominant GIF shape: PACKED triangle strips (PRIM 0x7C), NLOOP=20, regs FOG,ST,RGBAQ,XYZ2 (80 qwords per tag): 184k tags/s (~3.7M vertices/s, ~68k vertices and ~61k triangles per frame), 1086 ns per tag = 200 of the 368 ms/s spent in GIF tag handling. PS2X_GS_LEAN: drops the per-triangle probe timers/bookkeeping in vertexKick and decodes that shape in a dedicated loop. Verified 160k tags against the generic path (0 mismatches). A/B gl2 (2 rounds): GsWorker 14.30 -> 13.11 ms/frame (-1.2, -8.3%), both rounds consistent. Default ON now.
- UNPACK setup cache: verification found 39k mismatches in 131k checks and the hit rate was only 9% (UNPACK parameters really vary per call), slower in the A/B: removed. The existing UNPACK fast path was already an SSE masked loop (vifUnpackLoop), so the earlier SIMD attempt (LF) had nothing to win. The function-local static -> namespace static hoists (vifStatOn etc., line 817 was 2.6% self time of the Vif1Worker) are kept.
- Session-to-session machine variance: the SAME all-defaults dev build ran 54.5 fps in one session and 51.5 in another. Compare only inside one ab.ps1 run.

## 18. All defaults + PGO (full cycle GEN 95 s, 2 min training at the shop, USE 87 s), dev vs PGO A/B (pgo3)
fps 55.0 -> 60.0 (locked), frame p50 18.00 -> 16.70, p99 22.10 -> 18.65 (17.8 / 19.5), GameThread 11.20 -> 9.88, Vif1Worker 15.36 -> 13.77, GsWorker 12.86 -> 11.38, total 42.55 -> 38.63 CPU-ms/frame. Part A status in boost mode, shop: median locked, p99 18.65 (target 17.5), threads: Vif1Worker 13.8 (target 12), GsWorker 11.4 (ok), GameThread 9.9 (ok). Silent mode untested (stretch 1.27-1.40x would put the Vif1Worker at 17.5-19.3 ms: fails).

## 19. Offline VU1 corpus replay found (already existed): the fast exact loop for kernel work
Command (dev exe, no gameplay, ~50 s): clear PS2X_*; set PS2X_VU1_REPLAY=1 PS2X_VU1_REPLAY_REPS=3 PS2X_VU1_KERNEL=1 PS2X_VU1_TSC=1; run build\PS2Recomp\ps2xRuntime\ps2EntryRunner_dev.exe SCUS_975.01; summary in logs\vu1replay.txt (lines 'replayed=.. MISMATCHED=.. | vf vi acc qpi flags pc cycles workingClip misc mem gif', 'run_ms=.. calls=..', 'kernels (calls taken / ms): vertex= copy= skinFull=', 'run_ms = kernels + hot blocks + slow pairs'). Corpus logs\vu1corpus.bin (578 MB). Baseline (all defaults, dev, before LY): replayed=29999 MISMATCHED=0, run_ms=213.17 (3 reps), kernels 59.49 (skinFull 24.58 ms / 33,867 calls = 0.73 us, vertex 29.54, copy 5.36), hot blocks 111.54, slow pairs 42.71. Image hashes in the corpus: d6b2281aa7efd05a (the shop image) and 86503d39..., 4279fa21....
Vif1Worker profile of the PGO exe (sp3, inclusive): vu1NativeRun 48.3% (lbFull 16.0: lbVertex8R 8.0, lbVert 5.2), flushPipelines 9.4% (finishXgkick 8.3: GIF handoff submit 2.2, drain 2.5, gsFlushPending 1.9), resetScheduler 3.1% self (memset of 2.4 KB per run: members live in ps2_vu1.h, a lazy scheme needs either a header change = full rebuild, or touching all writer sites), memmove 2.6% (the GIF packet is copied twice: VU memory -> m_xgkick.packet -> arbiter vector; zero-copy needs header changes), UNPACK lambda 8.0%. Explorer analysis of lbFull (lb8N on 16 inputs ~140 ops, per-vertex commit loop ~65-75 SSE ops/vertex, gather addressing) -> Task LY.

## 20. Final PGO measurement (pgo5, same exe on both sides, 3 rounds each)
fps 59.7-59.8, p50 16.70, p99 20.5-21.3 (single runs 19.8-21.6; the earlier pgo3 had 17.8 and 19.5, so p99 varies by 2 ms between sessions), Vif1Worker 13.62-13.70, GsWorker 11.48-11.65, GameThread 10.26-10.33, total 38.96-39.27 CPU-ms/frame. LB2 default ON verified: replay MISMATCHED=0 (29,999 runs), shop screenshot correct with all defaults. See docs/STATUS_2026-11-10.md for the summary and the remaining options.

## 21. Vulkan ring capacities (Tasks MA/MB, 2026-11-12): mid-frame GPU waits removed
Diagnosis: GsWorker 10.7% of wall time in vkWaitForFences inside flush(); the present path was already async, the waits came from the prim ring overflowing (24576 prims; shop draws 35-61k/frame). MA added `flushwhy[prims/clut/staging/other]` to the [vk] line and env PS2X_VK_MAXPRIMS / PS2X_VK_MAXCLUT.
A/B mp1 (dev exe, 2 rounds, slow machine state ~49.5 fps both sides): default flushwhy=2071/0/0/0, sync_ms 4845, barriers 2310; with 131072/8192: flushwhy=0/0/0/0, sync_ms 86, barriers 802. fps/p50 unchanged (19.85 vs 19.75 ms, noise 0.3): the Vif1Worker (17.2 ms) limits, fence waits are not CPU time. GsWorker CPU -0.3 ms (noise level). Screenshot shot_mp1_1.png correct.
Kept: MB makes 131072/8192 the default (old sizes via env PS2X_VK_MAXPRIMS=24576 PS2X_VK_MAXCLUT=2048). Cost: +2x(32+6) MB host-visible memory. Gain: ~1.5 ms of GsWorker wall time per frame freed (headroom once the Vif1Worker drops).

## 22. Prim record staging (Tasks MC/MD, 2026-11-12): GsWorker -24%
Cause: prims_ is HOST_VISIBLE|COHERENT without CACHED (write-combined); gpuDraw did a 320-byte memset plus ~70 scattered out-of-order 4-byte stores per prim straight into it. MC builds the record in an aligned stack buffer and memcpys it once at commit (same bytes).
A/B mc1 (dev exe, 3 rounds): GsWorker 14.41 -> 10.89 CPU-ms/frame (-3.5 ms, every round), Vif1Worker 17.43 -> 17.01, total 47.6 -> 43.5. fps/p50 unchanged (Vif1Worker limits). Pictures shot_mc1_1 / shot_md1_1 correct.
Kept: MD makes it default ON (PS2X_VK_PRIMSTAGE=0 disables). Other mapped buffers checked: only bulk sequential memcpys or CACHED memory, nothing else to fix.
Next: item 3, direct geometry on the Vif1Worker (now the only worker above 12 ms).

## 23. GIF packet coalescing (PERF-MF, 2026-11-12, coded by Claude under the temporary coding grant): Vif1Worker -1.25, GsWorker -1.75 ms
Measurement first (PS2X_VU1_TSC + VIFSTAT, per frame at ~47.5 fps): VU1 kernel loop ~10.2 ms, epilogue ~1.7, submit ~1.4, VIF unpack ~2.9, DIRECT + other parse ~2. ~6400 XGKICKs/frame; per-packet overhead (pooled vector, queue entry, GS call with lock + draw flush) dominated, not bytes. So direct geometry's Vif1 gain (hand-off only, ~2-2.5 ms) is mostly per-packet cost: attacked that first.
Change (gs/ps2_gif_arbiter.cpp only): in VIF1 batch mode, PATH1 and whole PATH2 packets are appended to one 64 KB buffer instead of one vector each. Safe because GS::processGIFPacket walks tags to the end of its buffer with no per-call state except the native image-upload shape checked at buffer start; packets are only appended when their tags cover them exactly, never IMAGE tags, never that image shape; the open buffer is sealed before any other packet and on every flush. Probe: 94% coalesced (rest: PATH2 fragments/images).
A/B mf2 (3 rounds): Vif1Worker 17.68 -> 16.43, GsWorker 11.11 -> 9.36, p50 20.03 -> 18.95, fps 49.2 -> 52.0, vu1/f +0.2% (same work). GS queue packets 2.83M -> 1.25M per interval with PATH1-only coalescing (mf1); not re-measured after adding PATH2. Pictures shot_mf3/mf4 correct. Default ON (PS2X_GIF_COALESCE=0 disables).

## 24. New target: locked 60 in SILENT power mode (user, 2026-11-12). Silent baseline (silent0, dev exe, same exe both sides, 2 rounds)
fps 41, p50 24.0 ms, p99 ~30-32, Vif1Worker 21.4, GsWorker 11.8, GameThread 14.4, total ~52 CPU-ms/frame. Every thread must reach <= ~14 ms (silent) for 60 with headroom: Vif1Worker needs about -35%.
Plan: VIF1 two-stage pipeline (parser || VU1 exec, exact by event ordering; Tasks MG1/MG2), then VU1 math, then PGO retrain. Risky changes listed in docs/REVERSAL_MEMO.md.

## 25. VIF1 two-stage pipeline (Tasks MG1/MG2 by Gemini + small fixes by Claude): silent fps 39.3 -> 43.0
Design: processVIF1Data (one call ~ one frame) turns VIF codes into an ordered SPSC event stream (VU writes as lane-masked records, MSCAL/MSCNT, DIRECT packets); a new Vu1Exec thread applies them in order. The parser never touches VU memory / VU1 state / GIF while the pipeline is on, so results equal sequential execution; end-of-job drain keeps every outside contract. Sync points (drain, then old code): MPG, MSKPATH3, wrapping/unknown-format UNPACK, end of job.
Claude fixes: seq_cst on ring/flag atomics (Dekker lost-wakeup on the sleep path), and DIRECT image chunks queued as owned packets instead of a drain each (probe PS2X_VIF1_PIPE_STAT=1: 200 drains/frame -> 1).
A/B mg5 (SILENT, 3 rounds): fps 39.3 -> 43.0, p50 25.08 -> 22.73, p99 31.5 -> 29.7; Vif1Worker (now parser) 22.2 -> 11.5 CPU-ms, Vu1Exec ~20.6 (in "other"; ~15% of it spinning). Pictures shot_mg2 / mg5 correct. Default ON.
Now limiting: Vu1Exec (VU1 programs + XGKICK + DIRECT + record apply) ~21 ms/frame silent.

## 26. Where the silent-mode frame goes now (dev + PGO, 2026-11-12)
PGO retrained with the pipeline (tools\pgo_cycle.ps1: GEN 137 s, 90 s shop training, normal close, USE 125 s). A/B pgo6 (silent): PGO cuts CPU/frame on every thread (EE 16.2 -> 14.6, parser 11.3 -> 8.2, Gs 12.2 -> 10.9, Vu1Exec 20.4 -> 18.6, total -12%) but fps 43.0 -> 41.8 with +4.4% VU work per frame in B (not a clean comparison).
[wait] line: the EE waits in the VIF1 fence 28% (dev) / 36% (PGO) of the time; the worker is idle 14% / 27%. Frame = EE work + exposed wait for the VIF job at the game's syncs (VIF1_STAT/GIF_STAT polls from guest 0x2843D4 and sceGsSyncPath; both are real semantics, see section 9). So EE time and VIF job latency are both on the critical path.
Vu1Exec profile: native VU1 kernels ~58% (lbFull 19, lbVertex8R 11), per-run interpreter overhead ~19%, GIF submit ~8%, record apply ~3%, ring wait ~12%. EE profile (70% busy): VU0 microprograms 17% ([jm] probe: ~4400 calls/frame, ~670 ns each, 1/3 fixed overhead), sceDmaSend chain gather 14% (payload copy ~1.8 ms/frame silent).
Next: Task MH defers the RDRAM payload copy from the EE to the Vif1Worker (parser has ~9 ms slack).

## 27. Pipeline tuning and two refuted ideas (silent)
- Parser profile: vpPushRec was ~35% of parser CPU (a seq_cst store + head reload per record; the record volume is ~10x the UNPACK count). Relaxed tail + cached head: parser ~9.8 CPU-ms (was 11.5). Kept.
- Smaller rings (16K/64K records, 8K events): constant "full" waits, parser CPU up to 17 ms, no fps gain. Reverted to 64K/256K.
- Task MH (defer the VIF1 DMA RDRAM copy from the EE to the worker, PS2X_VIF1_DEFER): REFUTED, A/B mh3 fps 42.7 -> 40.8, p50 +1.1 ms, EE CPU unchanged. As predicted by the timing chain (frame ~ EE pre-kick work + job latency), the copy just moved inside the job. Code reverted (not committed).
- Spin count (PS2X_VPIPE_SPIN 4000 vs 200): no difference (A/B sp1). Default 4000.
- VU1 phase timers with the pipeline (silent, per frame): VU1 run ~17 ms = kernels ~8.4 + hot blocks ~6.3 + epilogue ~1.7 + prologue ~0.6. Vu1Exec total ~20 incl. record apply / DIRECT / events. VU1 compute alone exceeds the silent budget: next is the register-independence experiment (Task MI) to see if MSCAL programs can run on two threads.

## 28. VU1 programs do not depend on inherited registers (Task MI, replay scramble, 29,999 calls)
PS2X_VU1_REPLAY_SCRAMBLE: garbage in vf[1..31] (mask 1), vi[1..15] (mask 2) or acc/q/p/i (mask 4) at entry -> output differences (VU memory + GIF bytes) 0 of 29,999 for every mask. All MSCALs enter at 0x0008 (28,751) or 0x0040 (1,248). Exit registers differ (expected) but no program reads them. So a program's output is a function of VU memory (+ top/itop, flags not tested). Next: Task MJ tests whether program k+1 reads memory written by program k (consecutive shop capture + replay pair mode). If not, MSCALs can run on two exec threads.

## 29. VU1 program-to-program dependencies, shop (Task MJ + Claude probe extensions), 8,000 consecutive captured calls
Capture: PS2X_VU1_CAPTURE=1 EVERY=1 MAX=8000 DELAY_SEC=160 CORPUS=logs\vu1corpus_shop.bin (+ logs\vu1corpus_serial.bin); plain replay exact (0 mismatches).
- Pair mode 1 (revert program k's writes before k+1): 4,862 of 7,999 differ; culprit search (300 pairs, one qword at a time): ONLY qword 1023.
- qword 1023 = output-buffer toggle: words 2/3 swap between 0x179 and 0x94 (buffer bases 377 / 148). 66% of programs swap it, the rest leave it.
- Mode 2 (revert all earlier program writes except 1023): 5,236 GIF diffs, culprits only qwords 636-715. Mode 1 with 1023 kept: 189 GIF diffs (2.4%), culprits 716-795. So the cross-program state is exactly: toggle (1023) + a double-buffered 80-qword table (636-715 / 716-795, written by "palette writer" programs, 11% of calls, ~545 cycles, no GIF output). Output-buffer leftovers never matter.
- Structure per object: writer -> 1-2 small header programs (30/55 cycles) -> ~9 vertex batches (545 cycles, 1296 GIF bytes, swap toggle); median object 4,237 VU cycles.
- Predictability (python over the capture): header word 1 of the input batch at TOP predicts "swaps toggle" with 100% accuracy (28 distinct values); the full first qword predicts "palette writer" 100%. "same as previous" is only 79.6%.
Consequence: an exact two-thread VU1 executor is possible: alternate MSCALs, per-thread VU memory copies (VIF writes to both), forward toggle + palette (161 qwords) in program order, predict the toggle from the header type table, serialize after predicted palette writers, verify after each run and re-run on a surprise. Fallback to sequential for unknown header types / other code images.

- Scramble mask 8 (MAC/STATUS/CLIP incl. clip history) and mask 15 (everything) on the shop corpus: outdiff 0 of 8000 both. Plan written: docs/VU1_DUAL_PLAN.md; Task DA (thread-safety audit for two VU1 instances) sent to Gemini.


## 30. Task DB1: dual executor infrastructure (default off, PS2X_VU1_DUAL=1)
- Gemini added thread Vu1Exec2 (mirrors VIF writes into a shadow VU1 copy, own ring cursors), second VU1 instance s_vu1B + g_vu1MscalCallbackB, ps2_vu1_set_capture, ordered PATH1 submit of captured XGKICK output on X0. Small fix by me: the extern of g_vu1MscalCallbackB was inside the anonymous namespace (would not link once used).
- Shop, silent: picture correct (logs\shot_db1_1.png), MSCNT=0, X1 mirroring 235 ms vs X0 busy 1632 ms per stat window.
- A/B db1 (3 rounds, B = DUAL=1): fps 45.0 -> 42.7, p50 21.80 -> 22.87, Vif1 9.64 -> 13.74 ms. Expected cost of capture+ordered submit with no parallel run yet; DB2 must pay it back. Next: Task DB2 (X1 runs odd MSCALs, predicted W + verify/rerun).

## 31. Task DB2 + DB2b: dual executor runs odd MSCALs on X1 (PS2X_VU1_DUAL=1, default off) - BROKEN, not usable yet
- DB2 timed out in Gemini after writing ~2/3 (slots, prediction table, vpRunMscal run/verify/rerun, ordered GIF turns, drain reset); DB2b finished it (parser k/t numbering, MSCNT pre-drain, X1 runs vpRunMscal(ev,1)).
- Shop, DUAL=1 (logs\shot_db2_2.png): 3D geometry missing (only sky, HUD, 2D labels), ~25 fps. Stats per window: x1_runs ~180k, spec ~180k, reruns=0, waits_exact ~70k, exec_busy 1732 ms vs x1_busy 1713 ms (work is split evenly), drainwait 1178 ms (doubled).
- DUAL off (logs\shot_db2off_1.png): picture correct, 40 fps (single sample), so the default path is unaffected.
- reruns=0 with all 3D gone means the error is not the W prediction. Suspects for next session: (1) per-submit ps2_gs_async_batch(false/true) from two threads + thread_local GIF coalescing (PERF-MF t_gsCoalesce) and PATH arbitration when PATH1 is submitted from Vu1Exec2; (2) VU1 state on the second instance that the scramble test did not cover (s_vu1B is never told about anything m_vu1 gets outside the MSCAL callback); (3) X1 output order. First check: run DUAL=1 with X1 forced to run nothing but its own capture submitted by X0 (or PS2X_GIF_COALESCE=0) to split GIF-path vs VU-state causes.
- Cost even if fixed: per-program GS flush and turn waits; fps target needs a cheaper ordering (per-turn capture buffers submitted in order by one thread).

## 32. Where the time goes after the PCSX2 50%-EE test (silent, dev exe)
- User test: PCSX2 at EE cycle rate 50% holds 60 fps in the shop (silent mode) => the game's EE work per frame is < half a real EE frame; we spend ~14 ms EE CPU on it.
- EE thread sampler (logs\shot_eeprof.err, sampler on => ~30 fps): ~38% of EE samples asleep in ps2_vif1_fence (readIORegister of VIF/GIF status = waiting for the VU1 job), the rest is flat guest code + glue (dispatchGuestBranch 3-4%, writeIORegister 3%, VU0 run 3%, _NLG_Return2 5% unresolved). Earlier P350: VU0 calls ~25% of EE active, glue ~15%.
- So the frame = EE work + waiting for VU1. Real hardware waits little because its VU1 is fast; our VU1 is the frame limiter.
- Live VU1 split (PS2X_VU1_TSC, per second): loop 565 ms (hot blocks 243, native kernels ~320), epilogue 61, submit 40, prologue 20; 0 slow pairs live.
- Shop corpus replay with kernels: 8000 calls, MISMATCHED=0, 2.23 us/call (no GS submit).
- PS2X_VU1_FAST=1: INVALID (vu1/frame 6377 -> 333, rendering broken), not a lever.
- DB2 with PS2X_GIF_COALESCE=0: still no 3D => not the coalescing. Next: Task DC verify mode (X0 does all work, X1 recomputes odd programs and compares GIF + W).

## 33. Dual executor root cause found (Tasks DC/DC2 verify mode by Gemini + PROBE-DC3 by Claude)
- PS2X_VU1_DUAL_VERIFY=1: X0 does all real work (picture correct, logs\shot_dc_1.png), X1 recomputes odd programs on the shadow copy with exact W from slot(k-1) and compares. Result: GIF differs in ~42% of programs, W in ~3%.
- DC2 entry-memory compare: EVERY X1 program starts from a different memory: constants 994-1000/1010-1016 (matrices/constants written by the small header programs) and old output-buffer qwords 149-177 / 394-446. So section 29's 'only W crosses programs' does NOT hold live: header programs pass constants to the following vertex batches.
- PROBE-DC3 (PS2X_VU1_DUAL_VERIFY_SYNC=1: X1 starts from X0's exact 16 KB entry memory): gifMismatch 0-1 per ~95k programs, wMismatch 0. => the second VU1 instance is correct; only the memory forwarding is wrong.
- Next: Task DB3: forward each program's full write set (diff vs its entry snapshot) instead of the fixed W, speculate only when the predecessor is a 'kick-only' writer (writes only 1023 + its own XGKICK source range), verify and rerun otherwise.

## 34. Task DB3 (Gemini) + PROBE-DB3H / PERF-DB3P (Sonnet subagent): exact dual executor works, but is SLOWER - PARKED (default off)
- DB3: each program publishes its full write set (diff vs a 16 KB entry snapshot); the other thread applies it (skipping qwords VIF wrote since); speculation only after 'kick-only' predecessors (writes only 1023 + own XGKICK range), verify + rerun.
- PS2X_VU1_DUAL=1 shop: picture CORRECT (logs\shot_db3_2.png, logs\shot_db3p_1.png) but 19-21 fps vs ~41 single.
- Non-kick writes (PROBE-DB3H): 31% of programs; hottest qword 1018 (43.6k programs/window) and the table 636-650 (~23-28k). Majority predictor (PERF-DB3P, kick-only if >=75% of observations): spec 31k of 140k X1 runs, reruns ~500, waits_exact ~224k: nearly every program still waits for its predecessor.
- Cost: each thread ~1856 ms busy per window vs 1632 for the single executor in DB1, drain wait 1427 vs 573 ms: snapshot/diff/apply + per-program GS flush + turn waits outweigh the parallel part.
- Conclusion: program-level parallelism is blocked by real program-to-program dependencies (1018 + table + constants) and per-program sync cost. Parked behind PS2X_VU1_DUAL (default off). The VU1 time has to come down per program (decompiled/HLE kernels, per-call overhead), not by splitting.

## 35. Vu1Exec profile (silent, dev, PS2X_PROF_VU1EXEC, logs\shot_vxprof.err)
- Idle 18.8% (waiting for events): the VU1 thread is NOT saturated; the frame is a latency chain EE -> parser -> Vu1Exec -> EE fence wait.
- Inclusive: execute 69.6%, vu1NativeRun 55.8%, lbFull (skinning) 16.4% (lbVertex8R 8.8), lbVert 4.2, lbCopy 1.8; submitGifPacket 7.2 (GifArbiter::submit 4.4, coalesce insert 1.2, assign 1.5), flushPipelines 6.8 (finishXgkick 4.2, progressXgkick 2.6), resetScheduler 1.9, std::function layers ~2.
- Single hottest hot block: vuH_14 (pc 0158, 6-pair 4x4 matrix MUL/MADD loop with LQ/LQI/SQI) 4.9%.
- Per-call overhead live: prologue 20 + epilogue 61 + submit 40 ms/s at ~107k calls/s = ~1.1 us per call (~15% of busy).
- Every single item is <= 5% of the thread except skinning; 60 fps needs ~-8 ms of VU1 latency per frame => whole-program decompiled kernels remain the only lever of that size.

## 36. PGO retrain (pgo7) and the frame's critical path (PROBE-TL, Sonnet subagent)
- pgo7 (silent, 3 rounds, dev vs PGO exe): CPU/frame -10.6% (EE 14.97->13.59, Vif1 9.27->7.31, Gs 11.59->10.55) but fps 44.0 -> 43.0 (noise). [wait]: EE fence wait per frame 7.4 (dev) -> 9.1 ms (PGO): the job ends at the same time.
- PROBE-TL (PS2X_TL=1, ps2_memory.cpp) shop steady window: 1 VIF job per frame, queue wait 0.02 ms, job duration 20.3 ms (max 31), the EE kicks it 12.0 ms before it starts waiting and waits 8.4 ms. Frame ~25 ms = EE pre-kick work (~4.6 ms) + job duration (20.3 ms).
- => The frame is (EE time until the kick) + (VU1 job latency). Job latency = the Vu1Exec work of the frame. 60 fps needs job <= ~12 ms (and EE total 16.6 ms -> lower too, it is right at the limit). CPU savings off this chain (GS, parser, EE after the kick) cannot raise fps.
- Priorities: (1) VU1 per-program cost (decompiled kernels), (2) EE pre-kick work, (3) EE total.

## 37. VU1 program map, live (PROBE-PC, PS2X_VU1_PCPROF=1, Sonnet subagent; shop, silent, 5 s window, logs\shot_pcp.err)
- Native-run time ~497 ms/s (~12 ms/frame of the ~20 ms job; the rest = per-call overhead, record apply, submit). 0 slow pairs.
- By unit start pc: skinning 1FE0 753.6 ms (1.05 us/call) + tails 1EE0/1EF8/1F68/1F78 ~95 => ~34%; dispatcher pcs 0000/0008/0028/0050/0070/0088/0090/00A8/0188 ~544 ms (~22%, 0028 alone 3.3M entries/5 s, i.e. per-block dispatch overhead); vertex/clip machine 2440 + 24F0/24F8/25B8/2C78/2CB8/2D50/2DB8/2DD8/2DE0/2E18/2E40/2E88/2E98/2EF8 ~540 ms (~22%); matrix loop 0158 234.8 ms (~9.5%); copy 0C80 81.8 ms; 16C0 53.6; 1C90 19.5.
- Decompile order (VU1_DECOMPILE_PLAN): replay harness in functional mode first, then dispatcher + skinning (together ~56%), then the clip machine, then 0158.

## 38. VU1 handler inventory (PROBE-HI, Sonnet; shop, 5 s window, logs\shot_hi.err) + full image disassembly (docs\vu1_image_86503d39.txt)
- Handlers (inclusive): 1EE0 1761 ms/770k (~70% of VU1 native time: skinned-mesh pipeline = 1FE0 skin + 2440 vertex/clip + 2900+ clipping), 00A8 281 ms/129k (matrix setup + 0158 loop), 0C80 84 ms/1.1M (copy), 15E0 59 ms/14k, 0088 45/241k, 0050 43/241k, 0070 38/750k, 1C48 22/13k, 0B40 7.7/1.1k, 3160 0.7/449.
- Programs per signature (handler set): {70,C80,1EE0} 63%, {50,88,C80} 11%, {A8,C80} 11%, {50,88} 9%, {C80} 1.8%, {C80,1EE0} 1.7%, {15E0} 1.2%, {70,C80,1C48,1EE0} 1.0%, {70,B40,C80,1C48,1EE0} 0.1%, {C80,1EE0,3160} 0.04%.
- => Functional engine scope: dispatcher + 0050/0070/0088/0C80/00A8 + 1EE0 covers ~96% of programs and ~95% of time; then 15E0, 1C48, 0B40, 3160 for ~100%.

## 39. Task F1: functional VU1 engine skeleton (Sonnet subagent; PS2X_VU1_FUNC=1, default off)
- vu/vu1_func.inc (included by ps2_vu1_core.cpp): whole-program functional run for image 86503d39 (startPC 0008): dispatcher + handlers 0000/0050/0060/0070/0088/0C80/00A8 (00A8 via the verified closed forms, fmacV mirrors lbFmac), immediate XGKICK snapshots, undo log for fallback (no 16 KB snapshot), exact path on any unknown handler.
- Replay harness PS2X_VU1_REPLAY_FUNC=1 (mismatch = mem/gif only), shop corpus: taken 2494 / fallback 5506 (1EE0 5175, startPC!=8 184, 15E0 74, 1C48 64, 0B40 6, 3160 3), mem=0 gif=0.
- Live (logs\shot_f1_2.png): picture correct, ~36% of programs functional. A/B f1 (2 rounds): fps 45.0 vs 44.8 (neutral: covered handlers are cheap ones). A first-command skip memo lost good programs -> behind PS2X_VU1_FUNC_MEMO (off).
- Next: Task F2 = functional 1EE0 (skinned 1FE0 path from lbFull, rigid 2440 path from lbVert), docs\NEXT_TASK_F2.md.

## 40. Task F2: functional 1EE0 (Sonnet subagent) - EXACT, 92% of programs functional, but SLOWER (scalar port)
- vu1_func.inc: handler1EE0 (prologue closed form, vi12 kept as live state), skinned 1FE0 path ported 1:1 from the SCALAR lbVertex chain + lbFull commit layout, rigid 2440 path ported from lbVert (paths A/B/C, trivial-reject masks, 1022.x write, epilogue with 1023 swap + XGKICK). Falls back: 1EF0 entry, real clipping, N out of range, DIV by 0, aliasing guards.
- Replay (shop corpus): taken 7597 / fallback 402 (startPC!=8 184, 15E0 74, 1EE0 71, 1C48 64), mem=0 gif=0.
- Live: picture correct (logs\shot_f2_1.png), [vfunc] taken 92%.
- A/B f2b (3 rounds, silent, AC power; the first run f2 was on battery and agreed): fps 42.0 -> 38.8, p50 23.33 -> 25.40: slower than the exact native kernels, because the skinned path uses the scalar lbVertex instead of the 8-wide lbVertex8R kernel and the rigid path is scalar.
- Next: vectorise the functional vertex math (8 vertices per step like lbVertex8/8R with exact per-group fallback), then per-call overhead, then 15E0/1C48/clipping.

## 41. PERF-F2Z: zero-operand lanes skip the exact slow path in fmacV (Sonnet)
- Profile of the functional engine (logs\shot_f2prof.err): fmacV's per-lane double re-classification dominated because lanes with an exactly-zero operand always fail the exponent window. Zero-operand lanes now use the IEEE result (identical: signed zero / ac + 0), signbit via raw bits.
- Replay: mem=0 gif=0, taken 7597, run_ms 23.41 -> 18.58.
- A/B f2z (3 rounds, silent, AC): fps 42.2 -> 43.7, p50 23.17 -> 22.42 with PS2X_VU1_FUNC=1. First net win of the functional engine.

## 42. PERF-F2W: 8-wide AVX2 skinned path in the functional engine (Sonnet; ported lbVertex8 + exactness guard, scalar fallback per group)
- Replay: mem=0 gif=0, taken 7597, run_ms 18.58 -> 15.34 (1.92 us/call).
- A/B f2w (3 rounds, silent, AC): fps 40.7 -> 46.3 (+14%), p50 23.00 -> 21.42 with PS2X_VU1_FUNC=1.

## 43. Functional engine per-call overhead (Sonnet): one GIF submit per program, hook before resetScheduler/state init, skinned output span logged once
- Replay: mem=0 gif=0, taken 7597. Live picture correct (logs\shot_f2o_1.png).
- A/B f2o (3 rounds, silent, AC): fps 41.8 -> 51.7 (+24%), p50 23.17 -> 18.67 with PS2X_VU1_FUNC=1.
- Diagnostic modes (probe_ae, movie HLE verify, VU1 verify, replay/capture) keep the old hook order.

## 44. Functional VU1 engine DEFAULT ON (PS2X_VU1_FUNC=0 reverts; REVERSAL_MEMO)
- Exactness (replay PS2X_VU1_REPLAY_FUNC=1, mem/gif): shop corpus 7597/8000 taken, early-run capture (vu1corpus.bin, 20 s) 6598/8000, snow corpus 4895/5956, all mem=0 gif=0.
- Default build without env (logs\shot_fdef_1.png): picture correct, 51 fps in the shop (silent). Live fallbacks: 15E0, 1C48, 1EE0 (real clipping), 0B40, 3160, 0AF0, 1900, 1EF0; no non-0008 starts live.
- Roles from now: coding by Gemini 4 Hydrogen (Medium) via antigravity, Sonnet for quick fixes, Haiku for reading.

## 45. Critical path after functional VU1 (PROBE-TL, silent, default build): frame ~19.5 ms, VIF job 15.2 ms (was 20.3), EE fence wait 2.9 ms (was 8.4), EE work ~16.6 ms/frame => the EE is now the main limiter. Vu1Exec 20.6% idle; its top items: handler00A8 8.7%, GIF submit ~11%, fmacV ~6%. Next: VU0 microprogram inventory (Task V0A, Gemini 4 Hydrogen Medium) to decompile the hot VU0 programs the same way.

## 46. VU0 inventory (Task V0A by Gemini 4 Hydrogen Medium, PROBE-V0A PS2X_VU0_PCPROF=1; shop, 5 s): ~1.07M VU0 calls, ~745 ms (~3 ms/frame, ~18% of EE work). Image d985722524327b89 (docs\vu0_image_d9857225.txt). Top: 0x088 258 ms/460k (~560 ns), 0xCD0 253 ms/440k (~580 ns), 0x000 80/66k, 0x0F0 67/43k, 0x4B0 45/35k, 0x348 40/33k. 0x088 and 0xCD0 are 12-pair straight-line FMAC programs (scale + two 4x4 matrix multiplies): ~95% of their cost is per-call overhead of the generic execute path. Next: Task V0B fast path for straight-line VU0 programs with an exact check mode.

## 47. Task V0B (Gemini 4 Hydrogen Medium, ~4 min): fast path for straight-line VU0 FMAC programs (vu/vu0_fast.inc, hook in PS2Runtime::executeVU0Microprogram), PS2X_VU0_FAST=1 default off
- Check mode PS2X_VU0_FAST_CHECK=1 (fast on a copy vs normal path, every architectural field incl. MAC/STATUS/CLIP/pc/tpc/vpu_stat): 12.95M calls, 92% fast, 0 mismatches.
- A/B v0b (3 rounds, silent, AC): p50 19.00 -> 18.63 (-1.9%), fps 51.3 -> 51.7; EE busy column unchanged within noise (saved time partly becomes wait). Exact; candidate for default ON after one more scene check.
- Hydrogen notes: both tasks (V0A probe, V0B fast path) compiled first time and were correct; ~2.5 and ~4 min per job.
