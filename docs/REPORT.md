# Task EY Report
- BUILD OK.
- Grep verified: `ey call` and `ey vuop` in `ps2_runtime.cpp`.
- Added up-vector / macro probe in `dispatchGuestBranch` for targets 0x2540E4, 0x359EFC, and 0x254280 (first 40 occurrences each) logging `a3` (128-bit GPR 7), `vu0_vf[0..2]`, and `f12`.
- Added invariant check at every call: logs `ey vf0 CLOBBERED` once per 100 (cap 30) if `vu0_vf[0]` differs from `{0,0,0,1.0f}` without resetting it.
- Added startup self-test `ey vuop` evaluating the recompiled sequence of `0x169144` and `0x16915c` on test vectors.
- Files touched: `PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp`, `docs/REPORT.md`.
- Committed on branch `task/EY` in PS2Recomp and ApeEscape3_Recomp.
