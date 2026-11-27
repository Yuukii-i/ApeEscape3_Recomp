# Task WS3 (small): fix F1 under SDL, clearer aspect labels. Apply these edits only.
No other exploring, no .h edits, no build/run/commit. Mark `// FIX-WS3`. Paths under PS2Recomp/ps2xRuntime/src/lib/.

1. platform/ps2_sdl_platform.cpp: at global scope next to the `// PROBE-WSD1` extern line add
   `std::atomic<bool> g_ps2xF1Pressed{false}; // FIX-WS3`
   In `case SDL_EVENT_KEY_DOWN` (beside the F6 handler): on F1 key down (type KEY_DOWN, no repeat) `g_ps2xF1Pressed = true;`
2. ps2_debug_panel.cpp ~2409 (`PS2DebugPanel::draw`): declare `extern std::atomic<bool> g_ps2xF1Pressed;` at global scope
   (include <atomic> if needed) and change the condition to
   `if (ps2xSdlActive() ? g_ps2xF1Pressed.exchange(false) : IsKeyPressed(KEY_F1)) // FIX-WS3`
3. ps2_debug_panel.cpp ~2219-2268, change label strings only (same order, same count):
   aspectItems: "4:3 original (black bars)", "Widescreen (shows more)", "16:9 (stretched)", "16:10 (stretched)", "Raw pixels (unscaled shape)"
   "Widescreen cap (fill)" -> "Widest widescreen"
   hudItems: "screen corners", "within 21:9", "within 16:9", "within 4:3"
   "HUD anchor" -> "HUD position"
Reply in <=3 lines.
