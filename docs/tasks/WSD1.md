# Task WSD1 (small): F6 switch that disables culling (diagnostic). Apply these 6 edits only.
Do NOT explore, do NOT read other files, no .h edits, no build/run/commit. Keep all existing FIX-WS1 lines. Mark `// PROBE-WSD1`.
Paths are under PS2Recomp/ps2xRuntime/src/lib/ unless they start with recomp_source/.

1. decomp/ee_gfx_decomp.cpp, near line 28 (by `extern float g_rdAspectK;`), global scope, add definitions:
   `int g_ps2xNoCull = 0; unsigned g_ps2xNoCullCalls[3] = {0, 0, 0}; // PROBE-WSD1`
2. Same file, first lines inside `sub_003BAAC0_decomp` (~line 4990) and inside `sub_003BA898_decomp` (~line 2913):
   BAAC0: `++g_ps2xNoCullCalls[0]; if (g_ps2xNoCull & 1) { SET_GPR_U64(ctx, 2, 2ull); ctx->pc = GPR_U32(ctx, 31); return; } // PROBE-WSD1`
   BA898: same line with `[1]` and `& 2`.
3. recomp_source/sub_003BAAC0_0x3baac0.cpp: right after `ctx->pc = 0x3baac0u;` add ONE line:
   `{ extern int g_ps2xNoCull; extern unsigned g_ps2xNoCullCalls[3]; ++g_ps2xNoCullCalls[0]; if (g_ps2xNoCull & 1) { SET_GPR_U64(ctx, 2, 2ull); ctx->pc = GPR_U32(ctx, 31); return; } } // PROBE-WSD1`
4. recomp_source/sub_003BA898_0x3ba898.cpp: same after `ctx->pc = 0x3ba898u;` with `[1]` and `& 2`.
5. vu/vu1_func.inc: next to `extern float g_rdAspectK; // FIX-WS1` (~line 55) add
   `extern int g_ps2xNoCull; extern unsigned g_ps2xNoCullCalls[3]; // PROBE-WSD1`
   In `clipBitsV` (~line 2226), just before `return fl;`:
   `++::g_ps2xNoCullCalls[2]; if (::g_ps2xNoCull & 4) fl &= ~3u; // PROBE-WSD1`
6. platform/ps2_sdl_platform.cpp: at global scope near line 67 (`extern void ps2xPadMarker();`) add
   `extern int g_ps2xNoCull; extern unsigned g_ps2xNoCullCalls[3]; extern void ps2xSafeLog(const char *fmt, ...); // PROBE-WSD1`
   After the F7 handler (~line 1195), inside `case SDL_EVENT_KEY_DOWN`:
```cpp
if (ev.type == SDL_EVENT_KEY_DOWN && !ev.key.repeat && ev.key.scancode == SDL_SCANCODE_F6) // PROBE-WSD1
{
    g_ps2xNoCull = g_ps2xNoCull == 0 ? 1 : g_ps2xNoCull == 1 ? 2 : g_ps2xNoCull == 2 ? 4 : g_ps2xNoCull == 4 ? 7 : 0;
    ps2xSafeLog("[nocull] mode=%d calls sphere=%u aabb=%u vu1=%u\n", g_ps2xNoCull, g_ps2xNoCullCalls[0], g_ps2xNoCullCalls[1], g_ps2xNoCullCalls[2]);
}
```
Reply in <=4 lines: which edits were applied.
