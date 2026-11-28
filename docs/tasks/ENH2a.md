# ENH2a: carry the camera matrix to the post stage. Small task. Do NOT build/run/commit. No edits to existing .h.
Root c:\ApeEscape3_Recomp\PS2Recomp\ps2xRuntime. Mark `// FEAT-ENH2`. rd_enhance.h already has
RdEnhanceFrame { vpScaleZ, vpOffsetZ, camera[16], cameraValid, gsToClip[16] } (it is our own header; do not change it).

The camera is VU1 data memory quadwords 998..1001 (view-projection), as 4 consecutive vec4 in that order
(see `ldq(vu, 998u + r)` in vu1_func.inc ~line 2663).

1. src/lib/vu/vu1_func.inc: in beginLeanDraw (~line 2740-2774), where vpScaleZ/vpOffsetZ are taken from the draw
   with the most vertices (~line 2761), also copy those 16 floats into new SceneFrame members (camera[16],
   cameraValid; SceneFrame ~line 985-1026; reset in clear()). Only when ps2xEnhanceOn() or PS2X_ENH_DEBUG is set
   (declare `extern bool ps2xEnhanceOn();`).
   Right before the ps2xRdPublishLean call (~line 2452) call
   `::ps2xRdPublishCamera(cur.cameraValid ? cur.camera : nullptr);` (declare it extern).
2. src/lib/render/rd_view.cpp: define ps2xRdPublishCamera; store it as pending and make it follow EXACTLY the
   path of vpScaleZ (g_rdLastVpScaleZ -> slot.vpScaleZ ~line 2332; ring/gs copies ~line 3312; candVpScaleZ in the
   composition ~lines 3674-3700 and its assignment to g_rdGpu ~line 3856; struct members ~lines 650/708/786).
   At the enhance call site (~line 7517) fill f.camera / f.cameraValid from g_rdGpu.
3. Count distinct cameras: in vu1_func.inc, only if PS2X_ENH_DEBUG is set, hash quadwords 998..1001 per lean draw
   and once per second log with ps2xSafeLog `[enh] cam frames=<n> maxDistinctPerFrame=<n> changed=<frames whose
   chosen camera differs from the previous frame>`.
Reply with files and line numbers.
