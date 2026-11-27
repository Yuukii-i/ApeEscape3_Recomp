# Task SAVE2: a menu dim overlay must not count as a screen clear. One file, NO header edits. Do NOT build/run/commit.
File: PS2Recomp/ps2xRuntime/src/lib/gs/gs_frontend.cpp (large: grep, read small ranges only).
1) Remove every line added for the probe marked // PROBE-SAVE1 (restore the original CUTLOG==2 code exactly;
   `git diff` of this file shows what it changed; do not use git checkout if you cannot, edit it back).
2) Near the isFadeQuad / noColour / wantClearCheck definitions (~6470-6487): a draw with blending on and an alpha test
   that can never pass but still writes colour only (PRIM.ABE=1, TEST ATE bit0=1, ATST bits1-3=0 NEVER,
   AFAIL bits12-13=1 FB_ONLY) is a menu dim overlay, not a clear. Add
   `const bool isDimOverlay = ...; // FIX-SAVE2` (use the same prim/test variables isFadeQuad uses) and add
   `&& !(isDimOverlay && s_rdDimNoClear)` to wantClearCheck only.
   s_rdDimNoClear: function-local static bool, true unless env PS2X_RD_DIMCLEAR is "1".
Comment: "FIX-SAVE2: the save menu draws such an overlay between the 3D scene and the menu; cutting there put the menu
before the next frame's scene. PS2X_RD_DIMCLEAR=1 restores."
Reply in <=2 lines with line numbers.
