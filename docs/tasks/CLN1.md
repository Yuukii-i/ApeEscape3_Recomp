# Task CLN1: remove test-only logging before commit. Deletions only, no behaviour change otherwise.
Do NOT explore beyond the listed lines. No header edits. Do NOT build/run/commit.
Paths under c:\ApeEscape3_Recomp\PS2Recomp\ps2xRuntime\src\lib\ unless full.

1. gs/gs_frontend.cpp: delete `#include <map> // PROBE-UI1` (line 19), the two statics s_uiLayerLog / struct UiLayerAgg
   (about 6205-6208), and the whole `if (s_uiLayerLog) // PROBE-UI1 { ... }` block (about 6440-6500).
   KEEP s_uiCurLayer, the GS_REG_PRIM line and the `// FIX-UI5` b2d.prim line.
2. ps2_runtime.cpp, inside the `// FIX-UI5` wrapper (about 2933-2992): delete the counters s_tagged, s_missed,
   s_textTagged, s_textCalls, their increments and both `[uitag]` ps2xSafeLog statements (an `else ++s_missed;`
   branch goes away entirely). KEEP the tagging writes and the `break` logic.
3. platform/ps2_sdl_platform.cpp: delete the extern line about g_ps2xNoCull (line 69; keep any other declaration on
   that line that is still used elsewhere, e.g. ps2xSafeLog or g_ps2xWsMode), and the F5 `// FIX-WS2` and F6
   `// PROBE-WSD1` key handlers (about 1226-1236). Keep the F1 handler.
4. decomp/ee_gfx_decomp.cpp: delete line 29 (g_ps2xNoCull definition) and the two early-return lines at about
   2915 and 4993 that use g_ps2xNoCull.
5. vu/vu1_func.inc: delete lines about 57 and 2244 that use g_ps2xNoCull.
6. c:\ApeEscape3_Recomp\recomp_source\sub_003BA898_0x3ba898.cpp line 25 and
   c:\ApeEscape3_Recomp\recomp_source\sub_003BAAC0_0x3baac0.cpp line 24: delete that single `// PROBE-WSD1` line only.
Afterwards no occurrence of g_ps2xNoCull, PROBE-UI1, PROBE-WSD1 or "[uitag]" may remain in these files.
Reply in <=4 lines.
