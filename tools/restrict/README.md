# PERF-CG4: `__restrict` Locals for `rdram` and `ctx` (Staged)

This directory stages the `PERF-CG4` post-processor (`restrict_ctx.py`) without modifying `recomp_source` or the runtime.

## What It Does
For every generated function definition in `recomp_source/*.cpp` with signature:
```cpp
void <fn>(uint8_t* rdram, R5900Context* ctx, PS2Runtime *runtime) {
```
`restrict_ctx.py` renames the parameters to `rdram_in` / `ctx_in` and inserts `__restrict`-qualified locals as the first statements of the function body:
```cpp
void <fn>(uint8_t* rdram_in, R5900Context* ctx_in, PS2Runtime *runtime) {
    uint8_t* __restrict rdram = rdram_in; R5900Context* __restrict ctx = ctx_in; // PERF-CG4
```
Function declarations in `recomp_source/ps2_recompiled_functions.h` and function pointer types in the runtime dispatch table are unchanged.

Functions whose bodies assign to or take the address of `ctx` or `rdram` (`ctx =`, `rdram =`, `&ctx`, `&rdram`) are skipped and reported. The script is idempotent via the `// PERF-CG4` marker.

## Why It Is Safe
- `rdram` (the 32 MB EE RAM buffer) and `*ctx` (`R5900Context`, a static/heap object) never overlap in memory.
- Without `__restrict`, MSVC must conservatively assume that any fast-path guest store through `rdram` could alias `ctx->r[]`, forcing it to reload and re-store GPRs around every guest store.
- With `__restrict` on `rdram` and `ctx`, the compiler can keep guest GPRs in host registers across guest memory stores.
- Any call inside the function body that passes `ctx` (such as `runtime->dispatchGuestBranch(rdram, ctx, ...)` or syscalls/stubs) still forces memory synchronization for `ctx` at the call boundary because `ctx` escapes to the callee.

## How to Apply
1. Commit any pending changes in `recomp_source` first so the transform can be cleanly reverted:
   ```powershell
   git -C recomp_source add -A && git -C recomp_source commit -m "Pre-CG4 snapshot"
   ```
2. Preview counts with `--dry-run`:
   ```powershell
   python tools/restrict/restrict_ctx.py recomp_source --dry-run
   ```
3. Apply the transform (writes `tools/restrict/restrict_ctx.log`):
   ```powershell
   python tools/restrict/restrict_ctx.py recomp_source
   ```
4. Perform a full rebuild (`Release` `/arch:AVX2`).

## How to Undo
Revert the commit in `recomp_source`:
```powershell
git -C recomp_source revert HEAD
```
(Or `git -C recomp_source checkout -- .` if not yet committed.)
