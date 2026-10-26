# Ape Escape 3 (SCUS_975.01) Static Recompilation

A static recompilation of the PlayStation 2 game **Ape Escape 3** (NTSC-U, `SCUS_975.01`) for modern PCs, built on a fork of [PS2Recomp](https://github.com/ran-j/PS2Recomp).

The game's MIPS R5900 (Emotion Engine) executable is translated ahead of time into native C++ (`recomp_source/`). A custom runtime then provides the rest of the console: kernel and scheduler, GIF/GS/VU1/VIF/IPU/DMA hardware, and high-level emulation of the IOP services the game talks to (file streaming, memory card, controller, sound).

> ## ⚠️ This game is NOT playable yet
> The project is in an early stage. It boots, shows the loading and memory card screens, the SCEA logo, and plays both opening movies (the Dolby logo and the full intro cinematic) up to the title scene. **There is no menu, no 3D rendering, no sound output, and no gameplay yet.** Expect crashes, graphical glitches and slow performance. This is a development snapshot, not a release.

You need your own legally obtained disc image of the game. **No game files, executables, or assets are included in this repository**, and none should ever be committed.

---

## What works today

**Boot and system**
- The recompiled game runs from `crt0` through the game's own startup, thread/heap setup, and main loop, driven by a cooperative EE scheduler.
- Loading screen, memory card screen and SCEA logo are shown.
- Deterministic "virtual time" scheduling (on by default): vblank events and the guest's audio clock advance from the guest's own cycle count rather than host wall time, which the movie code depends on.

**Disc and IOP services (HLE)**
- `DATA.BIN` virtual file index (VFI) reader: 3,994 files / 266 directories resolved from the ISO (`tools/vfi/`).
- File streaming through the game's `CID1` (`file3.irx`) protocol: open, read, seek, stat, directory listing, and async job slots.
- Memory card (mcman/mcserv) backed by a host directory, controller handshake (DBC), and SIF/RPC plumbing.
- SoundGroup2 (SG2) RPC handling, including the **playback-position clock** the movie streamer uses for pacing. (No audio is produced yet, see below.)

**Graphics**
- GIF arbiter (PATH1/2/3), VU1 micro-mode interpreter, VIF1 UNPACK, and a software GS rasteriser (all primitives, texture/CLUT formats, alpha/Z/scissor tests), with a Raylib presentation window.
- Fast paths for the heavy cases the movies hit (sprite fills, page-linear sprites, UNPACK).

**Full-motion video**
- Both opening movies play: the Dolby logo movie and the intro cinematic (`new_advertise.str`, 6213 frames) all the way to the end.
- MPEG-2 decoding runs through an HLE of the IPU, with the game's own VU1 colour-conversion data converted natively per 16x16 block and uploaded to the GS in batches.

**Tooling**
- PCSX2 is used as the reference ("golden") behaviour. Findings are recorded in `docs/golden_pcsx2.md`, and every hypothesis, confirmed or refuted, in `docs/HYPOTHESES.md`.
- Built-in profiling sampler and per-subsystem probes (`PS2X_PROF_SAMPLE`, `PS2X_PROBE_AE`, `PS2X_PROBE_DC`), VFI tool, and log digest scripts under `tools/`.

---

## Known issues

- Movie playback **stutters**: motion looks like it steps back and forth. Under investigation.
- A short (about one second) decode stall occurs near the end of the intro cinematic.
- When the intro ends the game moves on to the title scene, which is not rendered correctly. Expect a screen of garbage pixels and a wrong picture height.
- The memory card screen draws a message box with the wrong height.
- No way to skip the movies yet.
- Performance is limited by the software rasteriser.

---

## Not done yet

- **3D rendering**: the title scene, menus and every in-game scene. This is the next big milestone and likely means moving from the software GS to a GPU renderer.
- **Sound**: the audio clock exists, but there is no ADPCM decoding, mixing, or output. Movies and the game are silent.
- **Gameplay**: input mapping and validation against the real game, game logic that depends on the unimplemented systems above, save/load.
- **Everything beyond the intro**: title menu, game modes, levels, bosses.
- **Enhancements** (after the game is actually playable): high frame rates, widescreen, resolution scaling.

---

## Building and running

Requirements: Windows, Visual Studio (MSVC, C++20), CMake. The scripts under `tools/` and the root `build_release.bat` are written for the author's setup (Visual Studio 2026 at the default path); adjust the `vcvars64.bat` path to match yours.

You must first generate the recompiled sources from your own copy of the executable. `recomp_source/` is intentionally not in the repository. See `docs/REGEN.md`.

```
git clone --recurse-submodules https://github.com/Yuukii-i/ApeEscape3_Recomp.git
cd ApeEscape3_Recomp
build_release.bat
```

(or `cmake -B build -DCMAKE_BUILD_TYPE=Release -DPS2X_ENABLE_AGRESSIVE_LOGS=OFF` followed by `cmake --build build`). Release builds are required for meaningful speed; debug builds are far too slow.

Run:

```
.\build\PS2Recomp\ps2xRuntime\ps2EntryRunner.exe SCUS_975.01
```

The runner finds the disc image from `PS2X_ISO`, or `ApeEscape3.iso` in the working directory (a few relative locations are tried as well).

Useful switches (environment variables):

| Variable | Effect |
| :--- | :--- |
| `PS2X_ISO` | Path to the game disc image. |
| `PS2X_VTIME=0` | Disable virtual time (wall-clock scheduling). On by default; the movies need it. |
| `PS2X_PROF_SAMPLE=1` | In-process sampling profiler, prints speed and hot spots. |
| `PS2X_DUMP_FRAMES=1` | Save debug PNG dumps of frames to `frames/`. |
| `PS2X_PROBE_DC=1` | Lightweight movie/scheduler probes. |

---

## Repository layout

- `PS2Recomp/` : the recompiler and runtime (fork of PS2Recomp), included as a submodule.
- `recomp_source/` : generated game code (not in the repository, regenerate locally).
- `docs/` : specs and findings (CID1, DBC, SG2 protocols, memory map audit, `golden_pcsx2.md`, `HYPOTHESES.md`).
- `tools/` : VFI archive tool, IOP module analysis, log digest and GS comparison scripts.
- `scripts/` : helper and patch scripts.
- `config.toml` : recompiler configuration (entry ELF, stubs, function mappings).
- `NOTES.md` : verified system facts, memory maps, and protocol layouts.
- `PLAN.md` : an early, now partly outdated, milestone plan kept for history.

---

## Development approach

This is a reverse-engineering project done by one person with heavy help from AI coding assistants for analysis and implementation, using PCSX2 as the source of truth for how the real game behaves. Claims in the docs are tagged with their evidence (log or PCSX2 observation versus code reading).

## Credits

- [PS2Recomp](https://github.com/ran-j/PS2Recomp) by ran-j and contributors, the base recompiler and runtime this project extends.
- [PCSX2](https://pcsx2.net) for the reference emulator used throughout.
- Ape Escape 3 is the property of Sony Interactive Entertainment. This project is unaffiliated. The repository contains no game code or assets: `recomp_source/` is generated locally from a copy you own.
