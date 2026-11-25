VC1 PCSX2 COP2 conformance run (addresses in layout.txt; blob base 0x01E00000, please confirm free)
1. python tools/vucheck/gen_pcsx2_test.py   (regenerates ops.txt inputs.* pcsx2_test.bin layout.txt)
2. In PCSX2 (game running, in a state where CU2 is enabled, e.g. in-level), pause.
3. write_memory pcsx2_test.bin to 0x01E00000 (size in layout.txt). Also zero 0x01E10000.. is NOT needed.
4. Set pc = 0x01E00000 (harness entry; first insn is `di`). Set a breakpoint at done_pc (layout.txt).
5. Continue; wait for the bp at done_pc; check word at 0x01E00810 == 0x600DF00D.
6. save_state, then read result table (layout.txt: result_table, num_ops*32*64 bytes) from eeMemory.bin
   at offset (result_table - 0), i.e. guest address == eeMemory.bin offset.
7. Save it as tools/vucheck/pcsx2_out.bin. Record = vf3,acc(vf5),status,mac,clip,Q,I,pad(3) (64 bytes).
   Index = (op_index*32 + case)*64; op_index = line order of ops.txt.
8. Do NOT resume the game afterwards (registers/pc are clobbered): reload the state or restart.
Notes: ACC is read via vmaddx vf5,vf0,vf0x (loses -0/NaN/denormal ACC lanes slightly). vf3 is preset to
0xDEADBEEF lanes, so ACC-only ops leave the sentinel in vf3. Harness clobbers s0-s5,t0,t1,ra.
