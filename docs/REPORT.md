# Task EU Report
- BUILD OK.
- Grep verified: `eu src10` and `eu dst10` in `ps2xRuntime/src/lib/ps2_vif1_interpreter.cpp`.
- Added UNPACK 0x6C (dest=235, num=10) logging for first 6 occurrences: dumps all 10 source qw (`eu src10`) and 10 read-back destination qw (`eu dst10`).
- In `ps2_vu1_core.cpp`, added dump of 10 VU qw at 235 on C80 entry when vi13==235 (`eu vu10`).
- In `ps2_vu1_core.cpp`, added VU store monitoring for qw 235..244 (`eu vustore`, up to 20 lines once per run after 6 matched UNPACKs).
- Committed on branch `task/EU` in PS2Recomp and ApeEscape3_Recomp.
