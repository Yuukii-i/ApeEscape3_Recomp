# LONG RUN PLAN (written 2026-11-23 for one long uninterrupted turn)

Purpose: this file is the task list for a single long turn. Read it fully, then work through the phases IN ORDER without ending the turn
between phases. A turn only ends when every phase is DONE or BLOCKED (see "How to stop"). Do not hand the turn back to the user for
status; write status into docs/LONG_RUN_LOG.md instead (append after every step, one line: time, phase, step, result).

## Standing rules (apply to every phase)
- Roles (CLAUDE.md): Claude writes NO repo code. Gemini 3.8 Flash Medium codes from docs/NEXT_TASK.md specs via the background subagent
  `antigravity:antigravity-rescue` (`--background --model flash-medium`; run the companion from cwd C:\ApeEscape3_Recomp with PowerShell and
  confirm the job id with the status command). Claude builds (`cmd /c tools\build_avx2.bat`, run in the background if >10 min), runs, measures, reviews diffs.
  New tools/scripts that are not repo code (scratchpad) are fine. The launcher in phase 4 is repo code, so it is also written by Gemini from specs.
- One task = one hypothesis = one build. Spec <=40 lines, ground truth first, acceptance test, budget "[call N/12]". Edit .cpp only, no headers
  (a header edit rebuilds hours of generated code; if one is unavoidable say so and ask the user first).
- Verify every change with the replay tooling: `logs\overnight_hub.padrec` (boot -> hub -> seaside_a) + `warp <stage>` via the dev console
  (scratchpad warp_shots.ps1, always PS2X_LOAD_TIMING=fast, PS2X_FRONTEND=sdl PS2X_SDL_RD=1 PS2X_RD_VIEW=1 PS2X_RD_CUT_ADAPT=1 PS2X_RD_COVER_TOL=400
  PS2X_RD_PAIRLAG=1) and look at the screenshots. A replay that lands on the wrong screen is INCONCLUSIVE, not a pass.
- PCSX2 is ground truth (MCP). Never use memory watchpoints (they froze PCSX2 twice). Read-only scans and backtraces only. The refs live in refs\pcsx2_dumps (.zst + .png).
- Never end a task with an untested change: if a change makes something worse, revert it (git checkout the file) and log why.
- Git: local commits per task, message `<type>(<scope>): <summary>`, NO Co-Authored-By / AI attribution (CLAUDE.md; the auto-mode classifier denies commits with the trailer).
  Pushing: only to the feature branches (never main), only after the pre-push scan (no raw instruction words, no disassembly/RAM dumps, no .patch/.png/.bin from game data;
  recomp_source/ never pushed), submodule first then parent. The user authorised ONE push before phase 3 (safe tag exists: safe-before-vu1-decomp-2026-11-23 on both repos).
  Any further push: do it only at the end of a completed phase, same scan.
- Do not touch the parked items: blur at the castle fly-by, transition length, frame-timing, studio music. (They are written up in docs/OVERNIGHT_2026-11-23.md.)
- Budget guard: if a single phase step fails 3 times in a row, mark it BLOCKED in the log with the evidence and move on to the next step. Never loop on the same failing step.

## Phase 1 - Mapping (analysis only, no behaviour change)
Goal: know exactly which VU1 programs/handlers run, in which scenes, and where the semantic scene layer (PS2X_SCENE) already exposes data.
1. Read docs/VU1_DECOMPILE_PLAN.md, docs/VU1_HANDLER_FORMS.md, docs/EE_RENDER_MAP.md, the end of docs/DECOMP_LOG.md, and the top of
   PS2Recomp/ps2xRuntime/src/lib/vu/vu1_func.inc (handlers list: grep `static bool handler`). Do not read whole large files; use Grep + 120-line reads.
