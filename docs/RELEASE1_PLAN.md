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
