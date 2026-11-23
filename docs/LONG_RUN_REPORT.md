# Long run report (2026-11-23)

All coding by Gemini 4 Hydrogen (Medium) from specs in docs/tasks/*.md; builds, runs and screenshot checks by Claude. Local commits only after the one authorised push (tag safe-before-vu1-decomp-2026-11-23 on both repos). Log: docs/LONG_RUN_LOG.md.

## Phase 1 - Mapping: DONE
docs/VU1_MAP.md. Measured with PS2X_VU1_FUNC=1 PS2X_VU1_HPROF=1 on hub, woods_a, castle_a, space_a, studio_a, ciscocity_a: `fallback=0` in every scene; the functional engine already runs all gameplay VU1 programs. 1EE0 (skinned) is the biggest cost (1.1-2.6 ms/frame), then 2440 (rigid), 2900 (clip).

## Phase 2 - Fog / haze / pause
- A. Hub: FIX-E10a (fog on the lean skinned path, previously hard-coded to 1.0; self-check 1.8M verts/s, 0 mismatches). Native hub and seaside look correct. Dev `warp` leaves stale fog constants (skinned models become blue silhouettes only after a warp) - artifact of warp, not of normal play. Hub tree haze vs PCSX2 and the pale hard-edged rectangle left of the TV are STILL OPEN: the rectangle is the landscape panorama draw (tbp 0x3300, ref draw #8690); removing it (PS2X_RD_TEXFILTER=5e1313300 PS2X_RD_TEXFILTER_INV=1) removes the rectangle and the hills; panorama texture alpha is uniformly 0x80; vertex alpha varies per vertex (0x00..0x80) so the edge softness depends on per-vertex alpha/F of the 12/21/15/36-vertex batches - needs a per-vertex comparison against the PCSX2 dump.
- B. Title-screen fog glitch: not reproduced in the current build (title ground normal with fog on).
- C. Pause menu ball: BLOCKED - logs/pause_test.padrec desyncs after the hub. Needs a new recording through a level + pause (user).
- D. God rays: not started (needs A to be settled first).

## Phase 3 - VU1 programs: mostly pre-existing; groundwork done
- docs/VU1_LIGHT_DATA.md (analysis of all light/skin/rigid handlers, VU memory addresses with CODE refs).
- FEAT-V2: SceneGlobals (view-proj, viewport, ambient, light scale, fog) + SceneLight records exported per draw only when PS2X_SCENE=1; check mismatch=0; default path unchanged.
- Finding: the 7 light handlers never run in the hub or seaside_a (lights=0); gameplay lighting is EE-precomputed vertex colours. A modern lighting path needs the EE-side light data (light matrix block / handler 1C48) or stage data, not the VU light handlers.
- Not done: bone-matrix export, stable object id, image 4279fa21 (117 runs/session, exact path).

## Phase 4 - Launcher: DONE through L4 (local commits)
tools/launcher (settings model + ini round trip, ImGui/SDL3 window with Game/Video/Audio/Input/Advanced/Log/About, process start with log capture, `--print-launch` / `--play` headless modes, first-run + validation messages), tools/build_launcher.bat (builds + runs 4 unit checks + print-launch), tools/package_release.bat (stages runtime + launcher + ini + README only), docs/LAUNCHER_PLAN.md, docs/RELEASE_CHECKLIST.md. Not done: interactive click-through test of Play in the UI (only headless `--play` verified: runtime boots), audio device / input remapping pages are stubs, release_staging/ should be added to .gitignore, the staged runtime is the 200 MB dev build (use a stripped Release build for releases).

## Needs the user
1. New padrec through a level + pause (pause ball) and, if wanted, a pause during the hub.
2. Decision: next big step = Enhanced renderer using the exported scene data (shadows first?) or finish the hub panorama/haze match first.
3. PCSX2 stopwatch of a white fade + its FPS counter (transition length), still parked.
4. Review + push of the local commits (parent: docs, launcher; submodule: E10a/V2) - pre-push scan required.
