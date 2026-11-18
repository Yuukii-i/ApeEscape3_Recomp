# Direct render path + lighting overhaul plan (2026-11-18)

Goal: draw the game with our own GPU renderer from world-space data, instead of emulating the PS2 GS from
screen-space triangles. One foundation for four user goals: much lower ms/frame, any resolution, any aspect
ratio (fill the window, no black bars), and the lighting overhaul (shadow maps, many lights, SSAO, bloom).

## Baseline (logs/base_on_bench.txt, Release, decomps on, boost mode, 60 fps everywhere)
| stage | CPU ms/frame | biggest threads |
|---|---|---|
| toyhouse_a | 45-46 | GameThread 12.4, Vu1Exec 9.7, Vif1Worker 7.9, GsWorker 6.2, PresentLatch 6.1 |
| space_a | ~24 | |
Emulation side (Vu1Exec + Vif1Worker + GsWorker + PresentLatch) = about 2/3 of CPU. GameThread (the EE game
logic) is the rest. PS2X_PRESENT_GPU=1 gave no gain. Decomps on/off: within noise.

## Why the current design is expensive
EE builds VIF packets -> VU1 program transforms every vertex on the CPU (clip, perspective divide, ftoi4) ->
GIF packets -> GS emulation rasterises into a 4 MB PS2 VRAM image -> readback -> present. Every stage is CPU
work, at PS2 resolution, in PS2 formats. A PC GPU can do the transform + raster for free.

## Capture seam: the VU1 command interpreter
The main VU1 image (86503d39) is a command interpreter (docs/VU1_HLE_PLAN.md). Per vertex it reads a model-space
position P (quad 636+idx), ST and colour streams, the matrix rows vf1/vf2..., and constants (1002/1003/1014/1016),
then writes screen XYZ/ST/RGBAQ into the GIF buffer. So at the per-vertex routine (2440 / 2670) we can capture,
for every batch: model-space positions, normals (lighting handlers), UVs, vertex colours (= baked lighting), the
matrix, and the GS state of the batch (texture, blend, alpha test, Z) from the GIF tag + registers it kicks.
The EE side (DrawObj / MatDesc / LightData / BoneMtx, docs/EE_GFX_DATA_MODEL.md sections 15-16) tells us which
object, material and light set each batch belongs to; the decomp gives us those names.
Capturing at VU1 input (not at the EE) means every EE path that ends in a VU1 draw is covered automatically.

## Phases (each one ships behind an env switch; the GS path stays as fallback and reference)
R0  Capture + CPU check (no rendering). PS2X_RD_CAPTURE=1: at the per-vertex routine record per batch
    {P[], matrix rows, constants, ST, colour, GS state}. Checker: recompute screen XYZ in C++ from the capture
    and compare with what VU1 wrote (exact ftoi4 match, count per frame). Proves we understand the data.
R1  Shadow draw. Same capture fed to a Vulkan pass that draws the batches into its own render target at PS2
    resolution with the captured matrix; image diff vs the GS output (PS2X_GS_COMPARE-style px count).
    First draw type: static level geometry (most of the frame). Then characters (skinning 1FE0 = already
    closed form), then particles/trails/sprites, water, HUD (2D, kept in screen space).
R2  Takeover. For draw types that pass R1, skip the VU1 transform + GS raster entirely (VU1 still runs the
    non-geometry handlers; EE still sees the same VIF/TOP/ITOP state). This is where ms/frame drops.
    Readback-sensitive effects (render-to-texture, framebuffer feedback) stay on the GS until handled.
R3  Resolution + aspect ratio. Our render target can be any size. Aspect: widen the projection (adjust the
    x scale in the captured matrix / the EE projection setup) and anchor the HUD to the screen edges.
R4  Lighting renderer. World-space meshes -> shadow maps (cascaded sun, spot, cube for point lights),
    Forward+ shading, SSAO, bloom, tonemap. Baked vertex colours kept as the ambient/base term, per-stage blend.
R5  In-game light editor. ImGui overlay + free camera (dev console), place/move lights, live shadows, save to
    mods/lighting/<stage>.json, loaded at stage entry; overhaul on/off in the options menu.

## Status
R0 already exists: scene buffer v1 (PERF-SA, docs/LIGHTING_PLAN.md "Scene buffer v1", AUTONOMOUS_LOG section 72).
PS2X_SCENE=1 records per draw {handler 1EE0/1EF0/2440/2900, local->clip matrix, viewport scale/offset, GIF offset/len}
and per vertex {clip-space pos, local normal, STQ, RGBA, emitted screen XYZ}; PS2X_SCENE_CHECK=1 re-projection:
0 mismatches over ~62k verts/frame (shop). Cost ON: 60 -> 44 fps (5 MB/frame written), to trim.
Missing for R1: the GS state per draw (TEX0/blend/test from the GIF packet) and a consumer.

## First verifiable step (next task): R1a geometry view
PS2X_RD_VIEW=1: each presented frame, draw the scene-buffer frame with our own Vulkan pipeline into an offscreen
image at WINDOW resolution (clip-space pos -> GPU, vertex colour, depth test, no textures yet) and show it instead of
the GS image. Acceptance: screenshots of travel_a / toyhouse_a show the level geometry at window resolution in the
right place (matches GS framing), no crash over a 2 min warp run; fps reported.

## Risks
- Batches that VU1 clips (2900+ clip subroutines) produce new vertices: R1 must clip on the GPU instead
  (standard), so screen output differs at clip edges by design; compare inside the frustum only.
- Effects that read the framebuffer (heat haze, screen fades, render-to-texture) need a GS-compatible path
  or a reimplementation; inventory them during R1.
- Multiple VU1 images (d6b2281a, 4279fa21...) have their own layouts; start with 86503d39.
