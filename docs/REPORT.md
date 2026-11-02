# Task KU Report — `sqrt.s` Operand Fix (`C315`)

## Build Summary
- **Build status**: **OK** (`exit=0`)
- **Executable paths**:
  - `C:\ApeEscape3_Recomp\build\PS2Recomp\ps2xRuntime\ps2EntryRunner.exe` (`139,642,368` bytes, `2026-10-30 03:02:37`)
  - `C:\ApeEscape3_Recomp\build\PS2Recomp\ps2xRuntime\ps2EntryRunner_msvc.exe` (`139,642,368` bytes, `2026-10-30 03:02:37`)
- **Number of files compiled**:
  - **103 modified `recomp_source/*.cpp` files** (136 `// C315` sites) across **77 Unity translation units** (`490.9s` with `cl.exe /MP8`)
  - Cleanly re-archived `build\recomp_source.lib` (`502,459,880` bytes) from all 730 Unity `.obj` files (`6.9s`)
  - Linked `ps2EntryRunner.exe` via `tools\build.bat` (`70.7s`, total `568.5s`)
- **Git commits on branch `task/KU`**:
  - `PS2Recomp` (`task/KU`): `40fd9a4` (`Task KU: sqrt.s operand fix (C315)` — `ps2xRecomp/src/lib/fpu_translator.cpp`)
  - Root repo (`task/KU`): `5883565` (`Task KU: sqrt.s operand fix (C315)` — `tools/fix_sqrt_s.py` + `PS2Recomp`)

## User Run Command (`ku`)
```powershell
$env:PS2X_GS_ASYNC="1"; $env:PS2X_VIF1_ASYNC="1"; $env:PS2X_GS_VULKAN="1"
.\build\PS2Recomp\ps2xRuntime\ps2EntryRunner_msvc.exe *> ku.log
```
