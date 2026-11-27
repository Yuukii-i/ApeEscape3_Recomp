# Task UI1 (probe only): log the depth value of 2D draws, grouped per second
File: PS2Recomp/ps2xRuntime/src/lib/gs/gs_frontend.cpp ONLY. No headers, no other files. DO NOT BUILD/RUN/COMMIT.
Mark `// PROBE-UI1`. No behaviour change; when env is off the cost is one static bool test.

1. Add `#include <map>` beside the other standard includes (if not already there).
2. Near the other file-scope statics before the 2D capture function, add:
   - `static const bool s_uiLayerLog` = env `PS2X_UI_LAYER_LOG` is "1".
   - `struct UiLayerAgg { uint32_t count; float x0, y0, x1, y1; uint32_t tbp; };`
3. In the 2D capture code, directly after the line `b2d.scissor = rdPackScissor(ctx); // FEAT-RD22` (about line 6430), inside `if (s_uiLayerLog) { ... }`:
   - static `std::mutex`, static `std::map<uint64_t, UiLayerAgg>`, static steady_clock start and lastFlush.
   - z = `static_cast<uint32_t>(triVerts[addCount - 1u].pos[2])`; key = (uint64_t(ctx.frame.fbp) << 32) | z.
   - bbox = min/max of pos[0], pos[1] over the addCount vertices; merge into the entry (union), ++count,
     tbp = `ctx.tex0.tbp0` if prim.tme else 0xFFFF (keep the latest). Do not insert new keys once the map has 64.
   - If >= 1000 ms since lastFlush: for each entry print with ps2xSafeLog:
     `[uilayer] t=%.1f fbp=%x z=%u n=%u bbox=%.0f,%.0f,%.0f,%.0f tbp=%x\n` (t = seconds since start), then clear the map.
Reply in <=3 lines with the line ranges touched.
