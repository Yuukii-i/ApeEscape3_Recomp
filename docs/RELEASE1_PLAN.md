# Release 1 plan: "the game is playable start to finish" (started 2026-11-23)
Scope decided by the user: playability only. Frame interpolation is PARKED (geometry goes crazy in motion; see FG_RUN_LOG.md). Enhanced renderer, lighting, god rays, Android/Linux are out of scope for release 1.

## Blockers known today
| id | symptom | what we know | first step |
|---|---|---|---|
| B1 | Blur pulse at castle fly-by (our port only; PCSX2 and two longplays have none) | our build triggers the game's own blend-previous-frame effect, FIX ramp 0x09..0x40; builder is runtime-computed, not input related; PCSX2 savestate slot 5 sits at the exact moment | compare the EE-side state that decides the effect (a flag/timer/RNG-like value) between PCSX2 slot 5 and our run |
| B2 | Random mesh explosions on objects tied to physics (e.g. bunny-costume monkey ears spike then recover) | earlier VU0/FPU fixes (flags, sqrt.s ft, RTZ) cured gameplay explosions; monkey capture still open | catch one explosion with a deterministic repro and diff the VU0/EE inputs against PCSX2 |
| B3 | Ninja rope glitch | not investigated yet | needs a repro location |
| B4 | Anything else that stops completion (softlocks, crashes, missing triggers, bad level load) | warp tour exists (docs/WARP_TOUR.md); crash fixes done 2026-11-16 | play-through route per stage + crash/softlock log |
| B5 | Transitions end early, music speeds up in transitions | load-time emulation added (FEAT-E8c, vblank host lock FIX-E8d); still early | PCSX2 stopwatch of a fade vs ours |
| B6 | Hub pale panorama rectangle and tree haze, pause-menu ball dark | open since 2026-11-22/23 | cosmetic, after B1-B4 |

## Method
Real-game-first: PCSX2 is the oracle for every blocker (register/memory state at the same guest address). Batch breakpoints, no memory watchpoints (they froze PCSX2 twice). Gemini 4 Hydrogen (Medium) writes all repo code from specs in docs/tasks/; Claude builds/runs/judges. Every fix env-free (no hacks), logged in docs/HYPOTHESES.md.

