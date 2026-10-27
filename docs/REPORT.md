# Task EW Report
- BUILD OK.
- Grep verified: `ew vcallms` and `ew vu0code` in `ps2_runtime.cpp`.
- Added VU0 microprogram probe at `executeVU0Microprogram` tracking `startPC == 0` calls under `PS2X_PROBE_VU3D=1`.
- Snapshots entry vf4..vf11 (32 words) and exit vf8..vf11 (16 words); flags exit lanes matching +-FLT_MAX, 0xFF7FFFFE, NaN, Inf, or |f| > 1e20.
- Prints `[probe] ew vcallms#N` and `[probe] ew extra` for the first 6 sane and first 6 bad calls with separate counters.
- Computes VU0 micro memory hash, non-zero words, and first 8 words on start and when hash changes (`[probe] ew vu0code`, max 10 prints).
- Added periodic 5-second console summary `[probe] ew counts calls=N bad=M idle=K`.
- Committed on branch `task/EW` in PS2Recomp and ApeEscape3_Recomp.
