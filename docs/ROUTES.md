# Pad-replay routes (PS2X_PAD_PLAY=<file>, F7 markers in <file>.marks, PS2X_PAD_STOP_MARK=<n> stops at marker n)
Polls run at ~119/s (2 per frame). Marker poll = index into the recording. Recorded in SILENT mode, audio driver OFF.

## logs\levels_run.padrec (main route, 2026-11-14, no monkeys caught, 25800 polls)
| mark | poll | where |
|---|---|---|
| 1 | 1258 | title |
| 2 | 2303 | lobby |
| 3 | 3230 | shop |
| 4 / 5 | 5506 / 7566 | level 1 enter / exit (Apotos-like town + beach) |
| 6 / 7 | 10140 / 11506 | level 2 enter / exit (forest; 2nd part is the heavy one) |
| 8 / 9 | 14086 / 17584 | level 4 enter / exit (city, small train, cars; bad slowdowns) |
| 10 / 11 | 19900 / 25148 | level 5 enter / exit (recording studio; 3 doors, 2 visited) |
| after 11 | -> end | level 6 (halloween): crashes when falling into water (end of recording) |
Stage dirs loaded in order: travel_a/b (lobby/hub), warpgate, seaside_a/b (L1), woods_a/b (L2), ciscocity_a (L4),
studio_a/b(/d) (L5), halloween_a (L6). Replay verified 2026-11-14: replay to mark 11 loaded the identical 354-file
sequence as the recording (deterministic in silent, audio off).
Level-exit pad pattern (backup if markers fail): Start, Up, X, Up, X (slow).

## logs\levels_monkeys.padrec (monkey / graphics route, 34200 polls, 7 marks; crashed ~30 s after mark 7)
marks: 1 1508, 2 2828, 3 3954, 4 5980, 5 13710, 6 20916, 7 29873 (locations: ask user / not yet given)

## Known crashes (bug phase, all pre-existing per user)
- Level 3 (castle): crashes on enter. Boss 1 (monkey in mecha dragon) reuses its assets: untested.
- Level 5 (studio): the door to the gymnastics studio crashes (PS2 also stutters there).
- Level 6 (halloween): falling into water crashed (since first gameplay). FIXED 2026-11-16 (C423, FIX-CR2): split
  function at a jal delay slot left the return address unregistered. Repro: logs\water_fwd.padrec (stick forward after mark 1).
- Unmorph (manual R1+R2 or timer): crashed, same cause (C423). FIXED. Repro: logs\morph_r1r2.padrec (R1+R2 after mark 1).
- Monkeys route: a crash ~30 s after mark 7 (level unknown); a second run crashed in the same level (logs\crash2.*).
- Bunny-costume monkeys: ear physics randomly explode (spikes) then recover.
- Sound effects: occasional random glitches (with PS2X_SG2_LLE=1).

## Perf notes from the user
Slowdowns sit where the real PS2 also hitches (level 2 part 2, level 4, level 5 gymnastics zone).

## levels_run_audio (user, 2026-11-15, recorded WITH PS2X_SG2_LLE=1; replay only with LLE on)
Marks: 1 menu, 2 lobby, 3 L1 start, 4 L1 end, 5 L2 start, 6 L2 end (recording ends at 6). Dolby FMV skipped early (it dies randomly with LLE).
