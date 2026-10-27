# Task EV Report
- BUILD OK.
- Grep verified: `ev src10` in `ps2_vif1_interpreter.cpp` and `ev vu10` in `ps2_vu1_core.cpp`.
- Added VIF1 snapshot buffers copying all 10 source qw and 10 destination read-back qw for every UNPACK 0x6C dest=235 num=10 without printing.
- In `ps2_vu1_core.cpp`, at C80 entry with vi13==235, scans all 10 qw for bad lanes (+-FLT_MAX, 0xFF7FFFFE, NaN, Inf); on first 3 bad hits, prints `ev vu10` (10 lines), elapsed ms, and triggers `ps2_vif1_dumpEvBuffers()` for `ev src10` (10 lines) and `ev dst10` (10 lines).
- Kept ring dump and store checks; removed verbose early eu prints.
- Committed on branch `task/EV` in PS2Recomp and ApeEscape3_Recomp.
