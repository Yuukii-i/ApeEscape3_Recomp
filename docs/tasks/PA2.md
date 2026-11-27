# Task PA2: pause screen is black because drawQuad2d still writes 28-byte vertices into a 32-byte-stride pipeline
File: PS2Recomp/ps2xRuntime/src/lib/render/rd_gfx_vk.cpp ONLY. No headers, no other files. DO NOT BUILD/RUN/COMMIT.
Mark changes `// FIX-PA2`. Apply exactly these edits, no other exploring.

In `static void drawQuad2d(` (about line 3607):
1. struct `OverlayVertex` (about line 3619): add a last member `float fog; // FIX-PA2`.
2. Directly after the struct add:
   `static_assert(sizeof(OverlayVertex) == 32, "OverlayVertex must match 32-byte stride"); // FIX-PA2`
3. In the `quad[6]` initialiser (about line 3643) add `, 1.0f` after the uv initialiser of each of the 6 vertices.

Reference: the other OverlayVertex at about line 3479-3519 (FIX-E1b) already does exactly this.
Reply in <=3 lines with the line range touched.
