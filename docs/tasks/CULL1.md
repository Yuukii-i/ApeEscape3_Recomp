# CULL1: probe the frustum test. Tiny task. Do NOT build/run/commit. No header edits.
File: PS2Recomp/ps2xRuntime/src/lib/decomp/ee_gfx_decomp.cpp, sub_003BA898_decomp (~line 2912-2953).
Mark every added line `// PROBE-CULL1`. With both variables unset behaviour is unchanged.
1. Env PS2X_NOCULL=1: whenever the function would return 0 (first test), return 1 instead (v0 = 1) and skip
   nothing else needed (do not run the second microprogram).
2. Env PS2X_CULLLOG=1: count calls by result (0, 1, 2; count the would-be 0 even when NOCULL overrides it) and
   once per second print with the project's ps2xSafeLog (declare extern as other files do):
   `[cull] calls=<n> r0=<n> r1=<n> r2=<n> rdK=<g_rdAspectK> nocull=<0|1>`
Use plain static counters. Read env once. Reply in 2 lines.
