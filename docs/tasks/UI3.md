# Task UI3 (probe): count which guest callers submit drawing packets. One file, do NOT explore, build, run or commit.
File: PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp. Mark `// PROBE-UI3`.
1. Add `#include <map>` beside the standard includes if absent.
2. In the `// FIX-UI2` block (about line 2925), after the existing registerFunction(0x003B7798u, ...) call and still inside
   the `if (const char *uiEnv ...)` block, also wrap 0x003B7840 the same way (own `static RecompiledFunction s_uiOrig2`),
   counting only, no memory writes.
3. In BOTH wrappers, before calling the original, count the caller:
   key = (which << 32) | GPR_U32(ctx, 31)   where which = 0 for 3B7798, 1 for 3B7840;
   use one shared file-scope `static std::map<uint64_t, uint32_t> s_uiRa;` (declare it above the function that
   contains the block), keep at most 128 keys.
   If >= 1000 ms (steady_clock) since the last flush: print each entry
   `[uiwr] t=%.1f fn=%u ra=%08x n=%u\n` (t = seconds since first count), clear the map.
   Put this in one small file-scope helper `static void ps2xUiRaCount(uint32_t which, uint32_t ra)`.
Reply in <=3 lines.
