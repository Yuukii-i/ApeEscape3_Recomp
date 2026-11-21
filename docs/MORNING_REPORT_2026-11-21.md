# Overnight report 2026-11-21 (Claude, unattended)
Branches (nothing merged, nothing on main): PS2Recomp `feat/pause-menu-fx`, `feat/sdl3-frontend`; parent `feat/pause-menu-fx`, `feat/sdl3-vulkan-platform`.

## 1. Pause menu (PS2X_RD_FXCLASSIC, default ON in the GL renderer)
The Start-pause is built by the game as screen-feedback draws (palette tint + half-res blur through a scratch buffer). The GL renderer cannot reproduce them; for those frames it now presents the Vulkan GS frame instead (menu animated, blue ball, text boxes). Background is black in GL mode (the Vulkan GS never rasterises the 3D scene). Never fires in gameplay stages (fxClassic=0 in castle/toyhouse/studio_a/arabian_a). Branch `feat/pause-menu-fx`.
Correction of an earlier claim: my "classic beats new" table used a stale exe. With the right exe the new renderer wins (CPU ms/frame studio_b 22 vs 47, studio_d 28 vs 59, castle_a 39 vs 51, toyhouse_a 53 vs 68).

## 2. Vulkan port (branch `feat/sdl3-frontend` + parent `feat/sdl3-vulkan-platform`)
- SDL3 (release-3.2.28, fetched by CMake) platform layer: window, Vulkan swapchain, keyboard/gamepad, audio. `PS2X_FRONTEND=sdl`.
- `rdgfx::` graphics interface under rd_view.cpp/rd_texture.cpp: GL implementation unchanged (A/B pictures identical, same fps), plus a full Vulkan implementation `rdgfx_vk` (shaders rd.vert/rd.frag -> SPIR-V by glslc at build time, pipelines, descriptor cache, dirty-state tracking, textures, palette, overlay, backbuffer copy, optional 4x MSAA).
- `PS2X_FRONTEND=sdl PS2X_SDL_RD=1` runs the NEW renderer on Vulkan inside the SDL window; picture matches GL on the hub; validation layer clean (`PS2X_VK_VALIDATE=1`).
- Pause menu in that mode: frozen scene through the measured tint ramp (R=G=0.25*Y+8, B=0.45*Y+14, fitted from the real classic pause frame) + the real animated menu on top (alpha-keyed): very close to the PCSX2 reference.
- Perf vs GL (CPU ms/frame): castle_a 39.8 vs 38.5, toyhouse_a 55.8 vs 50.5, studio_b 22.5 vs 21.2 (fps equal in castle/studio, toyhouse 53.8 vs 57). Remaining gap is mostly main-thread recording (~3-5 ms) and can be cut further.

## 2b. Robustness\nFull 148-stage warp tour in `PS2X_FRONTEND=sdl PS2X_SDL_RD=1`: 148/148 alive, no GPU errors, fps min 45 / median 59 (logs\vktour_summary.txt).\n\n## 3. How to try it (PowerShell, one block)
```
cd C:\ApeEscape3_Recomp
$env:PS2X_GS_ASYNC='1'; $env:PS2X_VIF1_ASYNC='1'; $env:PS2X_GS_VULKAN='1'; $env:PS2X_SG2_LLE='1'; $env:PS2X_EEDC='1'
$env:PS2X_FRONTEND='sdl'; $env:PS2X_SDL_RD='1'; $env:PS2X_MSAA='4'
.\build_avx2\PS2Recomp\ps2xRuntime\ps2EntryRunner_dev.exe SCUS_975.01
```
Keys: WASD left stick, IJKL right stick, arrows D-pad, X/Space cross, C/Esc circle, Z square, V triangle, Q/E L1/R1, Shift L2/R2, Enter start, Tab select. Env: `PS2X_VK_VALIDATE=1` (validation), `PS2X_RDVK_LOG=1` (timers), `PS2X_SDL_POLL_MS`, `PS2X_RD_SNAP`.

## 4. Known problems / not done
- Snapshot substitution (`PS2X_RD_SNAP=1`) misrenders in the Vulkan path (sky colour in the ground): defaulted OFF in SDL RD mode. The PREV cross-fade path works.
- The swirl (radial wipe with depth-mask sectors) is still unhandled in both renderers.
- The debug panel (Dear ImGui, SDL3 + Vulkan backends) now draws in the SDL window (F1 toggles, `PS2X_SDL_UI=0` disables); only the header bar was checked visually, the full panel has not been exercised.
- No window-resize/fullscreen/aspect options yet in SDL mode, no vsync choice; present is FIFO (display 180 Hz here).
- GL path and raylib are untouched (V4 "delete GL" NOT done, needs your review).
- The studio music slowdown on warps and the 250 ms hitches (PACE2 sub-timers never run) are not investigated yet.
- GS Vulkan backend needs VK_EXT_fragment_shader_interlock (checked at start): a portability risk for AMD iGPU / mobile.

## 5. Next steps (suggested)
1. You try the block above (hub, pause, a few levels) and tell me what looks wrong.
2. Dear ImGui (SDL3 + Vulkan backends) debug panel + the Enhanced-renderer UI from docs/OVERHAUL_PLAN.md.
3. Fix snapshots, then native fades/swirl in rdgfx_vk.
4. Camera/light research via PCSX2 for the overhaul.
5. Perf: batching/state sorting in the Vulkan path, GS double-raster removal (RTT plan P5).

