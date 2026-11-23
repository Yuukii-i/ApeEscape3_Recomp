# FG run log
- FG1 done: see chat. Phase A launched.
- FG2 done: content-key match 70-89% batches, deltas tiny (0.04 px mean), pub 60/s; tick metric invalid (needs matched-only). FG2b launched.
- FG2b done: matched 64-94% batches (unmatched verts 5-37%), all frames move at 60/s => game ticks 60Hz in scenes (no 30Hz). Design: slot-level lerp in rd_view upload path. FG3 launched (fixed t prototype).
- FG3 built: with PS2X_RD_INTERP=1 3D vanishes (hub black, woods HUD only), applyUs 150-420ms/s, counters inconsistent. FG3b fix launched.
