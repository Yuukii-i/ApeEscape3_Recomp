# Modern lighting plan (final roadmap objective) - design draft, 2026-11-14

Goal (user): PS2 -> "PS3-level" look: real-time shadows, light shafts (god rays), bloom, depth of field. No RT/PT.
Precondition (done or nearly): the VU1 microcode is decompiled into C++ handlers that know what they compute
(docs/VU1_HANDLER_FORMS.md), so the renderer can get SEMANTIC data instead of only finished 2D GIF primitives.

## What the decompiled VU1 code already knows (per draw call / MSCAL)
- Object/bone matrices (00A8 matrix setup; skinned 1FE0 path: per-vertex bone blend), world-space positions before projection
  (1EE0 rigid/skinned: transform -> clip -> project), normals (lighting handlers read them), UV generation (1A68 sphere map,
  1CD8 projective UV).
- Lights: directional x4 diffuse (0198) / specular (02E0), point diffuse (0628) / specular (0840), quadratic point (1720),
  spot diffuse (0CC0) / specular (1090): positions, directions, colours, falloff constants live in fixed VU memory slots
  (982..991, 1010..1017).
- Shadow volumes: 32A0 extrudes silhouette shadow geometry (the game already has dynamic shadows of some kind).
- Back-face cull (0B38), clipping (clipPolygon).

## Architecture (incremental, each step shippable, default-off switch per feature)
1. Semantic side channel: each handler optionally appends a compact record per draw to a per-frame "scene buffer":
   {object id (handler + command addr), world matrix, vertex stream (world pos, normal, uv, colour), material (texture TEX0,
   alpha, blend), light set}. GIF output stays unchanged (the PS2 picture remains the fallback / reference).
2. Vulkan backend: match GIF primitives to scene-buffer records (same order per MSCAL -> 1:1 mapping of emitted vertices),
   so each GS draw run knows its world positions/normals. Build a G-buffer (depth, normal, albedo from the PS2 texture
   sample, emissive) alongside the PS2 colour target.
3. Lighting passes on the G-buffer: (a) shadow maps from the scene buffer's world geometry for the main directional light
   (and the game's own shadow volumes as a hint), (b) light shafts as a screen-space radial blur from the light's screen
   position masked by depth, (c) bloom (threshold + mip-chain blur), (d) depth of field (circle of confusion from depth),
   (e) tone mapping that keeps the original palette feel. Composite over the PS2 image with per-effect strength sliders.
4. UI/config: per-effect toggles + presets; everything off = bit-exact PS2 output.

## Risks / open questions
- Screen-space vs world: PS2 draws 2D after projection; recovering per-pixel world data needs the scene-buffer <-> GIF
  mapping to be robust (fallback per draw: no G-buffer data = no lighting on that draw).
- Pre-lit / baked vertex colours: many PS2 games bake lighting into vertex colours; adding lights on top must not double-light
  (use the decompiled light handlers to separate base colour from computed light where possible).
- Cost: G-buffer + passes on the GPU (RTX 4060 laptop: cheap); CPU side must stay within the ~5 ms/frame spare.

## Order (after audio and bug fixing per the roadmap)
scene buffer + mapping (with a debug view of normals/depth) -> G-buffer -> bloom -> DoF -> shadow maps -> god rays.
