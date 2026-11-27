# Task TR9: count the game's frame-draw calls. Logging only. One file. No header edits. Do NOT build/run/commit.
File: c:\ApeEscape3_Recomp\PS2Recomp\ps2xRuntime\src\lib\ps2_runtime.cpp, right after the `// FIX-UI5` wrapper
block that follows `ps2xEeGfxDecompInstall(*this);` (~line 2924-3000). Mark lines // PROBE-TR9.
Only when env PS2X_RD_TRLOG=1: wrap guest function 0x003B3A90 with the same lookupFunction / registerFunction
pattern the FIX-UI5 wrapper uses for 0x003B7798 (keep the original pointer in a file-static; if lookup returns
null do nothing and log "[fd] no function"). The wrapper logs one line then calls the original:
  ps2xSafeLog("[fd] ms=%lld ra=%08x a0=%08x a1=%08x\n", <steady_clock::now().time_since_epoch() in ms>, ra, a0, a1);
reading ra/a0/a1 from ctx the same way the FIX-UI5 wrapper reads registers. Reply in <=2 lines.
