# Plan RTT: render-to-texture in the new renderer (GL FBOs), retire the Vulkan GS readback path
Status: PLAN 2026-11-20. Owner: Claude (spec/measure), Gemini (code). Branch: perf/rtt (from perf/overnight-risky). .cpp only, release builds.

## Why
Measured (takeover, studio_b): 8400 prims/frame go through the Vulkan GS backend, ~37 flushes/frame (each submit+fence ~0.4 ms) = ~14 ms; GsWorker 96% busy; 43 fps vs 59 in studio_a. PCSX2 keeps render targets on the GPU and samples them directly (flat 13.6 ms). Our path: draw RT in Vulkan -> download pages -> CPU decode -> GL texture. Every render-to-texture use (TV screens, and probably glow/blur/fades) pays that. Several open visual bugs are the same missing feature: transition swirl and fades (screen copied and used as texture), pause-menu frozen background, studio_e TV.
Tried and rejected (do not retry): bulk texture decode (RD73) and fast L2H (RD74) = bit-identical, no fps; async RT readback (needs PS2X_PRESENT_ASYNC, never engaged); coalescing syncs (RD76, SYNCALL: fps 43 -> 31, passes are a dependent chain).

## Current data path (facts)
- gs_frontend publish keeps only main-pass draws (filterFbp = display fbp, FEAT-RD18b/RD23); other-FBP draws are counted as rtSkipped and are rasterised by the Vulkan backend (queueDraw, ~gs_frontend 4423 "off-screen RT draws still rasterised").
- ps2xRdNoteDraw (rd_texture.cpp) asks ps2xVkSyncPagesForCpu(fpFirst,fpLast) for every textured draw whose pages are GPU-dirty (gives reason-6 flushes); fb-feedback draws (texture pages overlap display fb ranges, ps2xRdFbPageRanges) are kept via g_fbFeedbackRing (FIX-RD61/RD72) and sampled from the CPU copy.
- rd_view.cpp draws verts/batches from ring slots; textures come from ps2xRdGetTextureForBatch(serial, tex0, texa).

## Phases (one build each; every phase must keep PS2X_RD_RTT=0 == today's behaviour)
P0 MEASURE (probe, no behaviour change): per frame, list every non-display render target (frame regs: fbp, fbw, psm; zbuf; bbox from scissor; prims; draws) and every CONSUMER: textured draws whose texture pages overlap an RT written this/last frame (tex psm, tbp0 offset from the RT base, tw/th, whether CLUT/indexed, UV window), plus GS->host transfers (sbp, sbw, spsm, rrw x rrh) and GS->GS local copies (TRXDIR 2). Run on studio_b, studio_e, castle pause menu, a level transition, castle_a. Output decides P3/P4 scope: how many RTs are sampled 1:1 CT32/CT16 (easy) vs reinterpreted (T8/T4 palette tricks, hard) vs read by the EE (L2H, must stay on Vulkan).
P1 CAPTURE: stop dropping off-screen draws: publish them as an ordered "RT pass list" (per-batch frame regs, scissor, xyoffset, zbuf, ztest, alpha state, in original order, interleaved with main-pass markers). Main pass output unchanged. Memory: separate ring, bounded.
P2 GL RT MANAGER: lazily create GL texture+FBO per distinct (fbp, fbw, psm, height) with 1x PS2 resolution (optionally scaled later), shared depth renderbuffer sized to the largest; refactor the batch draw loop in rd_view.cpp into a function drawBatches(list, target) so RT passes reuse the exact 3D/2D shader state code. RT alpha stays in PS2 range semantics identical to CPU-decoded textures. Draw RT passes before the main pass each frame. Off by default (PS2X_RD_RTT=1).
P3 SAMPLE SUBSTITUTION: in the texture-for-batch lookup, when a textured draw's page range lies inside a live GL RT with a compatible psm (CT32/CT24/CT16 sampled as the same format, page-aligned offset), return an RT texture reference plus a uv offset/scale uniform instead of the CPU-decoded texture; no ps2xVkSyncPagesForCpu for those pages. Anything incompatible keeps the old path (and marks that RT "cpu-needed").
P4 CPU-NEEDED FALLBACK: RTs read by the EE (L2H), sampled with reinterpretation, or used by classic fallback stay on the Vulkan path (hysteresis per RT key). Both paths may render the same RT during a transition; the Vulkan copy is authoritative for CPU consumers.
P5 SKIP VULKAN WORK: when an RT is GL-only (no cpu-needed consumer for N frames), stop submitting its prims to the Vulkan backend (the 20 ms saving).
P6 UNLOCK + VERIFY: transition fades/swirl (screen copy as texture), pause-menu frozen background, studio_e TV; each verified with warp_shot / boot_shots and compared with PCSX2 screenshots.

## Acceptance (whole plan)
studio_b >= 57 fps with GsWorker < 8 ms; castle_a/toyhouse_a/arabian_a no regression (gate.ps1, 3 reps); screenshots of all stages vs PS2X_RD_RTT=0 within the noise floor except intended fixes; tour 148/148; no new classic fallbacks.

## Risks
Alpha/format fidelity of RTs (PS2 alpha 0..128, CT16 rounding); depth sharing and Z reuse between passes; RTs whose pages are partially overwritten by CPU uploads (hostNewer) mid-frame; mixed-psm reads (T8 on a CT32 RT) = fallback; viewport/scissor/xyoffset per RT; memory for many RTs; MSAA not needed on RTs. Each phase is switchable by env, so a bad build is reverted by turning the switch off.
