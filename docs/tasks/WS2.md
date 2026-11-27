# Task WS2 (small): widescreen narrows X twice; add F5 switch. Apply these edits only.
Do NOT explore beyond the named spots, no .h edits, no build/run/commit. Mark `// FIX-WS2`.
Fact: with aspect=fill, X is divided by k twice (VU1 matrix 998..1001 in ps2_vu1_core.cpp AND uVpB.z in rd_view.cpp).
Mode: 1 (default) = matrix only, 2 = shader only, 0 = both (old behaviour). Paths under PS2Recomp/ps2xRuntime/src/lib/.

1. render/rd_view.cpp, after `float g_rdAspectK = 1.0f;` (~line 1594), global scope: `int g_ps2xWsMode = 1; // FIX-WS2`
   Make sure the lines below can see it (they are after this line).
2. render/rd_view.cpp ~4756: `const float k = (g_ps2xWsMode != 1 && g_rdAspectK > 1.0f) ? g_rdAspectK : 1.0f;`
   ~5953 and ~6489 (the `vpB[4]` initialisers): same condition `(g_ps2xWsMode != 1 && g_rdAspectK > 1.0f)` for the 3rd element.
   Do not change any other use of g_rdAspectK in this file.
3. vu/ps2_vu1_core.cpp ~3574 add `extern int g_ps2xWsMode; // FIX-WS2`; ~3595:
   `const float k = (g_ps2xWsMode != 2) ? g_rdAspectK : 1.0f;`
   In the `else` branch of `if (k > 1.0f)` (~3617), before `s_hasScaled998 = false;`: if `s_hasScaled998` and
   `std::memcmp(vuData + 998u * 16u, s_lastScaled998, sizeof(s_lastScaled998)) == 0`, memcpy s_lastOrig998 back into vuData + 998u*16u.
4. vu/vu1_func.inc: next to `extern float g_rdAspectK; // FIX-WS1` add `extern int g_ps2xWsMode; // FIX-WS2`.
   In both FIX-WS1 conditions (clipBitsV ~2230 and effSgn ~3137) add `&& ::g_ps2xWsMode != 1`.
5. platform/ps2_sdl_platform.cpp:
   a) next to the `// PROBE-WSD1` extern line add `extern int g_ps2xWsMode; // FIX-WS2`
   b) beside the F6 handler add: on F5 key down (no repeat) `g_ps2xWsMode = g_ps2xWsMode == 1 ? 2 : g_ps2xWsMode == 2 ? 0 : 1;`
      then `ps2xSafeLog("[wsmode] mode=%d\n", g_ps2xWsMode);`
   c) in the F6 handler replace the cycle expression with `g_ps2xNoCull = (g_ps2xNoCull + 1) % 4;`
Reply in <=4 lines: which edits were applied.
