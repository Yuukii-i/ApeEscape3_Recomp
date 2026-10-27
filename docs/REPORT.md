# Task ER Report
- BUILD OK.
- Grep verified: `er drop` and `er counts` in `ps2xRuntime/src/lib/ps2_vif1_interpreter.cpp`.
- Added dropped UNPACK logging (`[probe] er drop`, max 40) capturing opcode, num, dest, pos, totalBytes, sizeBytes, m_vu1Data, cl, wl, and srcBase_rdram.
- Added chunk diagnosis (`[probe] er chunk`, first 10 chunks with dropped unpacks) logging size, start_pos, src, and first 4 words.
- Added tracking of executed vs dropped UNPACKs per opcode with periodic 5-second console summary `[probe] er counts drop(...) taken(...)`.
- Committed on branch `task/ER` in PS2Recomp and ApeEscape3_Recomp.
