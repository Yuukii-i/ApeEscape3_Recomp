# Task LSEL4: two rule fixes in FIX-LSEL3 (rd_view.cpp, FIX-UI5 loop). One file. Do NOT build/run. No headers.
tbp = (b.tex0 & 0x3FFF) of the batch.
a) band rule becomes: (textured && tbp == 0x3ec0 && minY < 200) || (existing position condition).
   (the rotating burst's pieces otherwise stay behind). The band scissor handling applies to both.
d) arrows rule becomes: textured && tbp == 0x2e00 && minY >= 255 && minY <= 300  ->  cx < 256 ? -d : +d
   (drop the width/height conditions).
textured = ((b.prim >> 4) & 1) != 0. Keep rule order. Comment "FIX-LSEL4". Reply <=2 lines.
