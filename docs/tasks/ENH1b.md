# ENH1b: pass-through post stage (Vulkan). Small task. Do NOT build/run/commit.
Root c:\ApeEscape3_Recomp\PS2Recomp\ps2xRuntime. Mark changes `// FEAT-ENH1`. Do not edit .h files.
ENH1a already added rd_enhance.h, the setting, the call site and an empty `ps2xEnhanceApply` at the end of
rd_gfx_vk.cpp.

1. New src/lib/render/rd_enhance_vk.inc, included by rd_gfx_vk.cpp near the end INSIDE namespace rdgfx_vk
   (closes at ~line 4063) so it can use s_vk and the helpers: createImageAndView ~908, destroyTargets ~850,
   ensureTargets ~950, imageBarrier ~679, invalidateCommandBufferState ~1032, ensureRenderPass ~1094,
   createShaderModuleFromFile ~827, endFrame ~2281 (shows the MSAA resolve image).
   It defines `void enhanceApply(const RdEnhanceFrame &)`; ps2xEnhanceApply calls it when active().
2. New shaders/fx_full.vert (full-screen triangle from gl_VertexIndex) and shaders/fx_composite.frag
   (texelFetch of the colour copy, written unchanged). CMakeLists.txt: compile and copy them exactly like
   rd.vert / rd.frag (~line 575-605).
3. enhanceApply: return if no frame is active. End the current rendering (this resolves MSAA), copy the
   single-sample colour (resolve image if msaaSamples > 1, else colour image) into a sampled image, then begin
   rendering on the same colour target with LOAD (never clear) and draw the triangle: own pipeline with the same
   sample count and attachment formats as the main one, no blend, no depth test, no depth write. Depth contents
   must be preserved: check load/store ops. Leave layouts and tracked state so later 2D draws work unchanged
   (invalidateCommandBufferState).
4. Images and pipeline are created on first use, recreated when target size or sample count changes, destroyed
   with the targets. No per-frame allocations (descriptor set per frame in flight), no vkDeviceWaitIdle per frame.
5. Add VK_IMAGE_USAGE_SAMPLED_BIT to the depth image (~line 981).
6. Log once per (re)creation: `[enh] on w=<w> h=<h> msaa=<n>`. If creation fails, log once and do nothing.
Reply with the files and line numbers touched.
