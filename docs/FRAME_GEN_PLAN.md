# Frame generation (FSR and DLSS): feasibility and plan (2026-11-28)

Status: not implemented. Checked from documentation and our code; nothing downloaded or installed.

## What both need from us

| Input | Today |
|---|---|
| World depth | Available to the enhanced effect stage |
| Camera matrix, this frame and previous | This frame available; keeping the previous one is small |
| Picture without HUD, or a way to draw the HUD after | Available: effects already run before the HUD |
| Motion vectors | **Missing.** From camera + depth we can compute camera motion only |
| Control of presentation | **Missing.** The tool must own the swapchain (our code: `platform/ps2_sdl_platform.cpp`) |

With camera motion only, characters, enemies, particles and the snow would smear or double. Real
object motion needs each object's previous position; the earlier geometry-matching attempt failed.

## FSR frame generation (AMD, works on any recent card)

- FidelityFX SDK v1.1.4 supports Vulkan (449 MB download from AMD's GitHub). It was published as
  MIT licensed; read the license file of the download before relying on that. Newer SDK 2.x exists;
  its Vulkan support must be checked first.
- The SDK replaces our swapchain and present calls and wants extra queues (the RTX 4060 has them).
- Work: device and queue setup, swapchain replacement, motion vector pass, frame pacing (game 60,
  screen 144), HUD handling, then tuning.

## DLSS frame generation (NVIDIA)

- Through NVIDIA's Streamline kit. Vulkan is supported; NVIDIA's guide says VSync with frame
  generation and multi-frame modes are limited to Direct3D 12.
- RTX 40 does 2x; RTX 50 more. Your laptop (RTX 4060) would get 2x.
- **Needs your approval:** the libraries come under NVIDIA's license, which has conditions for
  anyone who distributes them. I have not accepted or downloaded anything.

Sources: [AMD FSR SDK](https://gpuopen.com/amd-fsr-sdk/),
[FSR 3.1 integration overview](https://gpuopen.com/download/FidelityFX_Super_Resolution_3-1_Release-Overview_and_Integration.pdf),
[Streamline DLSS-G guide](https://github.com/NVIDIA-RTX/Streamline/blob/main/docs/ProgrammingGuideDLSS_G.md).

## Proposed order

1. Camera-motion vectors from depth, with a debug view (small, useful for either).
2. FSR frame generation behind a setting, on its own branch; judge the smearing on characters.
3. Decide whether object motion vectors are worth the work.
4. DLSS, if you accept NVIDIA's terms.

## Decisions for the user

1. May the AMD SDK be downloaded into the project (kept out of git)?
2. Do you accept NVIDIA's license for DLSS, or leave DLSS out?
3. Is a first version with smearing on moving characters acceptable to try?
