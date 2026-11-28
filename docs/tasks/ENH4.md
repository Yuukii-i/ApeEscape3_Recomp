# ENH4: first working effects (screen-space), "they just need to work". Do NOT build/run/commit.
Root c:\ApeEscape3_Recomp\PS2Recomp\ps2xRuntime. Mark `// FEAT-ENH4`. No edits to existing .h except our own
src/lib/render/rd_enhance.h. Logs with ps2xSafeLog only. Read first: rd_enhance_vk.inc, rd_enhance.h,
shaders/fx_debug.frag (world reconstruction from depth), rd_enhance_profile.cpp (key table), the panel's
drawEnhanceProfileControls() in ps2_debug_panel.cpp, CMakeLists.txt shader block.

1. Settings: add `shadows{bool on; float strength, length, softness;}` (struct, profile keys shadows.*, panel group
   "Sun shadows"). Everything else already exists.
2. Active only when: Enhanced on, no debug view, a valid camera, ps2xEnhanceStageName() non-empty (menus and
   title stay untouched), and at least one effect on with strength > 0. Otherwise exactly the current pass-through.
3. Images: copy of the world colour (as now) plus a downsample chain (1/2, 1/4, 1/8, 1/16) made with
   vkCmdBlitImage linear, for bloom and depth of field. A linear-clamp sampler for those.
4. One fragment shader shaders/fx_effects.frag (plain and multisampled-depth variants, like fx_debug), in order:
   a) ambient occlusion: ~12 samples around the pixel using depth/world positions, radius/bias from ao.*;
   b) sun shadows: march ~24 steps from the pixel's world position toward the sun (sun.dir, normalised; flip the
      sign if needed so that "up" light darkens ground behind characters), project each step with the clip-from-
      world matrix, compare with the depth buffer, darken by shadows.strength when occluded (shadows.length =
      ray length in world units, softness = fade with hit distance). Offset the ray start to avoid self-shadowing;
   c) fog: distance fog between fog.start and fog.end plus height term (fog.height/falloff), colour fog.color,
      scaled by strength; sky gets fog.sky of it;
   d) light shafts: radial samples of bright pixels toward the sun's screen position, only when it is in front;
   e) depth of field: mix in downsampled levels by distance from dof.focus (0 = depth at screen centre);
   f) bloom: sum of thresholded downsample levels * strength;
   g) grading: exposure, contrast, saturation, tint (scaled by grade.strength).
   Pixels with no real depth (sky: cleared value or extremely far) skip a), b) and e) and count as sky for fog.
   Work in float; output the original alpha.
5. Settings reach the shader through a small uniform buffer per frame in flight (not push constants if > 128 B).
6. enhanced/levels/default.ini (parent repo, c:\ApeEscape3_Recomp\enhanced\levels\default.ini): enable all effects
   with moderate values (e.g. bloom 0.5 threshold 0.75; shadows 0.4; ao 0.4; fog 0.35 start 1500 end 12000, blue-grey;
   shafts 0.25; dof 0.3; grade 1.0 with saturation 1.1 contrast 1.05), sun.dir=0.35,-0.8,0.5, sun.color=1,0.93,0.8.
   Check which world axis is "up" from the camera code or note that you assumed -Y.
7. Log once on activation `[enh] effects on stage=<name>`.
Reply in at most 8 lines: files, assumptions (up axis, depth direction), anything unsure.
