# Task FG2: content-key draw matching + tick-rate probe (stats only, env-gated)
Budget: "[call N/12]", stop at 12. Edit ONLY PS2Recomp/ps2xRuntime/src/lib/render/rd_view.cpp (no headers). DO NOT BUILD/RUN/COMMIT. Mark `// PROBE-FG2`.
Context: FG1 (PS2X_RD_INTERP_STATS=1, already in rd_view.cpp, marked PROBE-FG1) matched batch i to batch i; result: 25-50% unmatched and misaligned deltas when the draw list changes. Read the FG1 code first and reuse its previous-frame copy and statistics helpers.
Do, only when env PS2X_RD_INTERP_STATS2=1 (static bool, one test otherwise):
1. For each batch compute key = 64-bit hash of (tex0, prim, count, alpha, test, rgba+uv of the batch's first vertex, rgba+uv of its last vertex). Do NOT include positions.
2. Build a multimap prev: key -> list of previous-frame batch indices in order. For each new batch, the k-th occurrence of a key in the new frame pairs with the k-th occurrence of that key in the previous frame (if present). Else unmatched.
3. For matched pairs compute per-vertex |dx|,|dy| (pos[0], pos[1], same units as FG1). Report like FG1: mean, p95, max, teleport batches (max delta > 64), plus matchedPct = matched/total batches.
4. Tick-rate: a frame pair is "identical" if matchedPct == 100 and every matched vertex delta < 0.01. Track consecutive identical-frame run lengths; per second print the histogram of run lengths 1,2,3,4+ and the identical ratio. Also print the average microseconds between publishes.
5. Per second line: `[fg2] frames=%u batches=%u matchedPct=%.1f unmatched=%u meanD=%.2f p95D=%.2f maxD=%.1f teleport=%u identicalPairs=%u runs=1:%u 2:%u 3:%u 4+:%u pubUs=%.0f`
6. Nothing else changes; flag unset = one static-bool test.
Accept: compiles; reply <=3 lines with line ranges.
