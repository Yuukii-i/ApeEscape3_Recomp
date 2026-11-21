# Vulkan port of the new renderer (rd_view): plan
Status: PLAN 2026-11-21. Branches: PS2Recomp feat/sdl3-frontend (SDL3 platform layer done: window, Vulkan swapchain, input, audio; classic frame only).
Decision (user, 2026-11-21): port our own renderer from OpenGL/raylib to Vulkan; GL kept until the Vulkan path matches it; V4 (delete GL + raylib) only with the user's review.

## Why this shape
rd_view.cpp (3.9k lines) = CPU logic (ring slots, batches, texture notes, FBTEX/PREV/snapshots, effect handling) + a GL executor (~40 distinct gl*/rl* operations, 2 small GLSL shaders). Textures come from rd_texture.cpp (CPU decode -> GL texture ids). So: put a thin graphics interface `rdgfx::` between the logic and the API. GL implementation = today's calls verbatim (behaviour identical); Vulkan implementation = new. The logic is written once.

## Stages
- RDG1 (mechanical, GL only): new rd_gfx.h + rd_gfx_gl.cpp; rd_view.cpp and rd_texture.cpp call rdgfx:: instead of rl*/gl*/raylib shader calls. Own enums for blend factors / depth funcs / filters / wraps. Acceptance: builds, identical pictures (A/B screenshots vs the pre-refactor exe on the scripted pause/hub runs), same fps.
- RDG2: Vulkan implementation core (rd_gfx_vk.cpp): shares the SDL platform's VkDevice/queue; offscreen color+depth target (MSAA optional) resolved/blitted into the swapchain letterboxed; pipeline cache keyed by state (blend, depth, cull, color mask, topology); one descriptor set layout (sampler0 + palette sampler1) + push constants for the uniform block; dynamic vertex/index buffers; scissor/viewport dynamic. Shader: the same two shaders ported to GLSL 450, compiled to SPIR-V at build time (glslc custom command) or embedded arrays.
- RDG3: textures (create/update/params/mipmaps/delete, handle table uint32 -> VkImage), screen-copy-to-texture (PREV, snapshots).
- RDG4: SDL loop integration: PS2X_FRONTEND=sdl keeps takeover ON and calls ps2xRdDraw per frame inside the platform's frame; the classic effect frames (FX) present the classic image path.
- RDG5: A/B against GL with scripted runs, perf, then default decision (user).
- Later: V3 effects natively (pause tint, fades, swirl), Enhanced renderer hooks (docs/OVERHAUL_PLAN.md).

## Rules
.cpp + NEW headers only (never edit existing runtime headers: hours rebuild). Every stage env-gated or behaviour-identical. Gemini codes, Claude specs/builds/measures. Pre-refactor reference exe: build_avx2\...\base_prerdg.exe.
