# ENH2b: world position from depth, with two debug views. Small task. Do NOT build/run/commit. No edits to existing
.h except our own src/lib/render/rd_enhance.h. Root c:\ApeEscape3_Recomp\PS2Recomp\ps2xRuntime. Mark `// FEAT-ENH2`.
Logs must use ps2xSafeLog (plain stderr is discarded). ENH2a already fills RdEnhanceFrame camera/cameraValid.

1. Setting: env PS2X_ENH_DEBUG = depth | grid (default none). `int ps2xEnhanceDebugView(); void
   ps2xEnhanceSetDebugView(int);` (0 none, 1 depth, 2 grid) in config/ps2x_config.cpp next to ps2xEnhanceOn;
   declare in rd_enhance.h. ps2_debug_panel.cpp: combo "Enhanced debug view" under the Enhanced checkbox.
2. rd_gfx_vk.cpp: per frame remember the push constants uFlip, uVpA, uVpB, uFbSize and the Vulkan viewport of the
   3D draw (uMode2d == 0 and uVpB.w > 0.5) with the largest index/vertex count (drawIndexed ~2966 / drawArrays;
   viewport as set in applyViewportAndScissorIfDirty ~1060). Reset each frame.
3. gsToClip: the linear map shaders/rd.vert applies to aPos=(x,y,z,w) in its uVpB.w>0.5 branch followed by the
   final y flip and z remap. With A=uVpA, B=uVpB, F=uFlip, S=uFbSize it is:
     numX = x*A.x + w*A.z;  numY = y*A.y + w*A.w
     X = ((2*(numX - w*B.x/16)/S.x - w) / B.z) * F.x
     Y = (w - 2*(numY - w*B.y/16)/S.y) * F.y
     Z = (z*F.z + w) * 0.5;  W = w
   (check this against the shader). `aPos = camera * vec4(world,1)` where camera's COLUMNS are the four stored
   vec4 (camera[0..3] is column 0). So clipFromWorld = gsToClip * camera. Use double precision for the inverse.
4. rd_enhance_vk.inc: when a debug view is selected, use a second pipeline with new shaders/fx_debug.frag
   (add to CMakeLists.txt like fx_composite.frag) instead of the plain composite. Sample the depth image (it
   already has SAMPLED usage; multisampled: texelFetch sample 0, so a sampler2DMS variant or second shader for
   msaa>1) with a depth-only view and correct layout barriers; return depth to its attachment layout afterwards
   with contents unchanged. ndc.x = (fragX - vp.x)/vp.width*2-1, same for y, ndc.z = depth.
   world = inverse(clipFromWorld) * vec4(ndc,1), divide by w.
   depth view: grey = fract(viewDistance / 500.0), viewDistance = (camera*vec4(world,1)).w.
   grid view: original colour with 1-pixel-ish lines where world x, y or z crosses a multiple of 50 (use fwidth),
   x red, y green, z blue.
   If cameraValid is false or no 3D draw was seen, draw the plain composite.
5. With no debug view selected the stage must behave exactly as before.
Reply with files and line numbers, and anything you are unsure about.
