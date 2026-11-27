# Task LSEL2 (temporary probe): list one frame of level-select 2D draws. One file. Do NOT build/run/commit. No headers.
File: PS2Recomp/ps2xRuntime/src/lib/render/rd_view.cpp, FIX-UI5 layout loop (~4111). For batches with uiTag == 17:
env PS2X_LSEL_LOG=1 (static): once per run, when the file "logs\\gslog_go.flag" exists (check once per frame before the
loop), log EVERY uiTag==17 batch of that one frame BEFORE its vertices are modified:
 ps2xSafeLog("[lsel] i=%zu bbox=%d,%d-%d,%d tbp=%04x tex=%d count=%u sc=%llu..%llu\n", index, minX,minY,maxX,maxY,
   (unsigned)(b.tex0 & 0x3FFF), (int)((b.prim>>4)&1), b.count, b.scissor & 0x7FF, (b.scissor>>16) & 0x7FF);
Max 600 lines. Mark every line // PROBE-LSEL2. Reply in <=2 lines.
