# Enhanced graphics: design

Status: waiting for approval (2026-11-27). Replaces the draft parts of `docs/OVERHAUL_PLAN.md` and
`docs/LIGHTING_PLAN.md` where they differ.

## Intent

The look of a PS4-era remake on the same game: warm sunlight, soft real shadows, glowing lamps,
haze and light shafts, soft background blur. Same models, same textures, same art direction.
The data gathered for it is later reused by frame generation and, possibly, ray tracing.

The user's reference pictures (not in the repo): a meadow with a sunlit cabin, soft tree and
character shadows and a blurred distance; and an indoor stage with coloured spotlight beams,
glossy highlights and the character's shadow on the floor. Those pictures also show higher-detail
models, textures and grass. Those parts are **not** in scope; only the lighting and mood are.

## Goals

- An **Original / Enhanced** switch. Original looks exactly as today and costs nothing extra.
- Shadows from a sun and from characters; added lamps and coloured lights; bloom; depth of field;
  fog and volumetric fog; light shafts; soft darkening in corners; colour grading; water
  reflections.
- Each level and zone tuned by hand, live, with sliders.
- Shadows and light stay steady when the camera turns (the reason for stage 3).

## Not goals

- Ray or path tracing.
- New or changed models, textures or scenery (this removes the earlier swaying-grass idea).
- Frame generation (separate later work).
- The OpenGL backend: Enhanced is Vulkan only.

## Would count as failure

- Wrong lighting that breaks the game's palette and mood (the GTA Definitive Trilogy problem).
- Effects touching the HUD, menus, movies or 2D transition screens.
- Original mode changing in look or speed.
- Random blur. Motion blur is optional and **off** by default.

## What is known

Measured on one castle frame (`docs/HYPOTHESES.md` GEO1):

- One view-projection matrix for the whole frame (VU1 memory 998..1001). Object matrices are
  separate (978..981).
- Unit surface normals on all skinned and rigid points; none on clipped points (about 1,000 of
  59,000).
- About 3,700 draws and 59,500 points.
- No game lights were recorded in that frame. Open question: none used there, or the recorder
  misses them.

From the code:

- The Vulkan renderer draws into one 8-bit colour image and a 32-bit depth image that cannot yet
  be sampled. There is no post-effect stage.
- The fast path hands the renderer finished screen-space points (position, colour, texture
  coordinates, fog). No normals, no world positions, no camera matrix.
- Level lighting is largely painted into the models' point colours.
- The game tests object bounds against the view before drawing (`testFrustumAabb`,
  `sub_003BA898`; see `docs/EE_GFX_DATA_MODEL.md`).
- A scene recorder exists (`PS2X_SCENE`), but its dump path draws the player white. It is a
  diagnostic, not the path to build on.

## Approaches considered

| | What it is | Trade-off |
|---|---|---|
| A | Effects on the finished picture, using depth and the camera | Small and safe; no real shadows or lights |
| B | A, plus world positions and normals of what the game draws each frame | Real shadows and lights; off-screen things cast nothing, so shadows can pop |
| C | B, plus the whole fixed scenery of each level held by the renderer | Steady shadows and a base for ray tracing; largest, and one part unproven |

**Picked: C**, by the user, built in the order A, B, C so each stage shows results and nothing is
thrown away. The user accepts a long project and per-level tuning.

## Stage 1: screen effects

- The camera matrix and the game's depth mapping reach the renderer each frame.
- The world is drawn to its own images (higher range colour, readable depth). Effects run on them,
  then the HUD and other 2D are drawn on top.
- Effects: bloom, depth of field, distance and height fog, soft corner darkening, simple light
  shafts, colour grading. Each has an on/off and a strength. Start subtle.
- The game's own fog stays; added fog is on top of it and can be zero.
- Switch and sliders live in the existing debug panel (F1), saved to the settings file.
- Per-level profiles: a small file per level or zone (sun direction and colour, ambient, effect
  strengths). It reloads while the game runs, has a "save" button, and falls back to a default.
- Needs a reliable "current level and zone" value from the game; finding it is part of this stage.

Done when: the user can walk a level, switch Original/Enhanced, tune it and keep the result.

## Stage 2: live 3D shape

- Each drawn point also carries what is needed for world position and normal (positions can be
  derived from screen position and the camera; normals must be added).
- Sun shadows, character shadows, and added point and spot lights placed from the panel
  ("put a light at the camera").
- Fog and light shafts that respect shadows.
- Water reflections (screen-space), with water identified by its textures.
- Added light multiplies with the painted-in lighting, with a per-level strength, so scenes are
  not lit twice. Where a real shadow replaces the game's own blob or volume shadow, the game's is
  hidden in Enhanced.
- Find out where the game's real-time lights are used and reuse them if worthwhile.

Done when: shadows and lights work in a tuned level, and the user has judged how much popping
there is.

## Stage 3: whole level

Starts with a trial, run early (alongside stage 1) because it is the unproven part. Candidates:

1. Read the level's mesh and placement data from game memory.
2. Make the game's view test accept everything at chosen moments and keep what it draws.
3. Fallback: remember fixed scenery as the game draws it during play.

The trial passes if it yields the fixed scenery of the first castle area, including parts behind
the camera, lining up with what the game draws. Characters, monkeys and moving objects keep coming
from the live data of stage 2.

Level geometry is taken on the player's own machine from their own copy. It is never committed or
shipped.

If candidates 1 and 2 both fail, report that to the user before building the fallback.

## Constraints

- Claude specifies and measures; Gemini writes the code.
- Avoid header changes (hours-long rebuild). The point structure is defined three times, in
  `gs_frontend.cpp`, `rd_view.cpp` and `vu1_func.inc`; keep them identical.
- Every step is behind a switch and leaves the game playable.
- Frame rate: locked 60 with Enhanced on the test laptop (RTX 4060, 1080p). The graphics card has
  room; the processor does not. Any added processor work is measured with back-to-back runs, and
  the budget is about 1 ms per frame on the busiest thread.
- Effects have quality levels so weaker machines and later ports can turn them down or off.

## How it is checked

- Original mode: same replay spots before and after, no visible difference and no added frame time.
- Enhanced: screenshots of Original and Enhanced at the same spots, judged by the user.
- At least one outdoor level, one indoor level, one night level and one level with water.

## Left to the builder

Shadow map layout and resolution, blur and bloom methods, image formats, profile file format,
panel layout.

## Open questions

- Should tuned level profiles be committed to the repository? Until decided they stay local. They
  hold only our own numbers, keyed by level name.
- Names and placement of the switch in the game's own options menu (later).
