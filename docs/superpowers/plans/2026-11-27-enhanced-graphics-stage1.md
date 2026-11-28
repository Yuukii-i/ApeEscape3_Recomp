# Enhanced Graphics, Stage 1 and Level-Data Trial: Implementation Plan

> **For agentic workers:** this project's CLAUDE.md sets the execution method: Claude writes one
> task spec at a time (`docs/NEXT_TASK.md`), Gemini 3.8 Flash (Medium) writes the code, Claude
> builds, runs and judges. One task = one build. Steps use checkboxes (`- [ ]`).

**Goal:** an Original / Enhanced switch with screen effects tuned per level, and an answer to
whether whole-level geometry can be captured (stage 3).

**Architecture:** the world is drawn exactly as today. Just before the final HUD pass, one call
copies the colour and depth, runs a post chain, and writes the result back into the same target.
Settings come from per-level and per-zone profile files bundled with the port.

**Tech Stack:** C++20, Vulkan 1.2 dynamic rendering, GLSL compiled with `glslc`, Dear ImGui.

**Spec:** `docs/superpowers/specs/2026-11-27-enhanced-graphics-design.md`

Stage 2 and the rest of stage 3 get their own plans, written after the results here.

## Global Constraints

- Original mode: identical picture, no added frame time. Enhanced: Vulkan renderer only.
- Never affects HUD, menus, movies or 2D transition screens. Motion blur is not in this plan.
- Effects start subtle. Every effect has on/off and strength; strength 0 changes nothing.
- 60 fps locked in Enhanced at 1080p on the RTX 4060 laptop; added processor work about 1 ms per
  frame at most on the busiest thread.
- No edits to existing headers. A new header included only by render and panel files is allowed.
- `RdVert` is defined in `gs_frontend.cpp`, `rd_view.cpp` and `vu1_func.inc`; stage 1 does not
  change it.
- Builds use 2 workers at idle priority; game windows go to screen 1 (`PS2X_DISPLAY=2`), in the
  background.
- No game data, dumps or screenshots in git. Runtime code is marked `// FEAT-ENH<task>`.
- Branch per task, PR, PS2Recomp pushed before the parent.

## Review Focus

1. Pause, level select, shop, memory card screens, movies and transitions with Enhanced on: look
   as in Original (Tasks 1 and 11).
2. Frames with no 3D, loading, or an unreadable stage name: no effects or the default profile, no
   crash (Tasks 1 and 3).
3. MSAA 1x and 4x, render scale other than 100%, window resize, 4:3 and ultrawide (Task 1).
4. A profile file that is broken, half written or deleted while running: keep the last good
   values, log once (Task 3).
5. Switching Enhanced on and off repeatedly, including during a transition: no crash, no stale
   image (Task 1).

## Shared check

Unless a task says otherwise: build, replay `logs\blur.padrec` with `logs\mc0_blur_rec` (castle)
through the scratchpad script `fast.ps1`, and take screenshots with Enhanced off and on.

## File map (under `PS2Recomp/ps2xRuntime/`)

| File | Role |
|---|---|
| `src/lib/render/rd_enhance.h` (new) | `RdEnhanceSettings`, `RdEnhanceFrame` and the calls below |
| `src/lib/render/rd_enhance_vk.cpp` (new) | post images, pipelines, the effect chain |
| `src/lib/render/rd_enhance_profile.cpp` (new) | profiles: load, reload, save, stage lookup |
| `shaders/fx_full.vert`, `shaders/fx_*.frag` (new) | one fragment shader per pass |
| `src/lib/render/rd_gfx_vk.cpp` | sampled depth usage; hand device and images to the post code |
| `src/lib/render/rd_view.cpp` | one call before the final `draw2dUntil(0u, true)` (about line 7513) |
| `src/lib/vu/vu1_func.inc` | publish the camera matrix |
| `src/lib/config/ps2x_config.cpp`, `src/lib/ps2_debug_panel.cpp` | switch and sliders |
| `CMakeLists.txt` | new sources and shaders (shader block near line 575) |

---

### Task 1: Switch and pass-through post stage

**Files:** create `rd_enhance.h`, `rd_enhance_vk.cpp`, `shaders/fx_full.vert`,
`shaders/fx_composite.frag`; modify `rd_gfx_vk.cpp`, `rd_view.cpp`, `ps2x_config.cpp`,
`ps2_debug_panel.cpp`, `CMakeLists.txt`.