## Needed from the user (repro data)
1. B2: stage + object where explosions happen most (and whether they appear in PCSX2 never/rarely).
2. B3: stage and what the rope does wrong (visual, stuck, can't swing, crash).
3. Any other place where you could not continue or the game crashed.
4. A savestate or padrec near each case is ideal.

## B1 findings (2026-11-23, video refs/castle_blur.mp4, 30 fps, frames cropped in refs/game/)
- Blur is a heavy radial/zoom smear of the castle on video frames 301-305 (~0.17 s), clean from 307; it follows a title->castle crossfade (295-299). Reproduced by logs/castle_blur.padrec (fast load timing).
- The game itself builds the blur: a quad of +-1.2 floats (zoomed copy) at EE 0xa4c9b0/0xa4ebb0/0xa4eeb0, blend FIX ramp 0x09 0x18 0x24 0x2e 0x36 0x3c 0x3f 0x40 0x3f 0x3c 0x36 0x2e ... (smooth up/down). The same quad packet exists in PCSX2 slot 5 at 0xa4c9b0.
- Not yet known: whether PCSX2 draws the same ramp (invisible) or skips it; what texture/FB the quad samples in ours (stale previous-frame snapshot suspected: ps2xRdGetPrevFrame/FIX-RD80).
- Also seen in the video: briefing tunnel has black/grey tiles where blue is expected; video duplicate-frame stalls (about 1 s frozen at frames 269-289 in the title->castle load = our load stall, not blur).

## B1 update (real-load-timing recording logs/castle_real.padrec; PCSX2 video refs/castle_blur_ps2.mp4)
- PCSX2: briefing tunnel -> dark dip -> fully WHITE hold ~2.8 s (the load) -> castle fades in from white; castle sharp in every frame.
- Ours (real load timing, replay reaches gameplay): tunnel washes to grey (~80% white) for ~1 frame at 4 fps sampling, then the DARK tunnel returns for ~2.3 s (load), then castle crossfade with blur. So the white hold is missing: the tunnel keeps being published as real 3D frames (k0 n=29-45k, keptPrev~0, keepCapped=0 => NOT the keep-previous rule).
- Blur ramp (game, PS2X_BLURPKT) occurs in two clusters per run: one BEFORE the castle load (briefing), one after the last DVD read; each = big pulse 0x09..0x40..0x00 then small pulse 0x04..0x1a..0x04.
- Blend census (PS2X_RD_BLENDLOG=1): nothing skipped (skip=none). Suspect full-screen untextured sprites prim=006 with ALPHA=1 (reverse lerp, vertex alpha) reported blend=0 => possibly drawn without the intended blend. Unverified.
- Argon (second opinion, analysis only): bell ramp cannot be a one-way fade; alternatives H1 frozen scratch buffer TBP != live FBP, H2 snapshot misses the white pass, H3 pulse belongs to white hold and fast-load collides. Wants per-frame log of FBP/TBP0/ALPHA/3D-draw-count for the zoom quad.
- NEXT: PCSX2 GS dump (Shift+F8) at the white hold and at the dark dip just before it; parse draw list with scratchpad gsdump_draws.py; compare with our census.

## B1 GS-dump facts (PCSX2 dumps refs/pcsx2_dumps/ref_dark_dip, ref_white_hold, ref_after_white_hold; parsed with scratchpad gsdump_draws.py)
- WHITE HOLD: 4 frames, ZERO draws, zero uploads. Real HW submits nothing during the load; the GS keeps scanning out the last framebuffer (white).
- FADE = the LAST draw of every frame: full-screen untextured SPRITE (512x448), ALPHA=0x44, vertex white 0xffffff, vertex alpha ramp: dark dip 0x4a,0x4e (rising); after hold 0x19,0x0c (falling). Letterbox bars (after hold) = two SPRITES ALPHA=0x42, rgba 0x80ffffff, y 800..845 and 1203..1248 (primitive coords), drawn before the fade.
- No FIX-alpha zoom/blur quad in any of the 12 captured PCSX2 frames. Our run issues it (0x09..0x40..0x00 + 0x04..0x1a..0x04, two clusters per run). Need PCSX2 dumps of the tunnel frames and the first ~10 castle frames to see whether the real game draws it.
- OURS (real timing): tunnel returns DARK during the load => the last white fade overlay is not part of what we re-present when the game stops drawing. Keep-previous counters are ~0, so another path drops it (2D frame selection / cover check / fade quad handling). Unverified which.

- 2026-11-23 user note: the blur ALSO happens half-way through the castle level at a spot that always slows the game and applies the blur (game slow-motion+blur effect; see HYPOTHESES C319 monkey capture). Transitions work (T1..) may not fix the blur; do it first anyway.

## B5/B1 ROOT-CAUSE LEAD (PROBE-T1, logs/t1a_err.txt, real load timing)
- Publisher log [t1-pub], white fade sprite (prim=46 alpha=44, rgba0 = RGB white + alpha in low byte): seq 796-800 alpha 0x07,0x1c,0x31,0x47,0x5c rising; seq 809 = 0x7b (~96%); then seq 810.. alpha DECREASES 0x79,0x77,0x75,0x73,..,0x59 one frame at a time, game still ticking (n2d=10 per frame).
- PCSX2: fade reaches full white, then ZERO draws for ~2.8 s (load), then fades out (0x19,0x0c).
- => In ours the game does NOT block during the stage load: its fade state machine starts the fade-OUT immediately while the tunnel is still the scene (dark tunnel returns), and the castle only appears when the load truly finishes. This is the 'transitions end early' bug (main thread keeps ticking while PCSX2's is blocked in the load).
- Likely area: how the load completion is signalled to the guest (CID1 RPC deferred replies, FIX-AU5 queue, FEAT-E8c drive model) vs where the real game blocks (sceCdSync / semaphore / RPC wait) and whether we let the main loop (0x51DF88, sceGsSyncV 0x404198) run in that window.
- NEXT (PCSX2): savestate at the white hold -> pcsx2_get_threads + backtrace to see which guest function/semaphore the main thread blocks in; then compare with ours at the same stage.

## B5 ROOT CAUSE (PCSX2 slot 2 + breakpoints, PROBE-T2 trace in ours)
- Guest code 0x439b40..0x439bf8 = SDK sceSifCallRpc: CreateSema, SifSendCmd(0x8000000a), WaitSema (WaitSema(10), ra=0x439bec), woken by iSignalSema(10) from ra=0x439448. PCSX2 threads at white hold: TID1 running in WaitSema(10) sequence (every ~0.2-0.4 s per file), TID2 waiting in a semaphore, TID3/4 SleepThread (ra 0x35f4b4, woken every vblank).
- Ours: sceSifCallRpc is HLE (RPC.cpp SifCallRpc L1570+) and returns at once; trace shows tid1 (main, entry 0x100134) NEVER calls WaitSema in the load window, so the main loop keeps ticking and the fade-out starts while stage files are still read (castle reads span ~1100 log lines after the fade peak).
- Fix = T3: make sync SifCallRpc block the calling guest thread until the modelled IOP completion (Cid1DriveModel due time). Env PS2X_RPC_BLOCK=1 (default off until verified).

## B5 refinement (PCSX2 breakpoints)
- Sync RPC seen in PCSX2 during the white hold: guest 0x43de18 (called from game code 0x36bd50, a0=0x10000) -> sceSifCallRpc(client 0x76d7c0, fno=1, mode=0). NOWAIT per-vblank call (client 0x74b240 fno 0 mode 1, ra 0x3fc06c) is the pad poll and is the only RPC we also see.
- Ours: libcdvd calls are instant HLE stubs (Kernel/Stubs/CD.cpp) and never go through SifCallRpc; T3 (PS2X_RPC_BLOCK) therefore never fired. T4 = block the guest thread in those stubs while the Cid1 drive model is busy.

## B5 status after T3/T4 (2026-11-23)
- Guest 0x43de18 is mapped to sceSifAllocIopHeap (config.toml), i.e. an IOP-heap alloc RPC, NOT a disc poll: T4's premise was wrong. T3 (sync SifCallRpc block) and T4 (cd stub blocking), both env PS2X_RPC_BLOCK=1 default OFF, never fire in the load window ([rpcblock]/[cdblock] = 0).
- PCSX2 has 4 non-idle guest threads at the white hold (TID1 main, TID2 WaitSema, TID3 + TID4 SleepThread) vs 3 in ours (tid1 main entry 0x100134, tid2 entry 0x284268 sleeping, tid3 entry 0x35f4a4 sleeping). The thread that WaitSema()s in PCSX2 (TID2) has no counterpart in ours => likely the stage-loader thread, which our HLE/boot path never creates or lets exit. NEXT: get thread entry points + the semaphore TID2 waits on from PCSX2 (kernel TCB/sema table), then find who creates it in the game (CreateThread callers) and why ours differs.

## B2 math audit (docs/MATH_AUDIT.md)
- Suspect #1 FIXED (M2): translateVU_VFTOI used _mm_cvttps_epi32 => 0x80000000 on +overflow (sign flip); now saturates to 0x7FFFFFFF. 31 occurrences in 15 generated files patched by tools/fix_vftoi_sat.py (idempotent), translator fixed for regeneration, unit check tools/mathcheck_vftoi.cpp passes 7/7. NOT yet confirmed to cure the explosions - needs user test.
- Remaining suspects (audit table): VF0 write-guard, PMADDW/PMULTW unsigned mul, PMADDH/PHMADH/PMULTH accumulators, /fp:fast in ReleaseMode.cmake, VMAX/VMINI exp-255, VCLIPw exp-255, macro-mode flags, denormal flush, VDIV/VWAITQ timing. Several need verification before trusting (audit is analysis from reading code).

## B2 evidence (PROBE-M3/M4/M5)
- VU0 macro hook (M3) and VU0 microprogram tracer (M4): nothing logged during play where explosions + rope glitch were seen (user-confirmed) => physics is not in VU0.
- VU1 watchdog (M5, logs/v1w_err.txt): bad draws are 4-vertex rigid draws (handler 0x2440, mscal 0x00e5/0x0000) with object matrix X translation garbage (-4.99e13, -1.17e14, -3.15e12; bits 0xd6359b70) while Y/Z (0.5..1.4 / 554..632) and rotation are sane. ~250 bad draws per 5 s. Skinned 1EE0 has a few (n=2-7 per 5 s). => the bad float is written by EE code. NEXT: M6 store watch (find the writing PC) + RAM scan for the bad bits.

## B2 root cause (2026-11-23, PROBE-M5..M9)
- VU0 probes silent; VU1 [vu1bad] bad-matrix draws never reach the renderer (harmless). Visible spikes = prim 0x7d triangle fans from handler 0x2900 (clipPolygon), clipRan=1 vin=3 vout=4, output vertices all (0,0,0,0).
- [clipbad] dump (logs/m9b1_err.txt): clip INPUT vertices are ~1e37..2.8e38 (near FLT_MAX: PS2 div-by-zero => +-FLT_MAX, exists in PCSX2 too). Our IEEE arithmetic: (v1-v0) overflows to Inf, t*Inf with t==0 = NaN -> output zeros -> giant triangle. Real VU saturates to +-FLT_MAX (no Inf/NaN).
- Occurs with PS2X_VIF1_ASYNC=0 as well (not an async race). Intermittent per run (0..150 spikes/70 s) in warp toyhouse_a.
- Fix task: M10 (saturating clip arithmetic). Verify: [clipbad-sum] badCalls=0 and [spike-sum] 0 over several 70 s runs.

## B2 status 2026-11-24
- M10 (clip saturation) cut bad clip outputs from ~100k per run to 0-2k, still nonzero in ~2 of 5 runs. M11 (CPU wrap of RdVert pos) was WRONG (pos is clip-space x,y,z,w): broke geometry, disabled by default (PS2X_RD_WRAP=1 only). M12: GS-style 12.4 wrap in rd.vert for out-of-range vertices only (normal scene unchanged, visual check woods_a OK); not yet validated on a real spike (spike detector measures CPU-side values so it still counts them).
- Remaining clipbad input: polygons with ~FLT_MAX vertices from objects whose object matrix is filled with +-3.4e38 (EE side). Decisive check needed: does PCSX2 submit those draws (prim 0x7d fan, tex tbp 0xb720/b7c0/b900/b9a0/b980/b740) in toyhouse_a? => ask user for 2 PCSX2 GS dumps in toyhouse_a.

## B2 findings 2026-11-24 (PCSX2 dumps ref_toy, ref_toy2 + M13)
- User test of M10+M12 build: no visible change; explosions still happen => not fixed.
- PCSX2 toyhouse dumps: the spike textures (tbp 0x3720/0x3740/0x37c0/0x3900/0x3980/0x39a0, 64x64) are PARTICLE atlases drawn as large strip batches (one group of 2424 vertices); no polygon wider than ~2260 px ever. So the spikes are particle effect quads with garbage (+-FLT_MAX) positions in ours only.
- M13: sceGsSyncV returns exactly once per vblank (d1 only, no zero/double steps), main loop ~48 ticks/s in that setup; COP0 Count unused by the game (no mfc0 \ in recomp_source); timers T0/T1 read 0 in the probe (inconclusive). So a zero time step from loop pacing is NOT the cause.
- Next idea (costs a multi-hour full rebuild because ps2_runtime_macros.h changes): log the host return address of every FPU div-by-zero / FLT_MAX-clamp result (ps2_fdiv_slow etc.) and resolve it with the PDB to the guest function that creates the FLT_MAX values.

## DECISION 2026-11-24 (user): park B2 explosions + rope glitch (likely the same EE math/collision problem: character slides out of ropes) and B5 transitions until ONE batched overnight full rebuild that carries: (a) header probe on FPU div-by-zero/FLT_MAX results (return address -> PDB -> guest function), (b) real sceCdInitEeCB (worker thread 0x3c5270) / loader thread fix. Meanwhile work on items that need no full rebuild: briefing tunnel missing blue squares, level-select lag, hub panorama/haze, pause ball, bars.

## Items 3 and 7 are ONE bug: off-screen render targets (2026-11-24)
- Level-select preview: textures tbp 0x2e40/0x3240 (256x256 PSMCT32 = fbp 0x172/0x192) are all black in ours; 0x3640 (PSMT8) has the picture. PCSX2 fills them by rendering into those framebuffers. IPU is NOT involved (IP1: no IPU/MPEG activity in level select). Pause screen: copy display->scratch 0x70, shrink into fb 0xe0 (tbp 0x1c00), blend back; ours black. Frontend drops such draws (dropped-offscreen-fbp / dropped-feedback). HYPOTHESES C446 notes the same. Analysis task RT1 -> docs/RTT_ANALYSIS.md.

## Level-select preview, corrected (2026-11-24, RT2 + ref_levelselect uploads)
- NOT render-to-texture, NOT IPU: PCSX2 fills tbp 0x2e40 (and 0x3240) every frame with 16 host->local uploads of 16x256 PSMCT32 (a 256x256 picture in vertical strips), before the TV draws (#461/#475/#489). Ours: zero uploads to 0x2e40/0x3240 in level select (PS2X_UPLOAD_LOG=2), zero draws to fbp 0x172/0x192/0xe0 (PS2X_RTDRAW_LOG: only the per-frame fbp 0x70 copy), no IPU/MPEG calls (IP1). So the EE code that decodes/builds the preview frames does not run (or produces nothing) in ours. stages.bin (170880 B) IS read. Pause screen is separate: genuine render-to-texture (0x70 -> 0xe0 -> back) whose passes are dropped as dropped-offscreen-fbp; the Vulkan GS backend does run off-screen draws (RTT_ANALYSIS.md).
- NEXT: PCSX2 savestate at the level select with the preview visible; find the EE code that builds the 16x256 strip uploads (TRXREG 0x0000010000000010) and the source buffer, then check why it does not run in ours.

## Level-select preview: where it stands (2026-11-24)
- PCSX2 (state slots 7, 8): picture = 256x256 RGBA in EE RAM at 0x01c47480 (heap record 'ipu work'; every pixel quadrupled horizontally => low-res decode upscaled by EE code), sent to GS each frame as 16 strips of 16x256 (GIF packets at 0x00a35f50 +0x80). Source blocks 'ipc' (tv_<stage>_00, IPU-style bitstream, no MPEG start codes) are read from etc/warpgate/str/stages.bin in 170880-byte chunks to 0x01bb3a80 / 0x01bdd600: identical addresses and format in ours (data loads fine).
- PCSX2 breakpoints on every sceMpeg*/sceIpu* entry and the IPU_CMD write sites (0x41179c, 0x4118a8) and 8 libmpeg internals: NONE hit while the picture is decoded => decode is game EE code, no library, no IPU hardware. In ours the buffer at 0x01c47480 stays all zero (allocated: heap record present), no strip packets exist anywhere in RAM.
- Missing in ours: SDK thread entry 0x4367e0 (SIF RPC completion dispatcher: ring of 512 events, wake thread/signal sema) created at 0x436938 because sceSif*Rpc is HLE; thread 0x3c5270 is NOT created in PCSX2 either (var 0x69a514 = 0). All RPC endFunc args are 0 in ours (CID1 ring is polled).
- Unknown: which EE function decodes ipc and what gates it. Candidate next steps: (a) PCSX2 write watchpoint on 0x01c47480 (risky: froze PCSX2 twice before), (b) function-coverage diff PCSX2 vs ours at level-select entry, (c) park the preview (cosmetic) and continue with tunnel/godrays/perf.

## PAUSE screen (item 7) findings 2026-11-24
- Reproduced by logs/pause_nav.padrec (black after the hub) and by a live session (logs/pause_err.txt). Paused stretch: rtdraw passes run (fbp 0x70 x1, 0xe0 x2 per frame, backend ran them), but frontend frame-cut records NO boundary: [cutlog] noCut=1 nB=0 drawFbps=0,e0,70 disp=70, 2D batches accumulate (62k+), [t1-drop] hold-no-cut, nothing published => black, no UI at all. Display fbp is 0x70 (software swap copy 0 -> 0x70 each frame is the boundary). Fix 1 = PA1 (cut works while paused, UI visible). Fix 2 (later) = tinted scene backdrop via off-screen targets (0x70 alpha as PSMT8H index through a CLUT, shrink to 0xe0, blend back).

## Overnight full rebuild started 2026-11-24 (user asleep)
- Carries: PA1e (swap copy recognised via per-flip display fbp, pause black screen), M14 (PS2X_FPU_PROBE=1: FPU div0/rsqrt0/saturation counts per guest function, header change).
- After build: pause_nav replay with PS2X_RD_CUTLOG=1 (expect noCut=0 nB=1 batches~300), normal hub replay regression, then FPU probe run in a level with explosions/ropes.
- Transitions (B5) need NO regenerated code: missing thread TID2 (WaitSema, PCSX2 TID2 pc 0x435b28) has no counterpart in ours; kernel .cpp work only, do after the build.

- PA1e RESULT (logs/pa1e_err.txt, release build): NOT fixed. 11733/14218 paused flips still noCut=1 (batches +296/flip until a rare accept), [cutwhy] reason=no-clear gap=0 armed=0 although [cutfix] PA1e 'copy recognised disp=70' fires. Copy recognised but armed state is lost/not consumed before the clear check. PARKED per user.

## B3 rope: first data (2026-11-24, PCSX2 slots 9/10/0 vs ours logs/ramdump_1..6)
- Player position is at 0x647b00 (also 0x785bc0), same address in PCSX2 and ours. PCSX2: P09 (-241.7,53.2,193.1) air -> P10 (-238.8,39.2,190.8) -> P00 hanging (-246.7,35.1,197.5).
- A 5-node ring (stride 0x90 from 0x64af60, all same y; x,z within +-2 of the player) is the likely ground/contact probe: PCSX2 y=-23 (floor) before contact, +18/+15 after contact (rope height, ~20 below player), and fields +0x24 7->4.34, +0x30 0.105->0.322 change at the grab. OURS: those fields never change (7 / 0.105) and the ring y keeps falling (2, -25, -81 | -4, -20, -75 over ~1 s dumps) while the player stays y~35-50 => the rope contact is never detected, the player falls through. This is a COLLISION result (rope hit missing), not FPU specials, not dt.
- Next: find the writer of 0x64af84/0x64af90 at the grab (PCSX2 write watch on a rarely written word needs user OK; alternative store-trace in ours = header change).

## B3 rope: refined (WW1 store trace + PCSX2 bp, 2026-11-24)
- Correction: 0x64af60.. ring is a per-frame effect decal spawned by guest fn 0x285E60 (called from 0x342E94, f12 = size 7.0 in PCSX2 idle vs 5.0 in ours idle, f13 0.105) at the player's ground-contact point; NOT a collision result by itself. The ground-contact record (point at +0x300, normal +0x320) of the player object is written by guest fn 0x340AD4 (sq t6,0x300(s1) at 0x340BA4, uses MMI pextlw/ppacw/prot3w/pcpyld).
- Ours: ground records at 0x93e3f0/0x93e5b0 (group 1) and 0x8da340/0x8da500 (group 2): contact y = 14.9 (rope height, seen once at dump 2) then -44, -84 / -4 -> -20 -> -75 per ~1 s: the SURFACE THE PLAYER STANDS ON FALLS at gravity-like speed => the rope body itself collapses in ours (pinned ends not holding) => same chain/cloth physics family as the mesh explosions (C447).
- PCSX2 keeps ground y = 18.2 / 15.1 (hanging).
- Next: locate rope chain nodes (PCSX2 slots 9/10/0, positions along x~-245,z~195, y 15..60) and the guest fn integrating them; compare constraint/pin handling and the instruction classes it uses (MMI/VU0/FPU) with PCSX2.

## B3 rope: function-replay harness (2026-11-24)
- Tools (all env-gated, cpp-only): PS2X_WWATCH(+_AFTER/_MAX/_SIZE4) store trace with host-sym attribution; PS2X_FNREPLAY=<spec> runs ONE recompiled guest fn on a PCSX2 RAM image + regs (spec built by scratchpad gen_spec.py from MCP register dumps, RAM from p2s eeMemory.bin), dispatch loop until pc==ra, PS2X_FNREPLAY_REPEAT/_WATCH; F10 dumps EE RAM. Verified: fn 0x2903B8 replay == PCSX2 RAM exactly (525 words); fn 0x340744 (player collision update, a0=0x8D92E0) matches except 3 timing-counter words at 0x772730..44.
- Callers: 0x4de218 > 0x15a9f0 > 0x4dd63c(entity update, a0=player 0x8B6FB0) > 0x33f26c > 0x341a74 > 0x341aa0 > 0x340744 > (0x343800, 0x2903B8, 0x347534, 0x29045C, 0x41A3D8, 0x340ad4 ground-record writer).
- In PCSX2 fn 0x340744 is NOT called again once the rope is grabbed (state changes). Ours: replaying 0x4dd63c repeatedly on slot-9 RAM, ground y stays -23.08 for ~11 iterations then falls -6/iter (player pos not integrated there, so not conclusive).
- NEXT: capture the exact contact frame in PCSX2 (entry via CP0 Count window, exit with ret bp) and replay in ours; diff = the wrong instruction semantics. Also consider replaying 0x341aa0 (state setter) at that frame.
