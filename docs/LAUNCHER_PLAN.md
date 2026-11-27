# Launcher plan (phase 4, 2026-11-23)

Goal: one small executable `ape3_launcher` shipped with the port. The user points it at their own disc image, picks graphics/audio/input options, presses Play. It never contains or downloads game data.

## What the runtime needs today (measured from the code)
- Entry: `ps2EntryRunner_dev.exe SCUS_975.01` (argv[1] = guest ELF name, used for the game id). `--iso <file>` or any argument ending in `.iso` opens a disc image (main.cpp:301-312, IsoDisc). Without an ISO the runtime reads the extracted folder layout the dev setup uses.
- Settings file: `ps2x.ini` next to the exe, sections `[graphics]` (renderer, aspect, aspect_max, hud_anchor, render_scale, msaa, texture_pack, window, vsync, fullscreen) and `[debug]` (background_window). Environment variables `PS2X_*` override the file; `PS2X_NO_CONFIG=1` ignores it (ps2x_config.cpp; keys mapped to PS2X_ASPECT, PS2X_ASPECT_MAX, PS2X_HUD_ANCHOR, PS2X_MSAA, PS2X_RENDER_SCALE, PS2X_FULLSCREEN, PS2X_WINDOW_SIZE, PS2X_TEX_REPLACE_DIR ...).
- Flags that every verified run currently sets by environment (should become one "Release profile" the launcher applies, then move into the runtime defaults later): PS2X_GS_ASYNC=1, PS2X_VIF1_ASYNC=1, PS2X_GS_VULKAN=1, PS2X_SG2_LLE=1, PS2X_EEDC=1, PS2X_EEDC_CHECK=0, PS2X_FRONTEND=sdl, PS2X_SDL_RD=1, PS2X_RD_VIEW=1, PS2X_RD_CUT_ADAPT=1, PS2X_RD_COVER_TOL=400, PS2X_RD_PAIRLAG=1, PS2X_MC='' (memory card path), PS2X_LOAD_TIMING=original|fast.
- Debug-only (hidden behind an "Advanced/Developer" toggle, off by default): PS2X_DEV_CMD, PS2X_PAD_REC/PLAY, probes, PS2X_WINDOW_BACKGROUND.

## Design
- Stack: SDL3 + Dear ImGui (both already in the tree for the debug panel), single exe, no installer. Windows first; the settings model and the "build the command line" logic live in plain C++ with no Win32 calls so Linux/Android can reuse them (Android would embed the same settings page in the app).
- Pages: Game (disc image path / extracted folder, validation: must contain SCUS_975.01 or be an ISO with it; show detected game id), Video (renderer classic/new, resolution/window size, fullscreen, vsync, render scale, MSAA, aspect + widescreen cap, HUD anchor, texture pack folder), Audio (device later; volume), Input (keyboard map + pad detection; later), Advanced (load timing Original/Fast, memory card file, log level, Developer toggle), About (version, licence notes, "bring your own disc image").
- Process: the launcher writes `ps2x.ini`, builds the environment block + argv from the model, starts the runtime as a child process, streams its stderr/stdout into a log view, shows exit code/crash hint. Never edits game files.
- First run: no image configured -> Game page with a clear message; nothing is downloaded; nothing game-derived is stored in the settings except the user's own path.
- Errors: missing runtime exe, missing Vulkan (runtime exits with a message -> show it), unreadable image, ini write failure (read-only folder -> fall back to %APPDATA%).
- Packaging: release zip = runtime exe + launcher exe + ps2x.ini defaults + licences; never the ELF, BIOS, discs, dumps or recomp_source output (see docs/RELEASE_CHECKLIST.md).

## Build slices (each = one spec for Gemini, one build, one acceptance test; edit only new files under tools/launcher/ + one CMake target)
1. L1 settings model: `Settings` struct, ini read/write compatible with ps2x.ini (preserve unknown keys and comments), `buildCommandLine()` + `buildEnvironment()`. Test: unit test program that round-trips the repo's ps2x.ini byte-for-byte for unknown keys and produces the exact env block of the current verified command.
2. L2 window + pages with ImGui (Game, Video, Advanced), Save/Play buttons, validation messages. Test: launches, edits persist to ps2x.ini.
3. L3 process start/stop + log viewer + crash hint. Test: Play starts the runtime with two different settings sets; screenshots/logs match the manual command.
4. L4 first-run, About, Audio/Input stubs, error paths. Test: delete ini -> first-run page; point at a bad path -> message.

## Acceptance for the phase
Builds with the same VS toolchain (tools/build_avx2.bat style script `tools/build_launcher.bat`), launches the game with chosen settings, docs/RELEASE_CHECKLIST.md exists. Local commits only until the user reviews.
