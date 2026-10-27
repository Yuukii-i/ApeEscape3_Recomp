# Task FC Report
- Added C80 10-qw matrix block audit, classification (NF/BIG/ZR), and UNPACK source tracing.
- Added 1-sec periodic summary: `[probe] fc c80 total=.. flagged_nonfinite=.. flagged_big=.. zero_rows=..`.
- Logged first 20 flagged and 6 unflagged events as `[probe] fc blk ...`.
- Files touched: PS2Recomp ps2_vu1_core.cpp, ps2_vif1_interpreter.cpp (.cpp only, no headers).
- Build: BUILD OK.
- Branches: task/FC in PS2Recomp and ApeEscape3_Recomp.
