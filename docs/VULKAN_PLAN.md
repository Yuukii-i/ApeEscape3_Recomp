# Vulkan GS backend plan (decided 2026-10-28: Vulkan first, D3D11 maybe later)

Why: gameplay GS is the bottleneck (probe_hx: GS thread 100% busy, ~16M px/s, 5-7 vsync/s; 60 fps needs ~160M px/s). C202.
Seam: GS frontend (gs/gs_frontend.cpp) already hands the backend `GSPrimitiveBatch` (GSDrawState + vertices) via
GSCpuBackend::DrawPrimitive. CPU backend stays as fallback + correctness reference (env PS2X_GS_VULKAN=1 opts in).

## Window decision
Host window is raylib (OpenGL context, no Vulkan swapchain). Do NOT replace it. Vulkan renders OFFSCREEN; each vsync the
display image (existing PresentFromLocalMemory request) is read back (640x512 RGBA, small) and uploaded to the raylib
texture exactly like the CPU path does today. No swapchain, no window-system code. (Revisit for zero-copy later.)

## Dependencies (user installs once)
LunarG Vulkan SDK (headers, glslc, validation layers). CMake: find_package(Vulkan) behind option PS2X_VULKAN (default OFF
until stage 2 works). Shaders: GLSL -> SPIR-V by glslc at build time, embedded as uint32_t arrays.

## Stages (each independently playable; CPU path untouched)
V0  Bootstrap: instance/device/queue, offscreen image, clear + readback; prints GPU name. Proves toolchain.
V1  VRAM mirror: 4 MB GS VRAM as a GPU storage buffer; every CPU-side VRAM write (GIF image upload, local-to-local,
    CPU rasteriser fallback draws) marks dirty page ranges that get uploaded before the next GPU draw.
V2  Draw: GSPrimitiveBatch -> vertex buffer + pipeline keyed by (prim type, ABE/blend, ATE, ZTE, FBMSK, psm).
    Framebuffer and Z live IN the VRAM storage buffer (fragment shader does swizzled read/modify-write with
    fragment interlock / per-primitive ordering) => exact PS2 framebuffer-format semantics, no format conversion,
    CPU can still read VRAM after a GPU->host sync. (Simplest correct design; optimise with render targets later.)
V3  Textures: sampled directly from VRAM buffer in the shader (swizzle + CLUT + TEXA + wrap/clamp + bilinear in GLSL).
V4  Sync points: local-to-host, display capture, texture-from-framebuffer, any CPU VRAM read => flush GPU + download
    dirty pages. Lazy: track per-page GPU-dirty bits.
V5  Perf: render targets for hot FBPs, tile binning, async compute, multi-queue.

## Verification
Per-frame image diff GPU vs CPU backend (PS2X_GS_COMPARE=1: render both, report mismatching px count per frame),
PCSX2 screenshots only for sanity.

## Open risks
Fragment interlock availability (VK_EXT_fragment_shader_interlock) - needed for ordered RMW; fallback: per-primitive
barriers (slow) or tile-sorted compute rasteriser (planned B-option).
