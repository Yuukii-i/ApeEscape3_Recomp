# Task EQ Report
- BUILD OK.
- Grep verified: `eq unpack` in `ps2xRuntime/src/lib/ps2_vif1_interpreter.cpp`.
- Implemented UNPACK cmd 0x6C (V4-32) detector checking written qw lane 0/1 for 0x7F7FFFFF, 0xFF7FFFFF, 0xFF7FFFFE, or |f| > 1e30.
- Prints `[probe] eq unpack` (max 30) with src RDRAM addr/copied, dest, eff, num, tops, and first bad qw.
- For first 6 bad unpacks, prints `[probe] eq rdram 0x%08X <64 bytes hex> tag=n/a`.
- Added periodic 5-second console summary `[probe] eq counts bad=N total_v4_32=M`.
- Committed on branch `task/EQ` in PS2Recomp and ApeEscape3_Recomp.
