# Task ES Report
- BUILD OK.
- Grep verified: `ep ev` at line 159 and `src=0x` at line 1018 in `ps2xRuntime/src/lib/ps2_vif1_interpreter.cpp`.
- Added source information (src RDRAM addr or 0xFFFFFFFF, plus first 16 source bytes w0..3) to UNPACK events in the EP ring.
- Restored `ps2x_probeDump()` to output all 64 ring events (`[probe] ep ev %u: ...`) on bad vustores.
- Removed verbose EQ/ER per-unpack and count print spam.
- Committed on branch `task/ES` in PS2Recomp and ApeEscape3_Recomp.
