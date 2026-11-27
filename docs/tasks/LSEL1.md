# Task LSEL1: level select clips to a 16:9 area instead of 4:3. One file, small edit. Do NOT build/run/commit. No headers.
File: PS2Recomp/ps2xRuntime/src/lib/render/rd_view.cpp, FIX-UI5 layout loop (~4111-4160): UI-tagged batches are scaled
around the centre (vertex x via mapX, anchor 0) and, in `if (anchor == 0 && b.scissor != 0ull)` (~4143), their
scissor is mapped the same way, which hides everything outside the 4:3 box.
Level select is uiTag == 17 (game UI layer 16). Its carousel icons are already generated far outside 4:3.
Change: for uiTag == 17 only (positions unchanged), when the batch's ORIGINAL scissor spans the whole frame
(sx0 <= 1 and sx1 >= fbW - 2), set the new scissor x range to the "16:9 area" instead of mapX of the old one:
  areaPx = min(w, h * 16/9)  (w,h = the screen size already used in this block);
  halfFb = 0.5f * fbW * areaPx / w;  n0 = floor(0.5f*fbW - halfFb);  n1 = ceil(0.5f*fbW + halfFb) - 1; clamp 0..2047.
If the original scissor is not full width, keep the existing mapping. Env PS2X_LSEL_WIDE=0 disables (static bool).
Also check whether these batches have b.scissor == 0 (meaning no scissor) - if so nothing is needed for them.
Comment: "FIX-LSEL1: level select shows up to 16:9 of its carousel".
Reply with line numbers, <=2 lines.
