# ENH3b: panel controls for the profiles. Small task. Do NOT build/run/commit.
Root c:\ApeEscape3_Recomp\PS2Recomp\ps2xRuntime. Mark `// FEAT-ENH3`. No header edits.
File: src/lib/ps2_debug_panel.cpp, Graphics tab, under the "Enhanced debug view" combo (~line 2320). API is in
src/lib/render/rd_enhance.h (RdEnhanceSettings, ps2xEnhanceSettings/SetSettings/StageName/FilesInUse/Unsaved/Save).
Shown only when ps2xEnhanceOn():
- Text "Stage: <name or (none)>", "Files: <files in use>", and "unsaved changes" when ps2xEnhanceUnsaved().
- Buttons "Save for zone" and "Save for level" (disabled with no stage).
- A line "Effects are not built yet; these values are stored for later."
- One collapsing header per group (Colour grading, Bloom, Fog, Corner darkening, Depth of field, Light shafts, Sun)
  with an "On" checkbox, strength slider 0..1 and sliders / colour edits for the other values, sensible ranges
  (fog distances 0..20000 world units). Use PushID so equal labels do not collide.
- Copy settings, edit the copy, and call SetSettings only if a widget changed.
Reply with line numbers.
