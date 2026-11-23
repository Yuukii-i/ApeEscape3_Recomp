# Frame-generation unattended run plan (2026-11-23)
Rules: CLAUDE.md roles (Gemini 4 Hydrogen Medium codes from docs/tasks/FGn.md, Claude builds/runs/judges, no repo code by Claude). Build = `cmd /c tools\build_avx2.bat` (dev exe build_avx2\PS2Recomp\ps2xRuntime\ps2EntryRunner_dev.exe, ~25 s when only rd_view.cpp changes). Run scenes with scratchpad warp_shots.ps1 (`-tag -stage -extraEnv -shotsAfter`). Use PowerShell (Bash tool chokes on quotes). Local commits only, NO trailer, branch feat/sdl3-vulkan-platform, no push. Everything new is behind env PS2X_RD_INTERP* (default off, zero change). Log progress in docs/FG_RUN_LOG.md after every step. Do not stop until all phases are DONE/BLOCKED; then write docs/FG_RUN_REPORT.md.

Known (FG1, 2026-11-23): index matching leaves 25-50% of ~2700 draws/frame unmatched, p95 move in woods/castle 100+ px from misalignment, camHash never changes, hub p95 ~0.06 px (most consecutive published frames identical => logic probably 30 Hz).

## Phase A - FG2 probe (content-key matching + tick rate)  [docs/tasks/FG2.md]
Key = hash(tex0, prim, count, alpha, test, first vertex uv/rgba) with a disambiguation counter per equal key (k-th occurrence pairs with k-th occurrence). Report match %, mean/p95/max move, teleports (>64 px), identical-frame ratio (every matched vertex delta<0.01 px AND all batches matched), and the run length of identical frames. Run hub, woods_a, castle_a, space_a. Goal: >=90% matched, tick rate known.

## Phase B - FG3 prototype interpolation (only if A reaches ~90%)
Design: keep previous and current main 3D frame (verts+batches). Extra present at phase t in (0,1): for matched batches lerp pos x,y,z (not uv/rgba/fog; unmatched or teleport >64 px batches: draw the current frame's version at t>=0.5 else previous). 2D/HUD never interpolated (draw newest). Gate PS2X_RD_INTERP=1, PS2X_RD_INTERP_MODE=2|3 (extra frames per game frame). Emit by re-presenting using the existing present loop (ps2xRdDraw) with a synthetic slot; write spec after reading ps2xRdDraw (L1856+) and the GPU slot upload path, Claude reads max 120 lines per read.
Acceptance: screenshots at t=0.5 show no ghosting/tearing on hub, woods, castle; `[fg3]` log shows extra frames/s; default path unchanged (screenshots identical with env off).

## Phase C - pacing
Add the display-rate scheduler: present at vsync rate, interpolation factor from time since last real frame. Measure ms/frame cost of the extra pass (target < 1 ms). Log `[fg3] extra=%u cost_ms=%.2f`.

## Phase D - fallbacks and polish
Teleport/cut detection (camera cut = camHash change or >40% unmatched -> no interpolation for that frame pair), HUD/pause/transition frames (fades) never interpolated, toggle in launcher Video tab (add `interp` key to tools/launcher/settings; Gemini spec FG5, tools/launcher only).

## Phase E - commit + report
Commit each working step locally (`feat(render): ...`, submodule first, then parent pointer + docs). Write docs/FG_RUN_REPORT.md: results, numbers, screenshots paths, what needs the user (judge smoothness live: hub, a level, a fade).
If a phase is BLOCKED (build failure after 2 Gemini retries, ghosting not fixable), record why and move on; never leave the default path altered.