**Interfaces, produces:**
- `struct RdEnhanceFrame { float vpScaleZ, vpOffsetZ; float camera[16]; bool cameraValid; float gsToClip[16]; };`
- `bool ps2xEnhanceOn();` and `void ps2xEnhanceSetOn(bool);` (setting `graphics.enhanced`,
  variable `PS2X_ENHANCED`, default 0)
- `void ps2xEnhanceApply(const RdEnhanceFrame &);` runs between the world and the HUD, leaves the
  colour target ready for further drawing and the depth contents unchanged.

- [ ] **Step 1:** add the setting, a checkbox "Enhanced graphics" in the Graphics tab (live, saved
  by "Save to ps2x.ini"), greyed out unless the Vulkan renderer is active.
- [ ] **Step 2:** implement `ps2xEnhanceApply`: copy or resolve colour, composite it back
  unchanged. Depth gets sampled usage (read sample 0 when multisampled).
- [ ] **Step 3:** call it only when Enhanced is on and the frame has 3D batches.
- [ ] **Step 4:** with `PS2X_ENH_VERIFY=1`, read the target before and after on every 60th frame
  and log `[enh] verify maxdiff=<n>`.
- [ ] **Step 5:** run the shared check. Expected: `maxdiff=0` on every line, HUD present, no
  validation errors.
- [ ] **Step 6:** run Review Focus 1, 2, 3, 5 (recordings `leveselect`, `saveload`, `pause_user`,
  `transitions`; MSAA 1 and 4; `render_scale` 50 and 200; ultrawide). Expected: `maxdiff=0`.
- [ ] **Step 7:** commit `feat(render): enhanced switch and pass-through post stage`.

### Task 2: Camera matrix and depth, with debug views

**Files:** modify `vu1_func.inc` (`beginLeanDraw`, publish), `rd_view.cpp`, `rd_enhance_vk.cpp`;
create `shaders/fx_debug.frag`.

**Interfaces, produces:**
- `void ps2xRdPublishCamera(const float rows[16]);` from VU memory 998..1001 of the draw with the
  most points in the frame (same rule as `vpScaleZ`).
- `RdEnhanceFrame::camera` and `gsToClip` filled; `gsToClip` is the linear map `shaders/rd.vert`
  applies to `aPos` (its `uVpB.w > 0.5` branch, plus the y flip and the depth remap). Post shaders
  get world position from `inverse(gsToClip * camera)`.
- `PS2X_ENH_DEBUG=depth|grid`, and the same choice as a combo in the panel.

- [ ] **Step 1:** publish the matrix; log once per second `[enh] cam changes=<n> distinct=<n>`.
- [ ] **Step 2:** `depth` view shows distance as grey; `grid` view draws a one-unit-spaced grid
  from world position over the picture.
- [ ] **Step 3:** run the shared check with each view. Expected: `distinct=1` in gameplay; the grid
  stays fixed on walls and floor while the camera moves. A grid that slides means the maths is
  wrong: stop and fix before Task 5.
- [ ] **Step 4:** check a TV or studio stage (render-to-texture) and a level intro for a second
  camera taking over.
- [ ] **Step 5:** commit `feat(render): camera matrix and depth for post effects`.

### Task 3: Per-level and per-zone profiles

**Files:** create `rd_enhance_profile.cpp`, `enhanced/levels/default.ini` (parent repo);
modify `rd_enhance.h`, `ps2_debug_panel.cpp`.

**Interfaces, produces:**
- `struct RdEnhanceSettings` holding every value of Tasks 5 to 10, each effect as
  `bool on; float strength;` plus its parameters, and `float sunDir[3], sunColor[3], ambient[3]`.
- `const RdEnhanceSettings &ps2xEnhanceSettings();`
- `std::string ps2xEnhanceStageName();` reads the 32-byte name at guest `0x649650`
  (`docs/golden_pcsx2.md`).
- Files in `enhanced/levels/` (`key=value`), applied in order so later ones override key by key:
  built-in values (every strength 0), `default.ini`, `<level>.ini`, `<stage>.ini`. The stage name
  is e.g. `woods_a`; the level is the part before the last `_`.

