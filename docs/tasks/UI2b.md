# Task UI2b: three small insertions. Do NOT explore the codebase, do NOT open other files. Do not build/run/commit.
Paths under PS2Recomp/ps2xRuntime/src/lib/. decodePrimRegister already ignores bits above 10 (checked).

## A. ps2_runtime.cpp, directly AFTER line 2923 `ps2xEeGfxDecompInstall(*this); // DECOMP-BM`, insert:
```cpp
    // FIX-UI2: tag game UI quads with their layer in PRIM's unused upper bits
    if (const char *uiEnv = std::getenv("PS2X_UI_LAYER_LOG"); uiEnv && uiEnv[0] == '1')
    {
        static RecompiledFunction s_uiOrig = nullptr;
        s_uiOrig = lookupFunction(0x003B7798u);
        if (s_uiOrig)
        {
            registerFunction(0x003B7798u, [](uint8_t *rdram, R5900Context *ctx, PS2Runtime *runtime) {
                if (GPR_U32(ctx, 31) == 0x00508D94u)
                {
                    static uint32_t s_tagged = 0u, s_missed = 0u;
                    auto host = [rdram](uint32_t a) -> uint8_t * { return rdram + (a & 0x01FFFFF8u) + (a & 7u); };
                    uint32_t base = 0u;
                    std::memcpy(&base, host(0x006AF340u), 4);
                    const uint32_t s3 = GPR_U32(ctx, 19), s2 = GPR_U32(ctx, 18), end = GPR_U32(ctx, 5);
                    const uint32_t layer = (s3 - base) / 0x20u;
                    const uint32_t trailers = (*host(s2 + 1u) != 0 ? 1u : 0u) + ((*host(s2) & 1u) ? 1u : 0u);
                    const uint32_t prim = end - 0x70u - 0x30u * trailers;
                    uint64_t v = 0ull;
                    std::memcpy(&v, host(prim), 8);
                    if (layer < 35u && (v == 0x14Cull || v == 0x15Cull))
                    {
                        v |= static_cast<uint64_t>(0xA500u | layer) << 32;
                        std::memcpy(host(prim), &v, 8);
                        ++s_tagged;
                    }
                    else
                        ++s_missed;
                    if (((s_tagged + s_missed) % 2000u) == 1u)
                        ps2xSafeLog("[uitag] tagged=%u missed=%u\n", s_tagged, s_missed);
                }
                s_uiOrig(rdram, ctx, runtime);
            });
        }
    }
```
(If `ps2xSafeLog` is not already declared in this file, use the logging call the file already uses.)

## B. gs/gs_frontend.cpp
1. Directly after line `static uint32_t s_rd2dTexCounter = 1u;      // FEAT-RD8` (line 153) insert:
   `static uint32_t s_uiCurLayer = 0xFFu; // FIX-UI2`
2. In writeRegisterUnlocked, at `case GS_REG_PRIM:` (about line 5309), directly before `m_primRegister = decodePrimRegister(value);` insert:
   `s_uiCurLayer = (((value >> 40) & 0xFFu) == 0xA5u) ? static_cast<uint32_t>((value >> 32) & 0xFFu) : 0xFFu; // FIX-UI2`
## C. gs/gs_frontend.cpp, the `// PROBE-UI1` block (about line 6436)
- map key: also OR in `(static_cast<uint64_t>(s_uiCurLayer) << 56)`
- change the cap `64u` to `160u`
- in the `[uilayer]` log line add `layer=%d` right after `fbp=%x`, argument
  `static_cast<int>((entry.first >> 56) == 0xFFull ? -1 : static_cast<int>(entry.first >> 56))`,
  and extract fbp as `static_cast<uint32_t>((entry.first >> 32) & 0xFFFFFFull)`.
Reply in <=3 lines.
