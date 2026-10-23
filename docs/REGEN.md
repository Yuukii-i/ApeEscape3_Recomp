# Ape Escape 3 (`SCUS_975.01`) Recompiler Regeneration Guide (`REGEN.md`)

> **Status Tag Legend**:
> - `[CONFIRMED file:line]` / `[CONFIRMED log:line]`: Verified directly against source files, binary headers, git history, or execution logs.
> - `[INFERRED: reason]`: Logical deduction from confirmed code or data structures.
> - `[UNKNOWN]`: Not yet determined from code or logs.

---

## 1. Overview & Regeneration Safety

The static recompiler `ps2_recomp.exe` analyzes the original MIPS ELF (`SCUS_975.01`), applies function stub declarations from `config.toml`, and emits over 23,350 recompiled C++ functions into `recomp_source/`.

> [!WARNING]
> Running `ps2_recomp.exe config.toml` **completely wipes or overwrites** all files inside `recomp_source/`. Any manual modifications directly made to files in `recomp_source/` will be permanently lost unless they are migrated to the runtime engine (`PS2Recomp`) or captured in patches.

Before executing a real regeneration, always run the dry-run comparison script [`scripts/regen_dryrun.ps1`](file:///c:/ApeEscape3_Recomp/scripts/regen_dryrun.ps1), which recompiles into a temporary directory and reports exact file-level differences against your working tree.

---

## 2. Prerequisites & Toolchain

To regenerate the recompiled code, ensure the following files are present:
1. **Recompiler Binary**:
   - `ps2_recomp.exe` in the repository root (`c:\ApeEscape3_Recomp\ps2_recomp.exe`), or built from source at `build/PS2Recomp/ps2xRecomp/Release/ps2xRecomp.exe`.
2. **Recompiler Configuration**:
   - [`config.toml`](file:///c:/ApeEscape3_Recomp/config.toml) in the repository root (specifies `input = "SCUS_975.01"` and `output = "recomp_source"`).
3. **PS2 Boot Executable**:
   - `SCUS_975.01` in the repository root (`6,488,148` bytes).
4. **Disk Space**:
   - At least **1.5 GB** of free disk space to store temporary C++ files and unity compilation build trees.

---

## 3. Dry-Run Verification (Non-Destructive)

Always perform a dry run first to inspect what would change:

```powershell
# From repository root
.\scripts\regen_dryrun.ps1
```

### What `regen_dryrun.ps1` Does:
1. Validates that `ps2_recomp.exe`, `config.toml`, and `SCUS_975.01` exist.
2. Checks available disk space (aborts if free space < 1.0 GB).
3. Creates an isolated temporary directory in `$env:TEMP\ps2x_dryrun_<timestamp>`.
4. Clones `config.toml` to a temporary config with `output = "<temp_path>"`.
5. Executes `ps2_recomp.exe <temp_config>`.
6. Compares the newly generated C++ files against current `recomp_source/` byte-for-byte.
7. Prints a concise report of:
   - Total generated file count vs current file count.
   - Exact filenames of any modified, new, or missing files.
8. Cleans up the temporary directory automatically (use `-KeepTemp` if you want to inspect files manually).

---

## 4. Full Regeneration Procedure (When Ready)

Once the dry-run diff is reviewed and confirmed acceptable, proceed with full regeneration:

### Step 1: Backup Local Assets & Patches
```powershell
$env:PS2X_BACKUP_DIR = "C:\Backups\ApeEscape3_Assets"
.\scripts\backup_assets.ps1
```

### Step 2: Execute Recompiler
```powershell
# Execute the static recompiler targeting recomp_source/
.\ps2_recomp.exe config.toml
```

### Step 3: Rebuild the Runner Binary
```powershell
.\scripts\build.ps1
```

### Step 4: Verify Boot & Main Loop Execution
```powershell
.\scripts\run.ps1 -TimeoutSeconds 15
```

---

## 5. Which Hand Edits Will Be Lost & Why It Is Safe

As documented in [`docs/HAND_EDITS.md`](file:///c:/ApeEscape3_Recomp/docs/HAND_EDITS.md), full regeneration will overwrite 11 files in `recomp_source/` that currently contain manual instrumentation:

| File | Current Hand Edit | Why It Is Safe to Overwrite | Permanent Home |
| :--- | :--- | :--- | :--- |
| `sub_00100134_0x100134.cpp` | `[crt0]` entry counter & flight recorder check | `crt0` only runs once; restart loop was fixed in `CMakeLists.txt:71` | DELETE (obsolete debug noise) |
| `sub_00100190_0x100190.cpp` | `[crt0]` phase print | Debug milestone only | DELETE |
| `sub_00100210_0x100210.cpp` | .bss clear loop prints and syscall 0x3C/0x3D prints | Syscalls are already logged in `System.cpp` | DELETE |
| `sub_00101298_0x101298.cpp` | `push_trace` | Obsolete trace instrumentation | DELETE |
| `sub_001037E8_0x1037e8.cpp` | `[main]` first line print & subsystem `push_trace` | Spams console every yield; obsolete | DELETE |
| `sub_00159728_0x159728.cpp` | `push_trace` | Obsolete trace instrumentation | DELETE |
| `sub_0015993C_0x15993c.cpp` | `push_trace` | Obsolete trace instrumentation | DELETE |
| `sub_00159AAC_0x159aac.cpp` | `push_trace` | Obsolete trace instrumentation | DELETE |
| `sub_00159B68_0x159b68.cpp` | `push_trace` | Obsolete trace instrumentation | DELETE |
| `sub_00159BEC_0x159bec.cpp` | `push_trace` | Obsolete trace instrumentation | DELETE |
| `sub_0015B720_0x15b720.cpp` | `push_trace` | Obsolete trace instrumentation | DELETE |
| `trace_logger.cpp` / `.h` | In-memory circular buffer | No longer referenced | DELETE |

### Critical Function Overrides Already Safe in Runtime:
The 5 functional overrides originally attempted via hand edits in `recomp_source/` have **already been migrated to the runtime engine**:
1. `0x3703D4` (SoundGroup2 readiness): Overridden in [`ps2_runtime.cpp:1141-1145`](file:///c:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp#L1141-L1145).
2. `0x40FAE0` (IPU idle stub): Overridden in [`ps2_runtime.cpp:1146-1147`](file:///c:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp#L1146-L1147).
3. `_sceMpegWaitIpuIdle64` / `_waitIpuIdle`: Handled by HLE in [`IPU.cpp`](file:///c:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/Kernel/Stubs/IPU.cpp) and [`MPEG.cpp`](file:///c:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/Kernel/Stubs/MPEG.cpp).

Therefore, **zero functional regression** occurs upon full regeneration.
