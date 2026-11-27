# Task FG1: geometry-interpolation feasibility probe (stats only, zero visual change, env-gated)
Budget: "[call N/12]", stop at 12. Edit ONLY PS2Recomp/ps2xRuntime/src/lib/render/rd_view.cpp (no headers). DO NOT BUILD/RUN/COMMIT. Mark `// PROBE-FG1`.
Why: to render >60 fps we blend two real game states (docs/PERFORMANCE.md route B). Before building that, measure whether consecutive 3D frames can be matched draw by draw and how far vertices move. No stable object id exists (docs/VU1_MAP.md), so matching is by position in the batch list + state.
Read first: rd_view.cpp RdVert/RdBatch/Rd3DFrame (L366-426), ps2xRdPublishLean (L1145-1209), ps2xRdPublish (L1211+). RdVert.pos is the post-projection value the renderer draws with; RdBatch has prim/tex0/alpha/test/camHash/vpS/vpO/kickSerial.
Do (only when env PS2X_RD_INTERP_STATS=1, read once into a static bool):
1. Keep a static copy of the previous published 3D frame (verts, batches) inside the publish path (under g_rdMutex, swapped with the incoming data BEFORE the slot swap, or copied; copy cost is fine for a probe).
2. For each new frame, match batch i of the new frame to batch i of the previous one. A pair "matches" when count, prim, tex0 and alpha/test are equal. Also count a second, greedy matching: for unmatched new batches, search forward in the previous list (window 16) for the first with identical (count, prim, tex0).
3. For matched pairs compute per-vertex screen delta: dx=|x1-x0|, dy=|y1-y0| using pos[0], pos[1] (document in a comment whether these are pixels or GS 12.4; use RdBatch.vpS/vpO only if needed). Collect: mean, p95, max of max(dx,dy) over all matched vertices, and the number of batches whose max delta > 64 px ("teleport", must not be interpolated).
4. Once per second print: `[fg1] frames=%u batches=%u posMatch=%u greedyMatch=%u unmatched=%u verts=%u meanD=%.2f p95D=%.2f maxD=%.1f teleportBatches=%u camHashChanged=%u` (camHashChanged = batches whose camHash differs from the matched previous batch).
5. Nothing else changes. With the env var unset the code path must cost one static-bool test.
Accept: compiles; reply <=3 lines with line ranges.
