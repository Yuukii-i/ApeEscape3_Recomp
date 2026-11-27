# Task SCR1: choose which monitor the game window opens on. One file, one insertion. Do NOT explore, build, run or commit.
File: PS2Recomp/ps2xRuntime/src/lib/platform/ps2_sdl_platform.cpp. Mark `// FIX-SCR1`.
In `ps2xSdlInit`, AFTER the SDL_CreateWindow failure check and BEFORE the `// FIX-R1: start fullscreen` block (about line 1102):
  - int n = 0; SDL_DisplayID *ids = SDL_GetDisplays(&n);
  - for i in [0,n): SDL_Rect r; if SDL_GetDisplayBounds(ids[i], &r): printf `[sdl] display %d bounds=%d,%d %dx%d\n` (i+1, ...).
  - if env `PS2X_DISPLAY` is set and its integer value k is in 1..n and bounds of ids[k-1] succeed:
      SDL_SetWindowPosition(g_sdl.window, SDL_WINDOWPOS_CENTERED_DISPLAY(ids[k-1]), SDL_WINDOWPOS_CENTERED_DISPLAY(ids[k-1]));
      SDL_SyncWindow(g_sdl.window);
      printf `[sdl] window on display %d\n`.
  - SDL_free(ids).
Reply in <=3 lines.
