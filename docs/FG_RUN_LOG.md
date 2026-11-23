# FG run log
- FG1 done: see chat. Phase A launched.
- FG2 done: content-key match 70-89% batches, deltas tiny (0.04 px mean), pub 60/s; tick metric invalid (needs matched-only). FG2b launched.
- FG2b done: matched 64-94% batches (unmatched verts 5-37%), all frames move at 60/s => game ticks 60Hz in scenes (no 30Hz). Design: slot-level lerp in rd_view upload path. FG3 launched (fixed t prototype).
- FG3 built: with PS2X_RD_INTERP=1 3D vanishes (hub black, woods HUD only), applyUs 150-420ms/s, counters inconsistent. FG3b fix launched.
- FG3b fixed: 3D renders correctly with PS2X_RD_INTERP=1 T=0.5 (hub, woods), applyUs ~0.5ms; committed locally.
- FG4 (display pacing, extra presents) launched.
- FG4 built: fg4 enabled but extraPresents=0 skipped=0 (loop breaks immediately). FG4b diagnose+fix launched.
- FG4b works: hub rate2 118 presents/s on 180Hz (pm=0). But woods rate2 collapses to 15 fps, hub rate3 ~50. FG4c instrument+cut cost launched.
- FG4c: hub rate3 110 extras/s ok; woods rate2 extras skipped by overrun guard (drawRealMs 9.2, extra would double) => game stays 60. Cost = ps2xRdDraw itself. FG5 draw-cost instrumentation launched.
