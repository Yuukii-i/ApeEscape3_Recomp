# Task LSEL3: move level-select pieces to the screen/area edges; remove the LSEL2 probe. One file. Do NOT build/run. No headers.
File: PS2Recomp/ps2xRuntime/src/lib/render/rd_view.cpp, FIX-UI5 layout loop (~4111-4200, see FIX-LSEL1).
1) Delete every line marked // PROBE-LSEL2.
2) For uiTag == 17 only (and only if env PS2X_LSEL_WIDE not "0", same static as FIX-LSEL1), BEFORE the vertices are
   mapped with mapX, add a horizontal offset to every vertex of the batch, classified from its ORIGINAL bbox
   (minX,maxX,minY,maxY, cx=(minX+maxX)/2, fb space 512x448). Let areaPx=min(w,h*16/9), halfFb=0.5*fbW*areaPx/w,
   d  = max(0, halfFb/scaleToShader - 0.5*fbW)      // edge of the 16:9 level-select area
   dS = max(0, 0.5*fbW/scaleToShader - 0.5*fbW)     // real screen edge
   Rules, first match wins (otherwise offset 0):
   a) "Level Complete" band: cx > 330 && minY < 150 && maxY < 210            -> +dS
   b) bottom bars (Time Attack/Free Play, Cancel/OK): minY >= 372            -> cx < 200 ? -d : +d
   c) counter / best-time row: minY >= 200 && minY <= 245 && maxY <= 275     -> cx < 256 ? -d : +d
   d) arrows: width in 40..56 && height in 28..36 && minY in 255..295 && (cx < 100 || cx > 420) -> cx < 256 ? -d : +d
   Then map as now: vx = mapX(vx + offset).
3) Scissor for tag 17: for the band (rule a) set the batch scissor x range to the whole frame (0 .. fbW-1) so it is
   not cut on screens wider than 16:9. Others keep the FIX-LSEL1 scissor.
Skip full-screen fills (the existing `continue` before this stays). Comment "FIX-LSEL3". Reply <=2 lines.
