# Task TR5: log what is really drawn for fades and the swirl. Logging only, NO behaviour change.
One file: c:\ApeEscape3_Recomp\PS2Recomp\ps2xRuntime\src\lib\render\rd_view.cpp, function ps2xRdDraw (starts ~3110).
No header edits. Do NOT build/run/commit. All under env PS2X_RD_TRLOG=1 (static bool, one per function is fine),
lines marked // PROBE-TR5, use ps2xSafeLog. ms = steady_clock::now().time_since_epoch() in milliseconds (%lld).
Facts: during a loading stall the screen is redrawn without the black fade although the uploaded 2D list had a
full-screen black quad (alpha 128). Need to know whether it is emitted and whether 3D is drawn after it.
A. Next to `bool palDrawnThisFrame` (~4360): counters trFadeEmit=0, trFadeA=-1, trFadeAt3d=0, trSwirlEmit=0.
B. At the point in emit2dBatch (~5040) where the batch is really going to be drawn (after its early returns):
   if untextured (prim bit4==0), blending (bit6==1), vertices (g_rdGpu.local2dScratch) cover minX<=1, maxX>=fbW-1,
   height>=0.9*fbH (use the fbSize in scope), first vertex r,g,b<16 and alpha>=64: ++trFadeEmit, trFadeA=alpha,
   trFadeAt3d=drawn3dThisFrame. If g_rdSwirlMaskDraw: ++trSwirlEmit.
C. Just before the function's final `return true;` (~8150):
   "[trd] ms=%lld newComp=%d fg10Replay=%d draws3d=%u n2d=%zu fadeInList=%d fadeEmit=%d fadeA=%d at3d=%u\n"
   (fadeInList = max alpha of such black full-screen quads in g_rdGpu.local2dBatches, -1 none.)
   Also: any earlier `return` in ps2xRdDraw reached after the upload stage (after ~4200) logs "[trd] early line=%d".
D. Inside `if (!swirlMask2d.empty())` (FEAT-E4a/E4b block), after the masks are drawn:
   "[trs] ms=%lld masks=%zu emitted=%d view=%d,%d,%d,%d target=%d,%d fb=%.0fx%.0f clipped=%d bbox=%.1f..%.1f,%.1f..%.1f\n"
   (bbox over all mask vertices; target = rw,rh), and for the first 2 and the last mask batch:
   "[trsb] count=%u prim=%llx test=%llx alpha=%llx frame=%llx v0=%.1f,%.1f rgba=%u,%u,%u,%u\n"
If a name is not in scope, say so instead of guessing. Reply in <=4 lines.
