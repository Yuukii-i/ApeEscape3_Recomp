# Ape Escape 3 (SCUS_975.01) Static Recompilation

A static recompilation of the PlayStation 2 game **Ape Escape 3** (NTSC-U, `SCUS_975.01`) for modern PCs, built on a fork of [PS2Recomp](https://github.com/ran-j/PS2Recomp).

The game's MIPS R5900 (Emotion Engine) executable is translated ahead of time into native C++ (`recomp_source/`). A custom runtime then provides the rest of the console: kernel and scheduler, GIF/GS/VU0/VU1/VIF/IPU/DMA hardware, and high-level emulation of the IOP services the game talks to (file streaming, memory card, controller, sound).

> ## ⚠️ Early development: audio works, speed is much better, random crashes still happen
> **Audio now works**: music, sound effects, voices and movie sound, played by the game's own sound driver (on by default; `PS2X_SG2_LLE=0` turns it off). **Speed is much better**: on the test laptop most of the game runs at or near 60 fps, with occasional dips. **The game still crashes at random**, and **it is unknown whether it can be beaten**: nobody has played it from start to finish on this port.
>
> It boots, plays the opening movies, shows the title menu and character select in 3D, and the first levels can be played from start to finish: walking, camera, the net, capturing monkeys, the level-complete screen, the cutscenes and the hub (lobby). Saving is still unsolved (see below). This is a development snapshot, not a release.

You need your own legally obtained disc image of the game. **No game files, executables, or assets are included in this repository**, and none should ever be committed.

---

## What works today

**Boot and system**
- The recompiled game runs from `crt0` through the game's own startup, thread/heap setup and main loop, driven by a cooperative EE scheduler with deterministic virtual time.
- Loading screen, memory card screen, SCEA logo, both opening movies, title menu, character select.

**Gameplay (tutorial level and hub)**
- Walking, jumping, crouching, camera, the net, lock-on facing and capturing the first monkey, then the stage-clear screen, the scene movie and loading the hub.
- The real game's behaviour was matched against PCSX2 for each of these fixes (see `docs/HYPOTHESES.md`, entries C311 to C330).

**Disc and IOP services (HLE)**
- `DATA.BIN` virtual file index (VFI) reader (`tools/vfi/`), streaming through the game's `CID1` (`file3.irx`) protocol: open, read, seek, stat, directory listing and async job slots.
- Memory card (mcman/mcserv) backed by a host directory, controller handshake, SIF/RPC plumbing.

**Audio** (on by default; `PS2X_SG2_LLE=0` turns it off)
- The game's own sound driver (`sg2iopm1.irx`) runs on an IOP (R3000A) interpreter, with `libsd` emulated on top of a software SPU2: ADPCM voices, ADSR envelopes, pitch, volumes, streamed BGM and movie audio, output through Raylib at 48 kHz.
- Sequenced music (the game's MIDI player on the EE), sound effects, voices, the title theme and movie sound all play. Reverb is not emulated yet.
- `PS2X_AUDIO_WAV=<file>` records the mixed output to a WAV file.

**Graphics**
- GIF arbiter, VU1 micro-mode interpreter plus a native hot-block path, VIF1 UNPACK, a software GS rasteriser and an optional Vulkan GS backend (`PS2X_GS_VULKAN=1`), with a Raylib presentation window.
- `PS2X_ASPECT=16:9` stretches the picture for the game's own widescreen mode (the 2D UI looks stretched, not yet corrected).

**Tooling**
- PCSX2 is the reference ("golden") behaviour. Findings go in `docs/golden_pcsx2.md`, every hypothesis (confirmed or refuted) in `docs/HYPOTHESES.md`.
- Profiling sampler and per-subsystem probes (`PS2X_PROF_SAMPLE`, `PS2X_PROF_COUNTS`), RAM dump hotkeys (F9 full RAM, F10 frame sequence), VFI tool, VU1 generators, log digest scripts under `tools/`.

---

## Known issues

- **Performance**: much better than before. On the test laptop (Ryzen 7 7435HS, silent power mode) the median frame rate is 58 to 60 fps in every part of the test route (title, hub, shop, first levels), with occasional dips in heavy scenes. A locked 60 with headroom is the goal.
- **Stability**: the game still crashes at random. Known crash spots include the castle, the recording studio door and the Halloween water area.
- **Audio**: reverb is not emulated.
- **Saving**: using the save station in the hub soft-locks (the game asks for its save folder, gets "no entry" from the blank card, then waits forever).
- The gadget menu's Select button can soft-lock.
- Widescreen UI scaling, display filtering and other display options are not finished.
- Only the first levels and the hub have been played; later levels are mostly untested, and it is unknown whether the game can be beaten.

---

## Not done yet

- Fixing the random crashes, saving and loading, reverb.
- Performance work (guest-code overhead, VU0/VU1 plumbing).
- Testing and fixing everything beyond the hub: the other levels, bosses and modes.
- Enhancements: high frame rates, widescreen UI, resolution scaling.

---

## Building and running

Requirements: Windows, Visual Studio (MSVC, C++20), CMake, the Vulkan SDK (for the Vulkan backend). The scripts under `tools/` and the root `build_release.bat` are written for the author's setup (Visual Studio 2026 at the default path); adjust the `vcvars64.bat` path if yours differs.

The game-derived sources are **not** in this repository and must be generated locally from your own copy of the executable:

1. Generate `recomp_source/` from `SCUS_975.01` with the recompiler (`docs/REGEN.md`).
2. The generator has not been re-run for several fixes, so apply these in-place patch scripts to `recomp_source/` (all are idempotent): `tools/fix_vu0_flags.py`, `tools/fix_sqrt_s.py`, `tools/fix_vu0_q.py`, `tools/fix_vu0_r.py`, `tools/fix_delay_slots.py`, `tools/fix_branch_s64.py` (64-bit sign tests in branches; without it the music never plays), and `tools/fix_hidden_entries.py --addrs tools/hidden_entries.txt --split-returns` (registers functions and call-return points the splitter hid; without it entering water and un-morphing crash).
3. Generate the VU native code into `PS2Recomp/ps2xRuntime/src/lib/vu/generated/` with `tools/vu1gen/gen_vu1_native.py` and `tools/vu1gen/gen_vu1_hot.py` (these files are Sony-derived and are not tracked).

```
git clone --recurse-submodules https://github.com/Yuukii-i/ApeEscape3_Recomp.git
cd ApeEscape3_Recomp
build_release.bat
```

(or `cmake -B build -DCMAKE_BUILD_TYPE=Release -DPS2X_ENABLE_AGRESSIVE_LOGS=OFF` followed by `cmake --build build`). Release builds are required for meaningful speed. A full rebuild of the generated sources takes hours; `tools/overnight_build.bat` runs one at low priority.

Run (the usual set of switches):

```
set PS2X_GS_ASYNC=1
set PS2X_VIF1_ASYNC=1
set PS2X_GS_VULKAN=1
.\build\PS2Recomp\ps2xRuntime\ps2EntryRunner.exe SCUS_975.01
```

The runner finds the disc image from `PS2X_ISO`, or `ApeEscape3.iso` in the working directory (a few relative locations are tried as well).

Useful switches (environment variables):

| Variable | Effect |
| :--- | :--- |
| `PS2X_ISO` | Path to the game disc image. |
| `PS2X_GS_VULKAN=1` | Use the Vulkan GS backend. |
| `PS2X_GS_ASYNC=1`, `PS2X_VIF1_ASYNC=1` | Asynchronous GS and VIF1 processing (faster). |
| `PS2X_SG2_LLE=0` | Turn audio off (by default the game's own sound driver runs). |
| `PS2X_AUDIO_WAV=<file>` | Record the audio output to a WAV file. |
| `PS2X_ASPECT=16:9` | Display aspect (`16:9`, `16:10`, `4:3`, `fill`); use with the game's widescreen option. |
| `PS2X_EE_RTZ=0` | Disable the EE round-toward-zero default (debugging only; breaks animation). |
| `PS2X_VU0_HWQ=0` | Disable the hardware divide/sqrt semantics for VU0 (debugging only). |
| `PS2X_VTIME=0` | Disable virtual time (wall-clock scheduling). On by default; the movies need it. |
| `PS2X_PROF_SAMPLE=1`, `PS2X_PROF_COUNTS=1` | Sampling profiler and per-second counters. |
| `PS2X_DUMP_FRAMES=1` | Save debug PNG dumps of frames to `frames/`. |

---

## Repository layout

- `PS2Recomp/` : the recompiler and runtime (fork of PS2Recomp), included as a submodule (branch `perf/aggressive` has the current state).
- `recomp_source/` : generated game code (not in the repository, regenerate locally).
- `docs/` : specs and findings (CID1, DBC, SG2 protocols, memory map audit, `golden_pcsx2.md`, `HYPOTHESES.md`).
- `tools/` : VFI archive tool, IOP module analysis, in-place patch scripts for the generated code, VU1 generators, build scripts, log digest and comparison scripts.
- `scripts/` : helper and patch scripts.
- `config.toml` : recompiler configuration (entry ELF, stubs, function mappings).
- `NOTES.md` : verified system facts, memory maps, and protocol layouts.
- `PLAN.md` : an early, now partly outdated, milestone plan kept for history.

---

## Development approach

This is a reverse-engineering project done by one person with heavy help from AI coding assistants for analysis and implementation, using PCSX2 as the source of truth for how the real game behaves. Claims in the docs are tagged by evidence: `[CONFIRMED ...]` for observed runtime data and `[INFERRED]` for conclusions from reading code.

## Credits

- [PS2Recomp](https://github.com/ran-j/PS2Recomp) by ran-j and contributors, the base recompiler and runtime this project extends.
- [PCSX2](https://pcsx2.net) for the reference emulator used throughout.
- Ape Escape 3 is the property of Sony Interactive Entertainment. This project is unaffiliated. The repository contains no game code or assets: `recomp_source/` and the generated VU code are produced locally from a copy you own.
