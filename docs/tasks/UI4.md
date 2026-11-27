# Task UI4: tag font glyph quads too. ONE file, one insertion. Do NOT explore other code, build, run or commit.
File: PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp, inside the `// FIX-UI2` wrapper for 0x003B7798 (about line 2970-2995).
Mark `// FIX-UI4`.

Facts (PCSX2): the font drawer calls sub_003B7798 with return address 0x001DF85C and a1 (reg 5) = packet end.
Before `end` lie one or more glyph packets, 16-byte aligned: a GIF tag qword with low64 == 0x6400000000008001,
and 16 bytes after it a qword whose low64 is PRIM == 0x156.

Add, before the original function is called, an `else if` / separate `if (GPR_U32(ctx, 31) == 0x001DF85Cu)` branch that
uses the same `host` address helper style as the existing branch:
  - a = (end & ~0xFu) - 16; scan downward in steps of 16 while a >= end - 0x4000 (and a >= 0x100000):
      read u64 v at a and u64 g at a - 16;
      if g == 0x6400000000008001ull:
          if v == 0x156ull: write v | (uint64_t(0xA5FEu) << 32); ++textTagged;
          else if v == (0x156ull | (uint64_t(0xA5FEu) << 32)): break;   // reached an already-tagged earlier run
  - static counter; every 2000 calls ps2xSafeLog("[uitag] text glyphs tagged=%u calls=%u\n", ...).
Note: end may be above 0x20000000 mirrors; mask like the existing helper does.
Reply in <=3 lines.
