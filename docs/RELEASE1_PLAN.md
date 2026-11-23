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
