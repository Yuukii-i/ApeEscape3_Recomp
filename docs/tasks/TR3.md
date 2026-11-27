# Task TR3: stretch untextured effects; add a per-frame transition log. No header edits. Do NOT build/run/commit.
Do NOT explore beyond the places named. Dir: c:\ApeEscape3_Recomp\PS2Recomp\ps2xRuntime\src\lib
A. render/rd_view.cpp, layout loop `for (Rd2DBatch &b : g_rdGpu.local2dBatches)` (~4111). Cause: unlabelled
   batches (uiTag == 0) are moved left/right/centre one by one, which scatters the swirl's triangles and
   shortens letterbox bars. After the whole `if (s_uiLayout && uiTag != 0u) {...}` block and BEFORE
   `const bool isWide` add (env PS2X_FX_STRETCH, default on, '0' disables; static bool):
     if (s_fxStretch && uiTag == 0u && ((b.prim >> 4) & 1ull) == 0ull) continue; // FIX-TR3 untextured effects stretch
B. Log, only when env PS2X_RD_TRLOG=1 (static bool), mark lines // PROBE-TR3. Use ps2xSafeLog. Time is
   `ms` = duration_cast<milliseconds>(std::chrono::steady_clock::now().time_since_epoch()).count() as %lld.
 1. render/rd_view.cpp: once per draw call, just before the layout loop above (vertex bounds still original),
    scan g_rdGpu.local2dBatches: untextured (prim bit4 == 0), blending (prim bit6 == 1), bounds covering
    minX<=1, maxX>=fbW-1, height >= 0.9*fbH (use batchBounds). From the first vertex in
    g_rdGpu.local2dScratch[b.first].rgba: blackA = max alpha where r,g,b all < 16; whiteA = max alpha where
    r,g,b all > 111 (include 128 grey-white). Also count all batches matching isRdSwirlMask(b).
    Log: "[tr] ms=%lld black=%d white=%d swirl=%u n2d=%zu\n" (-1 for black/white when no such batch).
 2. gs/gs_frontend.cpp, right after `const bool useClassic = ...` (~2870): log
    "[trl] ms=%lld classic=%d repeat=%d geom=%d fx=%d\n" with useClassic, useRepeat, frameHasGeom, fxNow.
If a needed name is not in scope, say so instead of guessing. Reply in <=4 lines with the line ranges touched.
