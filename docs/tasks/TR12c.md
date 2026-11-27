# Task TR12c: read vertex fog from the FOG qword. One file. No header edits. Do NOT build/run/commit.
File: c:\ApeEscape3_Recomp\PS2Recomp\ps2xRuntime\src\lib\vu\vu1_func.inc
Facts: these programs output per vertex 4 qwords FOG, ST, RGBAQ, XYZ2 (GIF REGS 0x512a), qOut = first (FOG).
recordClipPolygon / recordRigid / recordSkinned wrongly read the fog byte from qOut+3 (the XYZ2 qword).
1. REMOVE everything added for FIX-TR12/TR12b in this file (gifCarriesFog helper, its calls, hasF, the
   PS2X_RD_FOGSRC counters/logs).
2. At the three lean sites (~2931, ~2995, ~3079) use for the fog only:
   `const uint32_t w3 = ldw(vu, qOut & 0x3FFu, 3u); // FIX-TR12 FOG qword`
   `const float fog = static_cast<float>((w3 >> 4) & 0xFFu) / 255.0f;`
   (keep any other use of the XYZ qword, e.g. ADC at qOut+3, unchanged.)
3. Non-lean paths in the same three functions: next to `sv.adc = ldw(vu, (qOut + 3u) ...)` do not change adc; find
   the converter that derives rv.fog from `sv.adc` (~2495) and say in your reply whether those SceneVertex users
   have access to the FOG qword; do NOT change them.
Reply in <=3 lines.
