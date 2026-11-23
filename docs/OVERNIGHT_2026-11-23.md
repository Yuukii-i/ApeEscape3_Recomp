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

## Test tooling (scratchpad, not in repo)
- logs/overnight_hub.padrec: boot -> hub -> seaside_a. Replay + `warp <stage>` via dev console works (warp_shots.ps1 in the session scratchpad). Always PS2X_LOAD_TIMING=fast.
