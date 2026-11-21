# Overhaul plan: "Enhanced" renderer (PS4-era polish on top of the same game)
Status: DRAFT 2026-11-21, written with the user. Owner: user (art direction), Claude (specs, measure), Gemini (code). Nothing here is implemented yet.

## Goal
Same game, same geometry, same textures. Toggle in options: Renderer = Original | Enhanced.
- Original: exactly today's PS2 picture, lowest cost (no extra passes run).
- Enhanced: soft/strong shadows, bloom, fake-wind grass blades and small decoration, volumetric fog and god rays on chosen levels, shiny water with pre-RT reflections (planar or screen-space, not ray tracing), depth of field and motion blur where they suit.
Art direction first: the game's own palette and mood stay. Reference for what NOT to do: the GTA Definitive Trilogy (wrong lighting that broke the art). Every effect has a strength that can be turned down; start subtle.
Ray/path tracing is out of scope (maybe a much later project).

## Per-level profiles (the real work, done by hand)
Each level and zone gets a small data file (JSON): light color and ambient, sun direction, shadow strength/softness/distance, bloom threshold/strength (night levels: weak bloom, soft shadows), fog (color, density, volumetric on/off), god rays on/off, grass zones (which ground materials, density, wind), water params (which texture tags, reflection mode), color grading, DoF/motion blur on/off.
Tooling required before authoring starts (otherwise it is unbearable): hot-reload of profiles while the game runs, an in-game debug panel with sliders per parameter that writes the file, one-key screenshots with fixed camera spots, a "current stage/zone id" readout.
Open: profiles are derived from game identifiers (texture hashes, stage ids): keep them git-ignored/local unless the user decides otherwise.

## Techniques (all rasterised) and what each needs
- Bloom, grading, vignette, sun glow, FXAA/higher res: colour only. Tier 1.
- Depth of field, SSAO, fog, motion blur (camera): need a readable depth buffer + camera matrices/projection (linearise depth). Tier 2.
- Sun shadows + character shadows (replace blob shadows): need geometry from the light's view = world-space positions (camera matrices let us unproject screen-space vertices) + per-level sun direction. Tier 3.
- Volumetric fog / god rays: screen-space light shafts first (needs light screen position); raymarch with the shadow map later. Tier 3.
- Grass blades, small rocks/vines: instanced meshes scattered on triangles of tagged ground materials, vertex-shader wind sway, distance fade. Needs: material tags by texture identity, world positions, a few simple authored meshes + placement lists. Tier 3.
- Shiny water: tag water by texture, planar reflection at low resolution or screen-space reflection, animated ripple/specular. Tier 3.
- Texture replacement (hash-based, upscaled textures, optional normal maps): separate roadmap item, shares the tagging system.
Every effect: switch + quality levels. Lowest level = cheap enough for an i3 8th gen iGPU, or off.

## Architecture requirements for the Vulkan port (so we do not rebuild)
1. Two top-level paths: Original (no post chain, no extra attachments) and Enhanced.
2. Scene pass and UI/2D pass are separate (bloom/DoF must not smear the HUD); the pause/fade/swirl screen effects are handled by the same render-to-texture + full-screen-pass machinery.
3. Own color image with an HDR-capable intermediate format in Enhanced; a sampleable depth image with kept projection parameters.
4. Vertex format with reserved slots: world position, normal, object/material id (empty until filled).
5. Full-screen post chain (ping-pong targets) as a framework, effects as plug-in passes.
6. Shadow pass hook (depth-only pass from a light) and instanced-draw system for decoration.
7. Material tagging layer by texture identity (shared with texture replacement).
8. Profile loader with hot reload + debug panel (drawn in the Vulkan UI layer).
9. Resolution scaling and any aspect ratio (HUD layout rules) in the base design.
10. SPIR-V shaders compiled at build time; permutation count kept small (mobile).

## Research that can run now (PCSX2 is the oracle; no renderer work needed)
- Where the game keeps the camera view/projection matrices and the current camera position each frame.
- The game's own light vectors and colours used for character shading (could seed the per-level sun direction for free).
- Stage id and zone id in RAM (for automatic profile switching); the dev console's warp table may already have them.
- How water and grass-like ground are drawn (texture ids), to design the tagging.
- Whether world-space positions can be recovered from screen vertices + depth + camera matrices at useful precision.

## Order
1. (Now) pause menu stopgap, then the Vulkan port V1-V4 (see chat/plan) with the requirements above.
2. Post chain + Tier 1 effects + profile loader/hot reload/debug panel.
3. Research results -> camera matrices -> Tier 2 effects.
4. Shadows, then grass/decoration, then water, then volumetrics.
5. Per-level authoring pass, level by level, user-driven.

## Decisions still open
- Option names in the game's own menu (Original/Enhanced) and what is exposed per effect.
- Where profiles live in git (see above).
- Minimum hardware tier we promise to keep at 60 fps in Enhanced.
