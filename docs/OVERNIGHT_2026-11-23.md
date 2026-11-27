# Session report 2026-11-23 (effects, transitions, level select)

## Done and committed (PS2Recomp, branch feat/sdl3-frontend, pushed; tag safe-before-vu1-decomp-2026-11-23 on both repos)
- FIX-E8b: Z-only end-of-frame sprite (ATST NEVER + AFAIL ZB_ONLY) no longer counts as a frame-boundary clear. Restores cinematic bars, blue briefing tunnel, white fade.
- FIX-E8d: VBlank never fires before its wall-clock deadline (vblanks were 75-103/s during loads). Restores the level-select tutorial.
- FEAT-E8c: optional PS2 DVD load-timing model (default ON, PS2X_LOAD_TIMING=fast disables). Did NOT fix early transitions; breaks padrec replays -> always replay with fast.
- FIX-E8g: level-select 3D lock-up (6-slot ring overflow + endless keep-previous). User confirmed fixed.
- Probes: E6a-c blur locator, E7a/b bars + prev-frame age, E8a blur-source pc (sampled, useless as call site), E8e/E8f state/pass logs (PS2X_RD_STATELOG / PS2X_RD_PASSLOG).

## Open findings
- Blur at the castle fly-by: our run issues the game's own blend-previous-frame pulse (FIX ramp 0x09..0x40..., twice); PCSX2 and longplays do not. Not input-related (user). Builder is runtime-computed, not findable by byte search. Parked.
- Transitions end early: vblank lock did not fix it; fade steps are per-vblank. Next test: PCSX2 stopwatch of a white fade and its FPS counter, or check EE timers (also advanced by guest cycles).
- Hub: reference has a vivid blue sky and glow; ours has a pale/white sky and a faint pale rectangle left of the TV. Large translucent planes with fge=1 (tex 0x2a00/0x2a40/0x2ae0/0x3300, a=0x44, F 190-255) are the likely cause. PS2X_RD_FOG_ZERO=1 makes it worse (flat blue patches); PS2X_RD_FOG=0 looks like the default. Needs the fog/haze work (item 3).
- VU1: a functional C++ engine already exists (vu/vu1_func.inc, ~5000 lines, handlers per program) and a scene extraction layer (PS2X_SCENE / SceneVertex pos+normal+stq, SceneDraw objMatrix) already exposes the data lighting needs. The remaining work is the consumer (Enhanced renderer: shadows), not the decompile itself.

## Hub "subtle blue square" lead (late evening, not fixed)
- Cropping our hub screenshot shows a pale translucent rectangle with a hard left edge (~x=95 of 640) between the sky and the TV, from the top down to the railing.
- It matches reference-hub draw #8690: tex tbp 0x3300 256x128 psm19 (the landscape panorama: hills, texture dumped in logs/rdtex/97478d1e68ca6b29_psm19_256x128*.png, alpha plane uniform ~0x80), ABE a=0x44, ATE ATST=NEVER AFAIL=FB_ONLY ("at=10:0x0/1"), fge=1 F=190-195, bb=(70,95)-(256,246).
- Hypothesis [OPEN]: with ATST NEVER + AFAIL FB_ONLY the pixel is written colour-only but still blended with source alpha 0x80 (=1.0 on PS2). If our shader maps tex alpha 0x80 to 0.5 for this path (or applies the F=190 fog as a 25% fog tint), the panorama is drawn half-transparent over the sky -> pale rectangle with a hard edge. Not fog-env related (PS2X_RD_FOG=0 and FOG_ZERO=1 do not remove it). TEXFILTER by tbp did not match (skipped=0), so isolate it with a probe logging the alpha and fog actually used for the batch.
- Also in ours: no glow halo around the TV (ref has a soft one, draws #18659 tex 0x2d00 a=0x44 and #22347 a=0x48 additive, bb ~(199,48)-(312,147)); PS2X_RD_FBTEX_CT=1 does not add it.

## Test tooling (scratchpad, not in repo)
- logs/overnight_hub.padrec: boot -> hub -> seaside_a. Replay + `warp <stage>` via dev console works (warp_shots.ps1 in the session scratchpad). Always PS2X_LOAD_TIMING=fast.
