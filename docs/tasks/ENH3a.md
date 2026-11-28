# ENH3a: per-level / per-zone profile module. Small task. Do NOT build/run/commit.
Root c:\ApeEscape3_Recomp\PS2Recomp\ps2xRuntime. Mark `// FEAT-ENH3`. Do not edit existing .h files except our
own src/lib/render/rd_enhance.h. Logs with ps2xSafeLog only (plain stderr is discarded).

1. rd_enhance.h: add POD `struct RdEnhanceSettings` (all defaults chosen so nothing changes):
   grade{bool on; float strength, exposure, contrast, saturation, tint[3];}
   bloom{on, strength, threshold, radius}  fog{on, strength, color[3], start, end, height, falloff, sky}
   ao{on, strength, radius, bias}  dof{on, strength, focus, range, blur}  shafts{on, strength, length, decay}
   float sunDir[3], sunColor[3], ambient[3];
   All `strength` = 0 and `on` = false by default; neutral values otherwise.
   And declarations:
   void ps2xEnhanceProfileTick(const uint8_t *rdram);
   RdEnhanceSettings ps2xEnhanceSettings();                  // thread-safe copy
   void ps2xEnhanceSetSettings(const RdEnhanceSettings &);   // live edit, marks unsaved
   std::string ps2xEnhanceStageName();  std::string ps2xEnhanceFilesInUse();  bool ps2xEnhanceUnsaved();
   bool ps2xEnhanceSave(bool wholeLevel);
2. New src/lib/render/rd_enhance_profile.cpp (add to CMakeLists.txt next to rd_view.cpp, ~line 430):
   - Stage name: up to 31 chars, NUL-terminated, at guest address 0x649650 in rdram (main RAM, 32 MB; KUSEG).
     Valid only if non-empty and all in [a-z0-9_]; otherwise treat as "no stage". Level = part before last '_'
     (whole name if none).
   - Folder: env PS2X_ENH_DIR, default "enhanced/levels". Apply key by key in this order, later overriding:
     built-in defaults, default.ini, <level>.ini, <stage>.ini.
   - Format: `key=value` lines, '#' comments, keys like bloom.on, bloom.threshold, fog.color=r,g,b, sun.dir=x,y,z,
     sun.color, ambient. Use one table of keys for both load and save.
   - Reload when the stage changes, or when any of the three files appears/changes/disappears (check mtimes once
     per second). A file with an unreadable line or unknown/non-finite value: log once per file change
     `[enh] profile error <file> line <n>` and keep the previous settings (do not apply that file partially).
     Reload discards unsaved edits.
   - Log `[enh] stage <name>` on change and `[enh] profile reload <files>` on each load.
   - ps2xEnhanceSave(false) writes all values to <stage>.ini; (true) to <level>.ini. Write to a temp file then
     rename; create the folder. Return false with a log on failure or when there is no stage.
   - tick() must be cheap when nothing changed (no file access except the once-a-second mtime check).
3. src/lib/ps2_runtime.cpp: call ps2xEnhanceProfileTick(memory().getRDRAM()) (adapt to the object in scope) once per
   host frame in the main render/present loop, only when ps2xEnhanceOn().
Reply with files and line numbers.
