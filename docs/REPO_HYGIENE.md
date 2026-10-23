# Ape Escape 3 Recompilation — Repository Hygiene & Git Architecture Report

> **Status Tag Legend**:
> - `[CONFIRMED file:line]` / `[CONFIRMED log:line]`: Verified directly against source files, binary headers, git history, or execution logs.
> - `[INFERRED: reason]`: Logical deduction from confirmed code or data structures.
> - `[UNKNOWN]`: Not yet determined from code or logs.

---

## 1. Executive Summary

This document audits the repository health, git architecture, object storage, and cleanliness of both the outer project repository (`ApeEscape3_Recomp`) and the nested engine repository (`PS2Recomp`).

Key findings:
1. **Clean Commit History**: Neither the outer repository nor the nested `PS2Recomp` repository has **ever** had proprietary game assets, ISO images, ELF binaries, or `.irx` modules committed.
2. **Submodule Disconnect Risk**: The outer repository tracks `PS2Recomp` via a bare gitlink (`160000 commit eb8688b`) with **no `.gitmodules` file**. Furthermore, the local `PS2Recomp` checkout is detached/ahead at commit `7d7df64` (2 commits ahead of the gitlink) and has **6 uncommitted modified files** in its working tree. Anyone cloning the repository today cannot clone `PS2Recomp` automatically.
3. **Proposed `.gitignore`**: A fully documented `.gitignore.proposed` protects against accidental check-ins of huge generated sources (`recomp_source/`), logs, frame dumps, build trees, and copyrighted game files.

---

## 2. Nested Repository (`PS2Recomp`) Status & Git State

### 2.1 Current State
- **Path**: `c:\ApeEscape3_Recomp\PS2Recomp`
- **Remote**: `origin https://github.com/Yuukii-i/PS2Recomp.git` `[CONFIRMED git -C PS2Recomp remote -v]`.
- **Branch**: `main`
- **Upstream Base**: `eb8688b` (`Emulate PS2 float semantics for EE FPU results and DIV.S/RSQRT.S (#272)`) `[CONFIRMED git -C PS2Recomp log]`.
- **Local Commits Ahead of Base**:
  1. `852bd50`: `Checkpoint runtime changes before resolving missing function 0x4133a0`
  2. `7d7df64`: `WIP: Ape Escape 3 runtime HLE bindings and translator fixes`
- **Outer Repo Gitlink Pointer**:
  - `git ls-tree HEAD` in the outer repo shows `160000 commit eb8688b2fd191129f103a39543002c005b33409c PS2Recomp`.
  - The outer repo's recorded submodule commit points to upstream `eb8688b`, **not** to `7d7df64`!
- **Uncommitted Modified Files in `PS2Recomp/` (6 files)**:
  - `ps2xRuntime/src/lib/Kernel/Stubs/GS.cpp` (DMAC handler drain in `sceGsSyncPath`)
  - `ps2xRuntime/src/lib/Kernel/Stubs/IPU.cpp` (Cleaned cross-game residue)
  - `ps2xRuntime/src/lib/Kernel/Stubs/MPEG.cpp` (Cleaned cross-game residue)
  - `ps2xRuntime/src/lib/ps2_memory.cpp` (`VIF1_MARK` 0x10003C30 MMIO handlers)
  - `ps2xRuntime/src/lib/ps2_runtime.cpp` (INTC cause 5 handling and frame dump diagnostic)
  - `ps2xRuntime/src/lib/ps2_vif1_interpreter.cpp` (`VIF1_MARK == 0x2000` INTC trigger)
- **Critical Flaw**: **No `.gitmodules` file exists in the outer repository**. Running `git clone --recurse-submodules` on a new machine fails to clone `PS2Recomp` because Git does not know what remote URL is associated with the `PS2Recomp` directory.

---

## 3. Options for Nested `PS2Recomp` Repository Architecture

### Option 1: Fork + Formal Git Submodule (RECOMMENDED)
- **Description**:
  1. Commit the 6 working-tree changes in `PS2Recomp` to a feature branch (e.g. `ae3-support`) on the `Yuukii-i/PS2Recomp` fork.
  2. Create a `.gitmodules` file in the root repository mapping path `PS2Recomp` to `https://github.com/Yuukii-i/PS2Recomp.git` (or an organization fork).
  3. Update the gitlink in the outer repository from `eb8688b` to the latest commit `7d7df64` (plus the new working-tree commit).
- **Pros**:
  - Full reproducibility: `git clone --recurse-submodules` checks out exact matching commits on any machine.
  - Upstream synchronization: Easy to pull future upstream improvements (`git -C PS2Recomp pull upstream main`) or submit PRs back to upstream `ran-j/PS2Recomp`.
  - Separation of concerns: Runtime engine code remains isolated from game-specific wrapper code.
- **Cons**:
  - Developers must remember to commit and push changes in `PS2Recomp` before committing the gitlink in the outer repo.

### Option 2: Monorepo Flattening
- **Description**:
  - Remove the `.git` folder from `PS2Recomp/` and commit all `PS2Recomp` source files directly into the outer repository.
