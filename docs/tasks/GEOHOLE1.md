# GEOHOLE1: draw-state ring too small. One-line fix. Do NOT build/run/commit. No header edits.
File: PS2Recomp/ps2xRuntime/src/lib/render/rd_texture.cpp, line ~77:
    constexpr uint32_t kRdRingSize = 65536u; // FEAT-RD5
Change the value to 1u << 19 (524288) and add `// FIX-GEOHOLE1: states were overwritten before late frames drew`.
It must stay a power of two. Check that nothing in this file assumes 65536 elsewhere (a literal mask or size);
report it if so, do not change anything else. Reply in at most 2 lines.
