# ENH1a: "Enhanced" setting, checkbox, stub and call site. Small task. Do NOT build/run/commit.
Root c:\ApeEscape3_Recomp\PS2Recomp\ps2xRuntime. Mark changes `// FEAT-ENH1`. Do not edit existing .h files.
Read only the lines named below plus a little around them.

1. New header src/lib/render/rd_enhance.h:
     struct RdEnhanceFrame { float vpScaleZ = 0, vpOffsetZ = 0; float camera[16] = {}; bool cameraValid = false; float gsToClip[16] = {}; };
     bool ps2xEnhanceOn();  void ps2xEnhanceSetOn(bool);  void ps2xEnhanceApply(const RdEnhanceFrame &frame);
2. src/lib/config/ps2x_config.cpp: ini key graphics.enhanced (0/1) -> setEnvDefault("PS2X_ENHANCED", v), next to
   graphics.render_scale (~line 208). Define ps2xEnhanceOn/SetOn here with a std::atomic<bool> initialised once from
   env PS2X_ENHANCED (default off), following the live graphics store at ~line 233-385. ps2xGfxSaveIni (~line 387)
   also writes graphics.enhanced.
3. src/lib/ps2_debug_panel.cpp (~line 2290-2345, next to the Fullscreen checkbox): checkbox "Enhanced graphics",
   disabled (ImGui::BeginDisabled) unless rdgfx_vk::active(). Live.
4. src/lib/render/rd_view.cpp: immediately BEFORE the final `draw2dUntil(0u, true)` (~line 7513):
     if (ps2xEnhanceOn() && !g_rdGpu.drawBatches.empty()) { RdEnhanceFrame f; f.vpScaleZ = g_rdGpu.vpScaleZ; f.vpOffsetZ = g_rdGpu.vpOffsetZ; ps2xEnhanceApply(f); }
5. Define ps2xEnhanceApply as an EMPTY stub at the end of src/lib/render/rd_gfx_vk.cpp (outside namespace rdgfx_vk),
   guarded the same way the file is built. If a build without Vulkan would then fail to link, put a no-op fallback
   in rd_view.cpp under the matching #if. The next task fills the stub in.
Reply with the files and line numbers touched.
