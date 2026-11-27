# Task UI5: lay out 2D draws by their UI label. Three .cpp files, exact edits only. No header edits. Do NOT build/run/commit.
Paths under PS2Recomp/ps2xRuntime/src/lib/. Mark `// FIX-UI5`. Do not explore beyond the regions named.

## A. ps2_runtime.cpp (the `// FIX-UI2` block, about line 2955-3040)
1. Install condition: instead of requiring PS2X_UI_LAYER_LOG=="1", install unless env `PS2X_UI_TAG` starts with '0'.
2. Remove the PROBE-UI3 probe completely: helper ps2xUiRaCount, map s_uiRa, its calls, and the whole 0x003B7840 wrapper.
   Keep the 0x003B7798 wrapper (sprite and text tagging) unchanged.

## B. gs/gs_frontend.cpp, line `b2d.prim = rdPackPrim(prim);` (about line 6427)
Directly after it:
    // FIX-UI5: bits 48..55 = UI label (0 = none, else queue index + 1; text = 255)
    if (s_uiCurLayer != 0xFFu) b2d.prim |= static_cast<uint64_t>((s_uiCurLayer + 1u) & 0xFFu) << 48;

## C. render/rd_view.cpp, the layout loop `for (const Rd2DBatch &b : g_rdGpu.local2dBatches)` (about line 4108)
1. Make it `for (Rd2DBatch &b : g_rdGpu.local2dBatches)`.
2. Directly after the existing `bw`, `bh`, `cx`, `dc` computations and before `isWide` is used to `continue`, insert:
```cpp
                static const bool s_uiLayout = []{ const char *e = std::getenv("PS2X_UI_LAYOUT"); return !(e && e[0] == '0'); }(); // FIX-UI5
                const uint32_t uiTag = static_cast<uint32_t>((b.prim >> 48) & 0xFFull);
                if (s_uiLayout && uiTag != 0u) // FIX-UI5
                {
                    if (minX <= 1.0f && maxX >= fbW - 1.0f && bh >= 0.9f * fbH)
                        continue; // full-screen fade/fill stretches
                    const uint32_t q = uiTag - 1u;
                    const float c = 0.5f * fbW;
                    int anchor = 0; // 0 centre (menus, text, everything else), 1 left, 2 right
                    if (q == 11u) anchor = 1;                     // health cookies
                    else if (q == 10u) anchor = 2;                // gadget ring
                    else if (q == 5u && !(bw >= 0.8f * fbW) && !(dc >= -0.1f * fbW && dc <= 0.1f * fbW))
                        anchor = (cx < c) ? 1 : 2;                // mixed HUD layer
                    const auto mapX = [&](float v) -> float {
                        if (anchor == 1) return m + v * scaleToShader;
                        if (anchor == 2) return fbW - m - (fbW - v) * scaleToShader;
                        return c + (v - c) * scaleToShader;
                    };
                    for (uint32_t k = 0u; k < b.count; ++k)
                    {
                        float &vx2 = g_rdGpu.local2dScratch[b.first + k].pos[0];
                        vx2 = mapX(vx2);
                    }
                    if (anchor == 0 && b.scissor != 0ull) // keep off-frame items hidden
                    {
                        const float sx0 = static_cast<float>(b.scissor & 0x7FFull);
                        const float sx1 = static_cast<float>((b.scissor >> 16) & 0x7FFull);
                        const float n0 = std::max(0.0f, std::min(2047.0f, std::floor(mapX(sx0))));
                        const float n1 = std::max(0.0f, std::min(2047.0f, std::ceil(mapX(sx1 + 1.0f)) - 1.0f));
                        b.scissor = (b.scissor & ~(0x7FFull | (0x7FFull << 16))) |
                                    static_cast<uint64_t>(n0) | (static_cast<uint64_t>(n1) << 16);
                    }
                    continue;
                }
```
Unlabelled batches keep the existing behaviour.
If `b` being non-const conflicts with something in the loop, report it. Reply in <=4 lines.