- [ ] **Step 1:** confirm in PCSX2 that `0x649650` holds the stage name in two levels and the hub;
  record it in `docs/golden_pcsx2.md`, including that the name changes on moving between zones.
- [ ] **Step 2:** load, reload when the file time changes (checked once per second), save from
  "Save for zone" and "Save for level" buttons; panel shows the stage name and the files in use.
- [ ] **Step 3:** a name with characters outside `[a-z0-9_]` or empty uses the default.
- [ ] **Step 4:** run: edit a value while the game runs (log `[enh] profile reload <file>`), write
  a broken line (log once, old values kept), delete the file (falls back).
- [ ] **Step 5:** commit in both repos `feat(render): enhanced profiles per level and zone`.

### Task 4: Trial: can we get the whole level? (stage 3 risk)

**Files:** create `docs/ENH_LEVEL_DATA.md`; for candidate 2, modify `ps2_runtime.cpp`.

- [ ] **Step 1 (PCSX2 first):** at `testFrustumAabb` (`0x3BA898`) record the return convention,
  callers and call count in the first castle area; look for the mesh and placement lists the
  callers walk (`docs/EE_GFX_DATA_MODEL.md`).
- [ ] **Step 2:** candidate 2: override gated by `PS2X_ENH_NOCULL=1` that reports every box as
  visible.
- [ ] **Step 3:** dump one frame with and without it (`PS2X_SCENE=1`, `PS2X_SCENE_DUMP=<n>`).
  Report draws, points, points behind the camera, and frame time.
- [ ] **Step 4:** judge against the spec's pass line (fixed scenery of the first castle area,
  including behind the camera, lining up). If the view test is not enough, assess candidate 1
  (reading mesh data) from the Step 1 findings.
- [ ] **Step 5:** write the verdict and recommendation, commit
  `docs: level geometry capture trial`, and report to the user before any fallback work.

### Tasks 5 to 10: the effects, one per build

Each task: **modify** `rd_enhance_vk.cpp`, `rd_enhance.h`, `rd_enhance_profile.cpp`,
`ps2_debug_panel.cpp`, `CMakeLists.txt`; **create** its shader. **Consumes** the frame data of
Task 2 and the settings of Task 3. Common steps:

- [ ] Add the pass, its settings, sliders and profile keys.
- [ ] Verify: strength 0 or off gives `[enh] verify maxdiff=0`.
- [ ] Shared check with the effect on at its default; log `[enh] gpu_ms=<total>`.
- [ ] Commit `feat(render): <effect>`.

| Task | Effect (shader) | Parameters beyond on/strength | Also accept |
|---|---|---|---|
| 5 | Colour grading (`fx_grade.frag`) | exposure, contrast, saturation, tint | neutral values give `maxdiff` at most 1 |
| 6 | Bloom (`fx_bloom_down.frag`, `fx_bloom_up.frag`) | threshold, radius | castle lamps glow; HUD does not |
| 7 | Added fog (`fx_fog.frag`) | colour, start, end, height, falloff, sky amount | sits on distant scenery, not on the character up close |
| 8 | Corner darkening (`fx_ao.frag`, `fx_ao_blur.frag`) | radius, bias | no halos around the character; no flicker standing still |
| 9 | Depth of field (`fx_dof.frag`) | focus distance (0 = follow screen centre), range, blur size | character sharp, far distance soft |
| 10 | Light shafts (`fx_shafts.frag`) | length, decay; direction and colour from the sun | only toward sky or bright openings; fades when the sun is off screen |

### Task 11: Stage 1 acceptance

**Files:** modify `enhanced/levels/*.ini`, `docs/HYPOTHESES.md`, `docs/HANDOFF.md`.

- [ ] **Step 1:** Original against the pre-plan build: back-to-back `performance.padrec` runs.
  Expected: no difference beyond run-to-run spread.
- [ ] **Step 2:** Enhanced with all effects: same replay. Expected: added processor time at most
  1 ms on the busiest thread, 60 fps held where Original holds it.
- [ ] **Step 3:** Review Focus 1 again with all effects on.
- [ ] **Step 4:** starting values for one outdoor, one indoor, one night and one water level.
- [ ] **Step 5:** give the user a run command; they tune and judge. Record their verdict and any
  change to the plan for stage 2.
