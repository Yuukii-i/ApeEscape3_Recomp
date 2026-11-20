# Overnight log (append one line per experiment; status OPEN / KEPT / REVERTED / VISUAL-REVIEW)
Format: `<id> <status> <area>: <what> | gate: <PASS/FAIL reason> | studio_d x->y fps, castle_a x->y, cpu/frame deltas | commit <hash>`

Baseline: tag `overnight-base` (PS2Recomp 2625f0d-era build; exe copy build_avx2\...\base_overnight.exe). Reference numbers (stage_bench, same session, takeover env): castle_a 58.9 fps / 46.8 ms cpu/frame; studio_c 33.3 / 71.4; studio_d 39.0 / 76.3; toyhouse_a 56.5 / 62.6; arabian_a 58.9 / 46.0.

