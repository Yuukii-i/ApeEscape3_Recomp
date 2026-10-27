# Task ET Report
- BUILD OK.
- Grep verified: `UNPACK-RB` at line 1691 and `mask=` at line 1026 of `ps2xRuntime/src/lib/ps2_vif1_interpreter.cpp`.
- Extended UNPACK ring event to record mask, mode, row[0..3], and col[0..3].
- Added post-write `UNPACK-RB` ring event logging first and last written quadwords directly from `m_vu1Data`.
- Added ring event logging for STMASK, STROW, STCOL, STMOD, MSKPATH3, and FLUSH.
- Raised ring buffer capacity from 64 to 128 events (256 bytes per event line).
- Committed on branch `task/ET` in PS2Recomp and ApeEscape3_Recomp.
