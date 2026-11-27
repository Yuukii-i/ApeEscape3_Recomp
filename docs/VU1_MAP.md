# VU1 map (measured 2026-11-23, build with FIX-E8g, PS2X_VU1_FUNC=1 PS2X_VU1_HPROF=1 PS2X_VU1_FUNC_NEW=1, replay overnight_hub.padrec + `warp <stage>`, 35 s after warp)

## Coverage result
The functional C++ VU1 engine (PS2Recomp/ps2xRuntime/src/lib/vu/vu1_func.inc, ~5000 lines) already runs EVERY in-game VU1 program we measured:
`[vfunc] fallback=0` in all six scenes. Only the one-off image 4279fa21 (~117 runs per session, 0 taken, 20 unhandled; boot/intro one-off) stays on the exact interpreter,
and d6b2281a (267 runs, all taken). Microcode images seen: 86503d3905e35276 (main, all gameplay), d6b2281aa7efd05a, 4279fa21....

| scene | vu1 ms/frame total | taken | fallback | top handlers (ms/frame / calls per frame) |
|---|---|---|---|---|
| hub travel_a | 7.3 | 6.6 | 0.00 | 1EE0 1.81/2008, 2440 1.18/446, 2900 0.65/338, 00A8 0.63/531, 15E0 0.56/202, 1C48 0.40/629 |
| woods_a | 7.9 | 7.2 | 0.00 | 1EE0 2.58/3019, 00A8 0.83/750, 0B40 0.82/770, 2440 0.71/352, 15E0 0.44/180, 2900 0.37/182 |
| castle_a | 6.1 | 5.5 | 0.00 | 1EE0 2.47/2780, 00A8 0.71/615, 2440 0.44/234, 2900 0.39/208, 15E0 0.18/66, 1C48 0.09/140 |
| space_a | 3.6 | 3.2 | 0.00 | 1EE0 1.08/1357, 2440 0.62/251, 00A8 0.38/341 |
| studio_a | 4.7 | 4.2 | 0.00 | 2440 1.52/757, 1EE0 0.61/671, 15E0 0.52/210 |
| ciscocity_a | 2.9 | 2.7 | 0.00 | 2440 0.77/375, 1EE0 0.54/601, 2900 0.32/173 |
Logs: logs/map_<stage>_err.txt (`[vu1h]` and `[vfunc]` lines). Handler 1EE0 (skinned model) is the biggest single cost everywhere; 2440 (rigid) second; 2900 (clipping) third.

## Handlers implemented in vu1_func.inc (names from the file)
Dispatcher/utility 00A8 (object matrix), 0088, 0C80 (copy), 0050, 0060, 0070; geometry 1EE0 (skinned, lean variant FEAT-RD40), 2440 (rigid), 2900/clipPolygon (clipping), 15E0, 1900, 1910, 1C48 (light matrix block), 3160, 0B40, 0AF0, 0B38, 1CC0/1CD8, 32A0, 0560, 0AE0, 0C38, 1E50, 2E20, 2E88;
lights (each a named C++ function with its own comment): 0840 point specular (Blinn-Phong), 0CC0 diffuse spotlight, 1090 specular spotlight, 02E0 4-directional specular, 0628 point diffuse, 1720 point ambient/falloff, 0198 4-directional diffuse.

## Lighting needs vs what we have
| need | status | evidence |
|---|---|---|
| vertex positions before projection | AVAILABLE | SceneVertex.pos[4] (vu1_func.inc:831), filled in rigid/skinned/clip paths (:1985, :2046, :2128) |
| normals | AVAILABLE (skinned + rigid paths) | `_mm_storeu_ps(sv.normal, ldq(vu, 556+ix))` :2050/:2132; rigid path zero-fills normal at :1988 (check per handler) |
| object matrix | AVAILABLE | SceneDraw.objMatrix, scene::setObjMatrix in handler00A8 (:1178) |
| bone matrices | PARTIAL | SceneDraw.boneCount only; matrices are consumed inside 1EE0 skinning, not exported |
| light constants (direction/colour/position/cone) | PARTIAL | the 7 light handlers are decompiled and read them from VU memory, but nothing exports them as named data; EE side writes them via emitVu1LightMatrixBlock (DECOMP_LOG BY3, handler ids 0x3F2/0x321/0x39B...) |
| material (TEX0/ALPHA/TEST) | AVAILABLE | SceneGs {prim, tex0, clamp, tex1, alpha, test, frame, zbuf, texa} |
| depth | AVAILABLE | Vulkan depth buffer in the renderer |
| per-object id / hierarchy | MISSING | no stable object id in SceneDraw (handlerPc, mscalIndex, gifOffset only) |
| shadow casters list (silhouette geometry by object) | MISSING | needs object id + bone export |

## Consequence for the plan
Phase 3 as "decompile the programs" is already done for gameplay. What remains: (1) export the missing semantic data (light constants, bone matrices, object id) into SceneDraw without changing GIF bytes, (2) the one-off image 4279fa21 (optional, ~117 runs/session), (3) the consumer: a renderer path that uses positions + normals + lights for shadows/lighting.

## V2 result (2026-11-23)
FEAT-V2 exports SceneGlobals (view-proj qwords 998..1001, viewport, ambient qword 1014, light scale qword 1013, fog qword 1016) per draw when PS2X_SCENE=1: hub shows ambient=(1,1,1), lightScale=128, scene check mismatch=0. The 7 light handlers are NOT executed in the hub or in seaside_a (lights=0 per frame; none appears in any scene's top-handler list): gameplay lighting arrives as EE-precomputed vertex colours, so a modern lighting path must either rebuild light sources from the EE side (light matrix block, handler 1C48, ~130 calls/frame) or derive them from the stage data, not from the VU light handlers. The light handlers were exercised in the shop image only.
