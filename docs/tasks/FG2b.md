# Task FG2b: improve FG2 matching + fix tick-rate metric (stats only)
Budget: "[call N/12]", stop at 12. Edit ONLY PS2Recomp/ps2xRuntime/src/lib/render/rd_view.cpp (no headers). DO NOT BUILD/RUN/COMMIT. Mark `// PROBE-FG2b`. Same env gate PS2X_RD_INTERP_STATS2=1; replace the `[fg2]` line by the `[fg2b]` line below (keep old code compiling or delete it).
Result of FG2 (logs/fg2_*_err.txt): matchedPct 70-89% only; identicalPairs always 0 because it required 100% matched. Likely causes: the key included first/last vertex rgba+uv, which change with lighting/animation; draw list reorders.
Do:
1. Three-tier matching per frame pair, each tier only over still-unmatched batches (k-th occurrence pairing inside a key group, in list order):
   tier1 key = hash(tex0, prim, count, alpha, test, first+last vertex rgba+uv) (as FG2);
   tier2 key = hash(tex0, prim, count, alpha, test, first vertex uv and last vertex uv only);
   tier3 key = hash(tex0, prim, count).
   Report per second the matched counts per tier and the total matchedPct; also `unmatchedVerts` (sum of counts of unmatched new batches) and its % of all vertices (this matters more than batch %).
2. Per-vertex delta stats only for tier1+tier2 pairs (tier3 pairs only counted). Teleport = batch max delta > 64 px.
3. Tick metric on MATCHED vertices only: movers = number of matched vertices with delta >= 0.05 px. For each published frame record movers==0 (still) or not. Keep a 32-bit history; print it as a 32-char string of 'S' (still) and 'M' (moving), newest last, once per second. Also print stillPct over the last second.
4. Line: `[fg2b] frames=%u matchedPct=%.1f t1=%u t2=%u t3=%u unmatched=%u unmatchedVertPct=%.1f meanD=%.3f p95D=%.2f maxD=%.1f teleport=%u stillPct=%.0f hist=%s`
Accept: compiles; reply <=3 lines with line ranges.
