# Task WW2: make the PROBE-WW1 store trace usable for long runs (cpp only, no header)
Budget: "[call N/12]", stop at 12. Edit ONLY PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp. DO NOT BUILD/RUN/COMMIT. Mark `// PROBE-WW2`.
Context: ps2xGuestWriteHit (PROBE-WW1, ~ps2_runtime.cpp L9154-9251) logs at most 400 hits, and the first 400 are always used up by a file copy at vbl~52, so the interesting writes (rope fall, hundreds of vblanks later) are never logged.
Do:
1. New env PS2X_WWATCH_AFTER=<vbl> : ignore (do not count, do not log) hits while the vblank counter is < that value (the same counter printed as vbl=). Default 0.
2. New env PS2X_WWATCH_MAX=<n> : max logged hits (default 400, clamp 1..200000).
3. New env PS2X_WWATCH_SIZE4=1 : ignore hits whose size != 4 (so byte-wise copies are skipped).
4. Each logged line additionally prints the previous float value at that address if cheaply known (read the guest RAM word BEFORE the write is not possible; skip this) -- instead print `n=%u` (per-sym hit counter at that moment). Keep the line format otherwise identical.
Acceptance: compiles. Reply <=4 lines with line ranges.
