# SNOW1: snow is split into three strips by the widescreen HUD layout. Small task. Do NOT build/run/commit.
No header edits. File: PS2Recomp/ps2xRuntime/src/lib/render/rd_view.cpp, the FIX-UI5 loop (~line 4153-4215).
Mark `// FIX-SNOW1`. Env PS2X_SNOW_WIDE=0 restores current behaviour (default on).

Facts: the snow is ~1500 sprites in the game's 512x448 2D space, each at most ~21 px, all textured with one
64x64 texture (TEX0 tw=6 th=6: bits 26..29 and 30..33 of b.tex0), alpha blended. Each sprite is 6 vertices in
local2dScratch (verify how sprites are stored; the batch may hold many). The loop currently anchors such batches
left/centre/right by position, which makes three strips with gaps.

Rule:
1. Before the loop, count "flake quads": over batches with uiTag != 0, textured (prim bit 4), tex 64x64, every
   consecutive 6-vertex quad whose width and height are both <= 32 (game units, before mapping).
2. Only if that count in this frame is >= 100: for those batches (all of whose quads qualify), do not anchor.
   Map each quad as: centre x stays unchanged (qc), so positions span the full width, and the quad keeps its
   normal on-screen shape: v' = qc + (v - qc) * scaleToShader. Do not apply the other anchor rules to them and
   make their scissor x range the whole frame (0 .. fbW-1) if they have a scissor.
3. Log once per run with ps2xSafeLog: `[snow] tag=<uiTag> quads=<count>`.
Reply with the line numbers touched.
