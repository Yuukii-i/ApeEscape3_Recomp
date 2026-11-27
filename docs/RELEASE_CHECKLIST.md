# Release checklist (draft, 2026-11-23)

## What ships
- Runtime exe (Release build via tools/build_avx2.bat or the PGO build), launcher exe (tools/build_launcher.bat, when it exists), default ps2x.ini, licence files, a short README (how to supply your own disc image).
- Shaders/SPIR-V the renderer loads at runtime (check the build output folder for the exact list).

## What never ships (and never gets pushed)
- Game assets or copyrighted material: ISOs, BIOS, the ELF (SCUS_975.01), extracted game data, memory cards (Mcd001*.ps2), GS/RAM dumps and PCSX2 refs (refs/pcsx2_dumps), texture dumps (logs/rdtex), screenshots of the game from replays.
- recomp_source/ (generated from the game) and any file with raw instruction words, disassembly or packet dumps.
- logs/, *.padrec recordings (they contain only inputs but keep them out of releases), ps2x.ini.bak, build_* folders, tokens/secrets.

## Before tagging / pushing
1. `git status` + `git diff --staged`: nothing from the "never ships" list.
2. Scan added lines for `// 0xADDR: 0xWORD` comments, disassembly-like hex columns, new binary/image files.
3. Release build passes locally; run the hub + one level + level select replay (`PS2X_LOAD_TIMING=fast`) and compare screenshots with the previous release.
4. Not on `main`: push the PS2Recomp submodule branch first, then the parent with the new pointer; PR + squash merge per CLAUDE.md; tag `v0.x.y` on main after merge.
5. Release notes: what changed, known issues (blur at the castle fly-by, transition length, hub haze until fixed), settings added.
