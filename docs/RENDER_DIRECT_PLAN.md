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

## Status 2026-11-19 (RD1-RD32 + config)
Done and verified against the GS picture in 29 sampled stages (boot, FMV, title, gameplay): geometry, textures (exact per kick,
render-target pages synced), blend/alpha/AFAIL/DATE semantics, HUD, drop shadows, viewport/FOV, any-aspect fill (Hor+ via the
VU1 view-projection + decomp EE frustum), texture replacement by content hash, ps2x.ini. Opt-in: renderer = new (PS2X_RD_VIEW +
PS2X_RD_TAKEOVER). Window-resolution rendering for free. CPU ms/frame, takeover vs classic, same-session (22:01-22:09 run +
later): -11% avg (castle 35.1/40.4, space 21.8/27.9, woods 40.7/44.6, toyhouse 53.8/56.1).
Known gaps: studio_e TV picture, boss intro light-beam passes (unverified), PS2X_ASPECT=fill for the 2D side is heuristic.

## Where the time still goes (woods_a, takeover, ms/frame): GameThread 12, Vu1Exec 10, GsWorker 6, Vif1Worker 6, GL thread 4, main 2
- Vu1Exec 10: the VU1 vertex programs still run on the CPU only to produce the clip-space vertices we record, and the GIF
  packets the GS frontend then ignores (raster is skipped for geometry draws).
- GsWorker 6: still parses all GIF vertex data of geometry kicks (kicks=5.5 ms in the PS2X_GW split) just to track state.

## R2b: GPU vertex transform (next big step, est. -8..-10 ms/frame = -20%)
Idea: in takeover mode do not run the VU1 FMAC pipeline for the geometry handlers (1EE0/1EF0 skinned, 2440 rigid, 2900 clip).
Record their INPUTS instead (model-space positions at VU quad 636+idx, normals 556+idx, ST/colour streams, matrix quads 998..1001
and 978..981, bone matrices, the index list) and let the vertex shader do the transform, skinning and perspective divide on
the GPU; the VU1 culls via ADC bits (back faces, off-screen) which the GPU needs as per-triangle flags or equivalent tests.
Steps, each verified by pixel diff against the current recorded-clip-space path (scene buffer already gives the reference):
 1. Inventory: for each geometry handler, which VU memory regions are inputs and which outputs feed later handlers (the
    dispatcher/vi15 control flow must stay exact; docs/VU1_DECOMPILE_PLAN.md says outputs are a pure function of entry memory).
 2. Shadow recording (check mode): record inputs AND clip-space outputs; a GPU/CPU reference transform of the inputs must
    reproduce the recorded outputs (same discipline as PS2X_SCENE_CHECK). Gate: 0 mismatches on the warp tour.
 3. Switch: with PS2X_RD_GPUXF=1 the handlers skip the FMAC work and the GIF output (state/tag still emitted for the GS state
    tracker), unrecognised variants fall back to the exact path per MSCAL.
 4. Shrink the GS side: geometry kicks emit only the tag + A+D state (no vertex qwords) so GsWorker parses ~nothing for them.
Risks: culling (ADC) semantics, clipping of near-plane crossings (GPU clips natively), fog/Q values (STQ perspective), morph (15E0
lerp) and the special UV generators (1A68, 1CD8) need their own input recording.

### R2b step 1 findings (read-only inventory of vu1_func.inc, 2026-11-19)
- Inputs (all handlers): stream pointers from quad 1018 (+vi12): s2base/s3base/i4base, N = ILW.w 1018; output base ubase = ILW.z 1023;
  positions 636+idx, normals 556+idx, 716+idx, 796+idx; constants 1002/1003 (viewport), 1014/1016, 1013, 1012; rigid path chosen by ILW.y 1011 < 0.
- Skinned (1EE0/1EF0, ~90% of draws): positions at 636+idx are ALREADY the output of the 00A8 table loop (matrix * input table); the handler
  itself mostly does 1/W, viewport scale, ftoi4 and copies the ST/colour streams. ADC for skinned = bit 15 of the INDEX WORD (word 3 of the
  XYZF2 qword is idx & 0xFFFF), i.e. an INPUT, not an FMAC result -> culling needs no VU math for skinned meshes. (idx bit 15 is harmless for the
  636+idx lookup because 32768 = 32*1024 and the quad index wraps with & 0x3FF.)
- Rigid (2440): positions raw from 636+ix, but the ADC/clip bits and screen XYZ come from the FMAC clip machine (ftoi16 of clamped w + 2048 flag);
  clip polygons (2900) are entirely FMAC-derived (Sutherland-Hodgman over 6 planes, count drives the GIF tag at quad 876).
- Dispatcher-visible state after the geometry handlers is tiny: vi12 plus R.I=255 and the valid masks; internal flags are not exported.
=> Plan refinement: the first GPU-transform target is the 00A8 table loop + skinned 1EE0/1EF0 (largest cost, simplest outputs); rigid/clip stay on the
   exact CPU path until the skinned path is verified. Measure with the existing per-handler timers (lbTimed / PS2X_VU1_TSC) before coding.