- **Pros**:
  - Single commit history: Changes touching both recompiled stubs and runtime engine can be committed atomically.
  - Eliminates all submodule management friction.
- **Cons**:
  - Completely severs upstream git history and makes rebasing onto future `PS2Recomp` upstream releases difficult.
  - Inflates outer repo history with third-party engine files and large header tables.

### Option 3: Keep Nested Repository with Documented Scripted Workflow
- **Description**:
  - Keep `PS2Recomp` as an untracked or loosely nested clone, and use a setup script (`scripts/setup_submodule.ps1`) to clone and checkout the required commit.
- **Pros**:
  - Requires zero changes to current git commits.
- **Cons**:
  - Fragile and non-standard. Automated CI/CD pipelines and new developer setups must run custom scripts instead of standard Git commands.

### Recommendation
**Adopt Option 1 (Fork + Formal Git Submodule)**. It conforms to standard open-source recompilation project practices (e.g. Zelda64 Recomp, Jak Project), preserves upstream PR capability, and provides 100% automated cloning via `git clone --recurse-submodules`.

---

## 4. History & Size Scan Findings (Read-Only)

### 4.1 Outer Repository (`ApeEscape3_Recomp`)
- **`git count-objects -v`**:
  ```text
  count: 13
  size: 39 KiB
  in-pack: 0
  packs: 0
  ```
- **Commit History**: 4 commits total (`3b0330b` -> `f30b1aa` -> `366dac8` -> `d7b2ad3`).
- **All Tracked Blobs by Size**:
  1. `221,012 bytes`: `config.toml` (Recompiler stub list)
  2. `7,695 bytes`: `README.md`
  3. `2,864 bytes`: `CMakeLists.txt`
  4. `282 bytes`: `.gitignore`
- **Proprietary Asset Check**:
  - Scanned all commit trees for `SCUS_975.01`, `*.iso`, `*.bin`, `*.irx`.
  - **Result: 0 proprietary assets have ever been committed** `[CONFIRMED]`.

### 4.2 Nested Repository (`PS2Recomp`)
- **`git count-objects -v`**:
  ```text
  count: 44
  size: 191 KiB
  in-pack: 3050
  packs: 1
  size-pack: 6511 KiB (6.36 MiB)
  ```
- **Largest Blobs in History**:
  1. `12,074,936 bytes` (`12.07 MB`): `ps2xAnalyzer/include/ps2recomp/sce_symbol_database_data.h`
  2. `1,995,561 bytes` (`1.99 MB`): `ps2xRuntime/vita/module/libGLESv2.suprx`
  3. `1,325,945 bytes` (`1.32 MB`): `ps2xRuntime/vita/module/libGL.suprx`
  4. `874,708 bytes` (`874 KB`): `ps2xStudio/external/Font/Font_1.ttf`
  5. `335,068 bytes` (`335 KB`): `ps2xStudio/external/Font/Font_2.ttf`
  6. `188,964 bytes` (`188 KB`): `ps2xRuntime/src/lib/ps2_stubs.cpp`
  7. `162,013 bytes` (`162 KB`): `ps2xRuntime/src/lib/ps2_syscalls.cpp`
- **Proprietary Asset Check**:
  - Scanned all 2,000+ commit trees for `SCUS_975.01`, `*.iso`, `*.bin`, `*.irx`, or Ape Escape assets.
  - **Result: 0 proprietary assets have ever been committed** `[CONFIRMED]`.

---

## 5. `.gitignore.proposed` Specification & Justification

The proposed `.gitignore.proposed` protects against all large, generated, transient, and proprietary files:

| Pattern | Category / Justification | Currently Tracked? | Action Required |
| :--- | :--- | :--- | :--- |
| `SCUS_975.01` | Original Sony PS2 boot executable (proprietary copyright) | No | None |
| `*.iso` | Disc images (multi-gigabyte proprietary game discs) | No | None |
| `*.bin` | Extracted disc archives (`DATA.BIN`) | No | None |
| `*.irx` / `tools/iop/*.irx` | Extracted IOP modules (Sony SDK / proprietary) | No | None |
| `recomp_source/` | 23,350+ generated C++ files (250+ MB; fully regenerable) | No | None |
| `build/` | CMake/Ninja build output tree | No | None |
| `logs/` / `*.log` | Runtime diagnostics, execution trace logs | No | None |
| `frames/` / `frame_*.png` | Frame buffer dumps from GS uploads | No | None |
| `tools/*/_out/` | Artifact outputs from IOP disassemblers or extractors | No | None |
| `mc0/` / `mc1/` | Virtual memory card save data | No | None |
| `imgui.ini` | ImGui layout configuration generated by runner | No | None |
| `*.exe` / `*.lib` / `*.pdb` | Compiled binaries in project root | No | None |

> **Audit Confirmation**: No files matching `.gitignore.proposed` are currently tracked in git index. Therefore, **no `git rm --cached` command is required** prior to activation.
