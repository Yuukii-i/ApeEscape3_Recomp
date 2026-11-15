# Things only the user can do (paste-ready)

## 0. Play the fastest build (2026-11-15: AVX2 + direct calls + VU0 handlers + PGO, no logging)
```powershell
cd C:\ApeEscape3_Recomp
Get-ChildItem env:PS2X_* -ErrorAction SilentlyContinue | ForEach-Object { Remove-Item "env:$($_.Name)" }
$env:PS2X_GS_ASYNC = "1"
$env:PS2X_VIF1_ASYNC = "1"
$env:PS2X_GS_VULKAN = "1"
$env:PS2X_VU1_KERNEL = "1"
$env:PS2X_PRESENT_ASYNC = "1"
$env:PS2X_PRESENT_GPU = "1"
.\build\PS2Recomp\ps2xRuntime\ps2EntryRunner_pgo.exe SCUS_975.01 2> $null > $null
```
If anything looks wrong compared with ps2EntryRunner_dev.exe, tell me (and which off switch helps: docs/REVERSAL_MEMO.md).

## 0b. (graphics decompilation) City level (level 4) SECOND area, with capture
The monkeys run hit an un-decompiled VU1 program (entry 0x01C8, ~100k fallbacks) right after the city level's second
area (stage ciscocity_b; your no-monkeys route never entered it). Please play the city level into its second area for
a minute or two (catching a monkey or two there helps) using the block in section 1 below (it has PS2X_VU1_CAPTURE_FB=1),
then close the game normally.

## 1. Play other levels with VU1 verification + capture (helps the graphics decompilation)
Plays normally (60 fps where possible). While you play:
- every 128th VU1 program that uses one of the 17 newly decompiled handlers is re-checked against the exact interpreter
  (`[vnc]` lines in the log; mismatches must stay 0),
- every VU1 program the decompiled engine cannot run yet is recorded to logs\vu1corpus_fb.bin (test data for the rest),
- your pad input is recorded to logs\levels.padrec (lets me replay the same route for benchmarks).
Play through 2-3 different levels / areas (cutscenes, water, snow, bosses if you get there), then close the game normally.

```powershell
cd C:\ApeEscape3_Recomp
Get-ChildItem env:PS2X_* -ErrorAction SilentlyContinue | ForEach-Object { Remove-Item "env:$($_.Name)" }
$env:PS2X_GS_ASYNC = "1"
$env:PS2X_VIF1_ASYNC = "1"
$env:PS2X_GS_VULKAN = "1"
$env:PS2X_VU1_KERNEL = "1"
$env:PS2X_PRESENT_ASYNC = "1"
$env:PS2X_PRESENT_GPU = "1"
$env:PS2X_VU1_CAPTURE_FB = "1"
$env:PS2X_PAD_REC = "logs\levels.padrec"
.\build\PS2Recomp\ps2xRuntime\ps2EntryRunner_dev.exe SCUS_975.01 2> logs\levels_play.err > logs\levels_play.out
```
Afterwards tell me; I will check `[vnc]` / `[vu1fb]` in the log and use the capture.

## 2. Close heavy background apps before I benchmark
Benchmarks run in silent mode on AC. A browser playing video / Steam downloading takes 2-3 cores and makes every A/B
unreliable (2026-11-14: both builds dropped from 60 to 55 fps under that load).

## 3. Visual check of today's default-on changes (if anything looks wrong, switch off and tell me)
- VIF1 MARK without fence: `$env:PS2X_MARK_NOFENCE = "0"`
- DMA chain copy on the worker: `$env:PS2X_DMA1_WORKER_COPY = "0"`
- Redundant GS state breaks skipped: `$env:PS2X_GS_REDUND = "0"`
- 17 new VU1 handlers: `$env:PS2X_VU1_FUNC_NEW = "0"`
(add the line before the last line of the block above)
