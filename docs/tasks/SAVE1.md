# Task SAVE1 (probe): dump the 2D frame's batch list and cut boundaries on demand. One file, NO header edits.
Do NOT build/run/commit. File: PS2Recomp/ps2xRuntime/src/lib/gs/gs_frontend.cpp (large: grep, read small ranges only).
Context: ~3096-3360 is where the 2D frame is cut and published; the PS2X_RD_CUTLOG=2 block ~3151-3215 dumps "[cutseq]".
Change only that CUTLOG==2 block (mode 2 only):
- Additionally trigger on demand: when the file "logs\\gslog_go.flag" exists (check at most once per 500 ms), set a
  static counter to dump the next 4 flips unconditionally (once per run). These ignore the existing 12-flip cap.
- For those on-demand flips: print all batches (cap 600 instead of 80), and one extra line before them
  "[cutseq-b] flip=%u nB=%zu boundaries: (kb,sb) ..." listing every pair in s_rdBoundaries (first=batch index).
Mark changes // PROBE-SAVE1. Reply in <=2 lines.
