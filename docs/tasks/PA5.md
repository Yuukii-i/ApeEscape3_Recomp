# Task PA5: pause/gadget background = tinted HUD-free scene, drawn by the new renderer
Do exactly this. No header edits. Do NOT build, run or commit. Do NOT explore beyond the places named. Mark lines // FIX-PA5.
Dir: c:\ApeEscape3_Recomp\PS2Recomp\ps2xRuntime\src\lib
Ground truth (one paused frame of local2dBatches): offscreen copies (tme, ps2xRdIsFbFeedback) into frame fbp 0x70 and 0xE0;
then to fbp 0: a full-screen tint (tme, tex psm 0x1B, tbp0=0xE00) and two blur draws (tme, psm 0, tbp0=0x1C00).

A. gs/gs_frontend.cpp ~line 1614: s_rdFxOn must be true ONLY when PS2X_RD_FXCLASSIC starts with '1' (default now off).
B. render/rd_view.cpp:
1. Next to `static unsigned int s_prevTexId` (~340): statics s_sceneTexId, s_sceneFbo (unsigned), s_sceneW, s_sceneH (int), s_sceneFilled (bool).
2. In the draw function, before `auto emit2dBatch` (~4934):
   - static bool pauseBgOn: env PS2X_PAUSE_BG, default on, '0' disables.
   - Collect copyTargets (small fixed array) = `frame & 0x1FF` of every batch in g_rdGpu.local2dBatches with tme (`(prim>>4)&1`),
     ps2xRdIsFbFeedback(texSerial) and !isRdFbTexDisplayBatch(b).
   - tbp0 = tex0 & 0x3FFF, psm = (tex0>>20)&0x3F. fromTarget = (tbp0 & 31)==0 && (tbp0>>5) is in copyTargets.
     isPauseTint = tme && psm==0x1B && fromTarget. isPauseBlur = tme && psm==0 && fromTarget && (frame&0x1FF) not in copyTargets.
   - bool pauseFrame = pauseBgOn && at least one batch isPauseTint AND at least one isPauseBlur.
   - bool sceneSnapped=false; lambda takeScene(): wantW=vw, wantH=(int)((int64_t(vh)*512+224)/448); copy the backbuffer into
     s_sceneTexId exactly like copyToFbTarget (~7642) does for s_prevTexId (own rdgfx::BackbufferCopyState,
     beginBackbufferCopy / copyBackbufferToTexture(..., vx, vy, vw, vh, vw, vh, false) / endBackbufferCopy, same
     g_rdc.invalidateTex handling); set s_sceneFilled and sceneSnapped on success.
3. In draw2dUntil's while loop, right before `const uint32_t ate = ...` (~5335):
   - if (pauseFrame && isPauseBlur(b0)) { log2dReason(i2d, b0, "skip-pauseBlur"); ++i2d; continue; }
   - if (pauseBgOn && !pauseFrame && !sceneSnapped && drawn3dThisFrame > 0 && ((b0.prim >> 48) & 0xFF) != 0) takeScene();
     (bits 48..55 non-zero = first game UI draw, so the copy has no HUD.)
4. In emit2dBatch where `texId = rdFbTexSelectId(b0.tex0)` (~5036): if (pauseFrame && isPauseTint(b0) && s_sceneFilled &&
   s_sceneTexId != 0) { texId = s_sceneTexId; palDrawnThisFrame = true; } keep the existing palette handling that follows unchanged.
5. At end of frame, just before `if (!palDrawnThisFrame) // FIX-RD86` (~7664): if (pauseBgOn && !pauseFrame && !sceneSnapped &&
   drawn3dThisFrame > 0) takeScene();
If vx/vy/vw/vh are not in scope somewhere, say so instead of guessing. Reply in <=5 lines with the line ranges touched.
