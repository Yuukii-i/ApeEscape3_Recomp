# Task TR7: full-screen fades must be drawn after all 3D. One file. No header edits. Do NOT build/run/commit.
File: c:\ApeEscape3_Recomp\PS2Recomp\ps2xRuntime\src\lib\render\rd_view.cpp, function ps2xRdDraw.
A. REMOVE the whole `// FIX-TR6` code added near line 3787: restore exactly
   `bool wantKeepPrev = (candDrawable3d == 0u && g_rdGpu.prevDrawn3dCount > 0u) || rejectPartial; // FEAT-RD34 // FEAT-RD37`
   and `if (wantKeepPrev) // FIX-E8g`.
B. Cause: draw2dUntil (~5380) interleaves 2D between 3D batches by serial, so newer 3D paints over the fade quad.
   1. Just before `auto draw2dUntil`, compute `size_t fadeFirstIdx = SIZE_MAX;` = index of the first batch in
      g_rdGpu.local2dBatches (index < n2d) that is: untextured (prim bit4==0), blending (bit6==1),
      (alpha & 0xFF)==0x44, vertices in g_rdGpu.local2dScratch cover minX<=1, maxX>=511, height>=400, first
      vertex alpha>=1 and r,g,b all <16 or all >=240. static bool env PS2X_FADE_LAST, default on, '0' disables.
   2. In draw2dUntil's while condition add `&& (drawAll || i2d < fadeFirstIdx)`, and add the same
      `(drawAll || j < fadeFirstIdx)` to the inner batch-merge while condition. Nothing else.
Mark // FIX-TR7. Reply in <=3 lines.
