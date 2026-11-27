# Task TR6: do not paint new 3D over a fade. One file, one small edit. No header edits. Do NOT build/run/commit.
File: c:\ApeEscape3_Recomp\PS2Recomp\ps2xRuntime\src\lib\render\rd_view.cpp. Do NOT explore beyond lines 3600-3830.
Cause (from log): before every loading stall a present takes new 3D (v3nNew3d) without a new 2D list
(!v3nNew2d) while the shown 2D list has a full-screen black fade; the old 2D is ordered before the new 3D, so the
3D covers the black and that picture stays frozen.
1. Directly before `bool wantKeepPrev = ...` (~3787) compute `bool fadeHold = false;` with static bool
   s_fadeHoldOn (env PS2X_FADE_HOLD, default on, '0' disables) and static uint32_t s_fadeHeld = 0.
   If s_fadeHoldOn && v3nNew3d && !v3nNew2d && g_rdGpu.hasCompleteComposition: scan g_rdGpu.local2dBatches
   (still the list currently shown) for a batch that is untextured (prim bit4==0), blending (bit6==1),
   (alpha & 0xFF) == 0x44, whose vertices in g_rdGpu.local2dScratch cover minX<=1, maxX>=511, height>=400, and
   whose first vertex has alpha>=64 and r,g,b all <16 or all >=240. fadeHold = found && s_fadeHeld < 60.
   If found, ++s_fadeHeld, else s_fadeHeld = 0.
2. Make wantKeepPrev true when fadeHold, and make fadeHold bypass the FIX-E8g stale/cap rejection: change
   `if (wantKeepPrev) // FIX-E8g` to `if (wantKeepPrev && !fadeHold) // FIX-E8g`.
Everything else unchanged. Mark lines // FIX-TR6. If a name is not in scope, say so. Reply in <=3 lines.
