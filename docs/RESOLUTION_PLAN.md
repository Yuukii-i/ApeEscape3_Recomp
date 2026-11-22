# Resolution / aspect / widescreen plan (2026-11-21, frame-timing work parked by user)

## State measured 2026-11-21 (SDL+Vulkan RD, ps2x.ini aspect=fill window=1600x900)
- Works: resizable window; PS2X_ASPECT / ini `aspect` = 4:3 (default) | fill | 16:9 | 16:10 | native; `fill` widens the 3D view horizontally (g_rdAspectK = winAspect/(4/3), FEAT-RD16) and anchors the HUD to the screen edges; k<1 falls back to a 4:3 box; MSAA 4x; internal render size = window pixel size (so hi-res is automatic, but cost scales with the window).
- 21:9 (2560x1080): fills, but ~3% black strips at both far edges (geometry/backdrop the game never draws outside its 4:3 frustum): belongs to phase 2.
- Missing: fullscreen, present mode/vsync choice, render scale (render resolution independent of window size), ini keys for those, in-game panel controls, per-scene widescreen audit.

## Phase 1: resolution foundation (this plan)
- R1 window/present: borderless fullscreen (F11 + ini `fullscreen`), present mode (ini `vsync`: on=FIFO default, mailbox, off=immediate; env PS2X_VK_PRESENT).
- R2 render scale: offscreen target = scale x window size (ini `render_scale` 25..400 %, default 100); final composite scales to the swapchain (linear). Weak hardware can lower it, strong hardware can supersample.
- R3 config + panel: all keys readable from ps2x.ini in SDL mode; debug panel (F1) graphics section to change aspect/scale/msaa live where cheap.
- R4 widescreen audit per scene type that works today (3D gameplay, HUD, menus/level select, FMV (4:3 pillarbox), pause FX composite, loading/intro screens, boss/cutscene letterboxes). Fades/transitions/swirl are OUT of scope until native fades exist in the Vulkan renderer (user note 2026-11-22). Fix what stretches or leaves bars.

## Phase 2: widescreen content popping (after phase 1)
- The game culls objects/textures against its 4:3 frustum and draws backdrops sized for 4:3. Find the culling tests/FOV constants (EE side), GS scissor / guard band limits, LOD/streaming radius, and widen them for aspectK (hack ledger entries, env-gated). PCSX2 pnach widescreen/no-cull patches for SCUS-97501 are a lead.

## Progress 2026-11-21 (autonomous block while user on break)
- DONE R1: F11 borderless fullscreen (untested by hand), PS2X_VK_PRESENT / ini vsync (on|mailbox|off|relaxed) verified by log.
- DONE R5: SDL classic present crops to the real picture region and centers a PS2X_ASPECT box (intro/SCEA/FMV/Now Loading centered, verified at 1280x720).
- DONE R6: PS2X_ASPECT_MAX (ini aspect_max, default 21:9): fill is capped, side bars on ultra-wide. Verified 3840x1080.
- DONE R7: draws clipped to the display box (side bars verified black). The ~3% strips at the box edges are the game's own undrawn extents (phase 2), NOT bleed.
- DONE R2: PS2X_RENDER_SCALE / ini render_scale (25..400 %): offscreen target = scale x window; final blit scaled (LINEAR); ImGui on the swapchain. Verified 50/100/200 % on the hub (60 fps at 100 and 200 %). rdgfx_vk::setRenderScalePercent/getRenderScalePercent exist for a live UI.
- DONE R8: PS2X_HUD_ANCHOR / ini hud_anchor = edge (default) | 16:9 | 4:3 | safe=<aspect>. Verified 16:9 safe area on 2560x1080 (margin 61 fb px). A wide HUD gauge at the bottom right still sits at the edge.
- TODO R3: F1 panel controls (aspect, render scale, HUD anchor, vsync, fullscreen) + saving to ps2x.ini; R4 per-scene audit (menus, level select, fades/swirl, FMV, pause composite in wide windows, bosses).
- PHASE 2 NOTE: decomp testFrustumAabb (ee_gfx_decomp.cpp sub_003BA898, FEAT-RD16) already scales the frustum x by 1/g_rdAspectK; testSphereAabb (sub_003C1D18) and other visibility tests (LOD, actor activation radius, GS scissor/guard band, backdrop/skybox extents) are the next candidates. Strips at the box edges at 21:9 prove some draws are still 4:3 limited.
