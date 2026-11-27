# Task TR8: tiny logging trigger. One file. No header edits. Do NOT build/run/commit. Do not explore further.
File: c:\ApeEscape3_Recomp\PS2Recomp\ps2xRuntime\src\lib\render\rd_view.cpp
Just after the whole `if (g_rd2dReasonOn) { ... }` block that sets `rd2dReasonDump` (search `rd2dReasonDump = true`,
about line 4780-4850; add AFTER the closing brace of the outer if), add, marked // PROBE-TR8:
  static const bool s_tr8On = [] { const char *e = std::getenv("PS2X_RD_TRDUMP"); return e && e[0] == '1'; }();
  static uint32_t s_tr8Dumps = 0u;
  if (s_tr8On && g_rdGpu.local2dBatches.size() <= 12u && !g_rdGpu.local2dBatches.empty() && s_tr8Dumps < 400u)
  { ++s_tr8Dumps; rd2dReasonDump = true;
    ps2xSafeLog("[tr8] ms=%lld n=%zu\n", <steady_clock::now().time_since_epoch() in ms>, g_rdGpu.local2dBatches.size()); }
Reply in <=2 lines.
