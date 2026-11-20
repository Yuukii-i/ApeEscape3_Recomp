# Overnight log (append one line per experiment; status OPEN / KEPT / REVERTED / VISUAL-REVIEW)
Format: `<id> <status> <area>: <what> | gate: <PASS/FAIL reason> | studio_d x->y fps, castle_a x->y, cpu/frame deltas | commit <hash>`

Baseline: tag `overnight-base` (PS2Recomp 2625f0d-era build; exe copy build_avx2\...\base_overnight.exe). Reference numbers (stage_bench, same session, takeover env): castle_a 58.9 fps / 46.8 ms cpu/frame; studio_c 33.3 / 71.4; studio_d 39.0 / 76.3; toyhouse_a 56.5 / 62.6; arabian_a 58.9 / 46.0.


START 2026-11-20 04:22 - silent mode, YouTube playing in background (background load present for all A/B runs).
n0 DONE gate noise floor (full, identical code, 3 alt reps): fps within +-1.6%, cpu/frame within +-3.4% (toyhouse +3.4%). Visual check false-FAILed castle_a once (frac 0.0201 vs floor 0.02) -> thresholds widened to max(2x noise, 4.5 mean / 0.09 frac). Gains below ~3-4% cannot be proven by the gate; micro-opts are kept when the gate PASSES and they remove work at zero risk.
EX1-3 KEPT ee: hoist/cache in checkpointDue/advanceEeTimers/accountCycles/ps2DcallContinue/dispatchGuestBranch/decompThunkImpl/eeCheckpointDue/Load128 | gate e1b+e1c PASS (3 reps): fps unchanged, cpu/frame castle -5.4%, toyhouse -1.8%, ciscocity -1.6%, studio +-1.5% (noise) | PS2Recomp 991d192
EX4+EX5 KEPT vif1/render: aligned queue atomics, trimmed VP_WRITES events, out-param pops; texture-cache upkeep every 16th frame, clut note on miss only, direct texParam indexing | gate e45 PASS (3 reps, 4 stages): fps unchanged, cpu/frame studio_d -3.5%, ciscocity -3.9%, castle -1.0%, toyhouse -0.9% | PS2Recomp be0cb56