2. Find the existing probes (PS2X_VU1_FUNC, PS2X_SCENE, PS2X_SCENE_DUMP, PS2X_SCENE_CHECK, PS2X_RD_RECPROF, vuH counters). Run the hub, a forest level (woods_a),
   a castle level and the level select with them on (replay + warp) and produce docs/VU1_MAP.md: per scene, handler pc -> calls/frame, ms/frame, share; which handlers the
   functional engine covers and which fall back to the exact interpreter; the microcode image hashes seen. If a needed counter does not exist, write a spec for Gemini (probe only).
3. In the same doc: a table "what lighting needs vs what we already have": world pos, normals, object matrix, bone matrices, light constants (where in VU memory, which handler reads them),
   material (TEX0/ALPHA), depth. Mark each AVAILABLE / PARTIAL / MISSING with the file:line evidence.
4. DONE when docs/VU1_MAP.md exists with measured numbers for at least hub + woods_a + one castle scene, and the table is filled.

## Phase 2 - Menu fog, hub haze and pause menu too dark
Items (user-reported, real game is the reference, see refs\pcsx2_dumps\ref_hub, ref_pause_menu, ref_forest*, ref_level_enter):
A. Hub: pale translucent rectangle with a hard left edge (panorama draw #8690, tex 0x3300; PROBE-E9a was just added in rd_view.cpp, gated PS2X_RD_PANOLOG=1) and missing soft glow
   around the TV (draws #18659 / #22347, tex 0x2d00, a=0x44 then additive a=0x48, bb ~(199,48)-(312,147)). Build the probe, run the hub warp with PS2X_RD_PANOLOG=1,
   read what alpha / alpha-test / fog the renderer really applies, compare with the PCSX2 values, write the fix spec, verify with screenshots against ref_hub.png.
B. Title screen "fog on the lower ground" glitch and the general fog rule (E1: skipping F==0 batches PS2X_RD_FOG_ZERO; real fog area-weighted). Use the title screen at boot of the replay
   (shots around 12-32 s) and the forest dumps (large translucent 256x256 planes 0x3a00/0x3b80/0x2a00, a=0x44, F 0-255). Decide the correct fog behaviour from PCSX2 data, then fix.
C. Pause menu: the ball is too dark in the port (ref_pause_menu; additive 0x48 sprites). Use logs\pause_test.padrec / pause_nav.padrec (verify they still replay; they predate the vblank
   fix) or open the pause menu during a warp replay with the pad. Compare with ref_pause_menu.png, find the missing/dark draw, fix.
D. God rays (forest): only after A-C, and only if the evidence from the forest dumps is clear; otherwise write the analysis into docs/EFFECTS_PLAN.md and stop.
Each item: probe/analysis -> spec -> Gemini -> build -> replay screenshot vs reference -> keep or revert -> local commit -> log line.
DONE when A, B, C each have a verified screenshot match (or a BLOCKED note with evidence) and docs/EFFECTS_PLAN.md is updated.

## Phase 3 - Decompiling the programs (what is actually left)
IMPORTANT: most of this already exists. vu1_func.inc (~5000 lines) is a functional C++ VU1 engine with named handlers (handler00A8, 0AF0, 0B40, 15E0, 1900, 1C48, 3160, 0840, 0CC0, 1090,
02E0, 0628, 1720, 1A68, 0198, 0B38, 1910, 1EE0 ...) and a scene layer (SceneVertex pos/normal/stq/rgba, SceneDraw objMatrix/handlerPc). The DECOMP_LOG says all VU1 programs of the hub and
in-level images of the 1 h corpus run as C++. So this phase is NOT "write 40 handlers from scratch". It is:
1. From docs/VU1_MAP.md (phase 1): list handlers that still fall back to the exact interpreter in any scene (hub, forest, castle, level select, pause, shop). Those are the work items.
2. For each fallback handler (in share order): read its microcode via the existing tooling (docs/VU1_HANDLER_FORMS.md, tools/vu1gen), write the spec for Gemini (exact semantics, memory
   effects, GIF output, the registers the dispatcher reads), implement behind the existing PS2X_VU1_FUNC machinery, verify with the corpus replay (PS2X_VU1_REPLAY_FUNC=1 / PS2X_VNC self check):
   MISMATCHED(mem/gif)=0 is the acceptance test. A handler that cannot reach 0 mismatches is reverted and left on the exact path.
3. Semantic layer: make sure every decompiled handler fills SceneVertex/SceneDraw (positions before projection, normals, object/bone matrices, light constants if the handler reads them),
   and add the missing fields the lighting table in docs/VU1_MAP.md marks MISSING. Keep GIF output byte-identical.
4. Never enable a new handler by default unless the corpus replay shows 0 mismatches AND screenshots of hub + woods_a + castle match the previous build. Default flags stay as they are otherwise.
5. DONE when the fallback list from step 1 is empty or each remaining handler is BLOCKED with evidence, docs/VU1_MAP.md is updated with the new coverage, and docs/DECOMP_LOG.md has the entry.

## Phase 4 - Launcher (from scratch) for the first releases of the port
Goal: a small standalone launcher the user can ship with the port: pick the game image, pick graphics options, start the game. It must NOT bundle or require any game data in the repo.
1. Design first (write docs/LAUNCHER_PLAN.md, <=2 pages): platform targets (Windows first; Android/Linux later - choose a UI toolkit that is not Windows-only; Dear ImGui is already in the
   tree for the debug panel, so prefer SDL3 + ImGui, one executable, no installer needed), what it configures (game image path or extracted folder, resolution/render scale, aspect/widescreen, vsync/fullscreen,
   load timing Original/Fast, renderer Original vs Enhanced when it exists, input mapping, audio device), where the settings live (ps2x.ini, the same keys the runtime already reads via ps2xLoadConfig;
   check ps2x_config.cpp for the existing key list and the F1 Graphics tab), how it starts the runtime (child process with the env vars/args the runtime expects today: SCUS_975.01 arg, PS2X_FRONTEND=sdl,
   PS2X_SDL_RD=1, etc.; document each), first-run flow (no game found -> clear message, never ship/download game files), error handling (missing image, missing GPU/Vulkan), and the legal notes
   (user supplies their own disc image; no BIOS/ELF/game assets in the repo or the release zip).
2. Build plan: new CMake target `ape3_launcher` in the parent repo (tools/launcher/), no changes to runtime headers. Specs for Gemini in slices, each one build: (a) window + settings model + ini read/write,
   (b) the pages (Game, Video, Audio, Input, Advanced), (c) process start/stop + log viewer, (d) first-run + validation + about page. Each slice has an acceptance test (launches, writes the ini the runtime reads,
   runtime starts with the chosen options and shows the same result as the manual env-var command).
3. Verify by launching the runtime through the launcher with two different settings sets and checking screenshots/logs. Add the launcher to the release checklist in docs/ (docs/RELEASE_CHECKLIST.md: build flags,
   what ships, what never ships, pre-push scan).
4. DONE when the launcher builds, starts the game with the chosen settings, and docs/LAUNCHER_PLAN.md + docs/RELEASE_CHECKLIST.md exist. Keep it local until the user reviews it (commit locally only).

## Logging and reports
- docs/LONG_RUN_LOG.md: append one line per step (time, phase, step, PASS/FAIL/BLOCKED, evidence path). Create it at the start.
- At the end: docs/LONG_RUN_REPORT.md with what was done per phase, what was reverted, what is blocked, measured numbers, commits made (hashes), what needs the user (PCSX2 captures, decisions).

## How to stop
Stop only when: all four phases are DONE or BLOCKED-with-evidence, OR the user interrupts, OR a step needs something only the user can provide (PCSX2 interaction, a design decision that changes
public behaviour, permission for a push). In the last case write the question into LONG_RUN_REPORT.md, skip to the next independent step, and only end the turn when nothing independent is left.
Do not stop because a phase is large. Split it into steps and keep going.
