# Task SAVE3: one small edit. File PS2Recomp/ps2xRuntime/src/lib/gs/gs_frontend.cpp. Do not explore other code, do NOT build.
At about line 6484 there is:  const bool wantClearCheck = rdFrameCutOn() && !prim.tme && addCount > 0u && !isFadeQuad && ... !noColour; // FIX-E8b
Directly BEFORE that statement add:
    // FIX-SAVE2: the save menu draws a dim overlay between the 3D scene and the menu; counting it as a screen clear cut the
    // frame there and put the menu before the next frame's scene. PS2X_RD_DIMCLEAR=1 restores.
    static const bool s_rdDimNoClear = []() { const char *e = std::getenv("PS2X_RD_DIMCLEAR"); return !(e && e[0] == '1'); }();
    const bool isDimOverlay = prim.abe && (ctx.test & 1ull) != 0ull && ((ctx.test >> 1u) & 7ull) == 0ull && ((ctx.test >> 12u) & 3ull) == 1ull;
and inside wantClearCheck add the term  && !(isDimOverlay && s_rdDimNoClear)  next to !isFadeQuad.
Reply "done" or the compile-relevant problem, one line.
