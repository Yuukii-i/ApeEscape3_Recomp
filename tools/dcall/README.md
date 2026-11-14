# PERF-CG2: Direct Calls for Static JAL Targets (Staged)

This directory stages the direct-call optimization (`PS2_DCALL`) without modifying the active build tree.

## Files
- `ps2_dcall.h`: Inline `ps2Dcall` / `PS2_DCALL(target, fallthrough)` fast path. Calls through `g_ps2RecompiledFunctionTable[target >> 2]` (preserving runtime probe/override wrappers), batches cycle accounting (`g_acctPending += 8`, flushing out-of-line at `>= 256`), resets `vu0_vf[0]`, saves/restores `g_currentExecutingFunction`, and delegates non-fallthrough returns/chaining to `ps2DcallContinue`.
- `ps2_dcall.cpp`: Startup `g_ps2DcallSlowMode` flag, `ps2DcallFlushAcct`, and `ps2DcallContinue`.
- `direct_calls.py`: Post-processor over `recomp_source/*.cpp` rewriting exact 3-line `GuestBranchKind::DirectCall` + `"JAL"` + `{ return; }` sites to `PS2_DCALL(target, fallthrough)` when `target` has a `sub_<TARGET>_0x*.cpp` file and is not special-cased (`0x001037E8`, `0x0031A1B4`, `0x0031A240`, `0x00408000..0x00413000`).

## Diagnostics Decision (Slow Mode Only)
- `EeProfilerScope`: Only measures outermost dispatch rdtsc ticks (`s_depth == 0`); every `JAL` inside guest code is already nested inside an outer `dispatchGuestBranch`, so omitting it in `PS2_DCALL` does not affect `[prof]` timing.
- `pushDispatchPc` / `g_lastDistinctFns`: Used only for crash/stall diagnostics (`dumpEeDiagnostics`, `onBlStallDiag`), not guest correctness. Kept in slow mode (`PS2X_DCALL=0`).

## Apply Steps (after current build finishes)
1. Copy `tools/dcall/ps2_dcall.h` to `PS2Recomp/ps2xRuntime/include/ps2_dcall.h`.
2. Copy `tools/dcall/ps2_dcall.cpp` to `PS2Recomp/ps2xRuntime/src/lib/ps2_dcall.cpp` and add `src/lib/ps2_dcall.cpp` to `PS2Recomp/ps2xRuntime/CMakeLists.txt` (next to `src/lib/ps2_runtime.cpp`).
3. Preview rewrite counts:
   ```
   python tools/dcall/direct_calls.py --dry-run recomp_source
   ```
4. Apply rewrite (idempotent; writes `tools/dcall/direct_calls.log`):
   ```
   python tools/dcall/direct_calls.py recomp_source
   ```
5. Full rebuild (`Release` `/arch:AVX2`).

## Off Switch
- Set `PS2X_DCALL=0` in the environment to route all `PS2_DCALL` sites back through `PS2Runtime::dispatchGuestBranch`.
- Slow mode is also enabled automatically when `PS2X_PROF_COUNTS=1`, `PS2X_DISPATCH_PROBES` is set, `PS2X_PROBE_VU3D=1`, `PS2X_ACCT_BATCH=0`, or `PS2X_DISPATCH_LEAN=0`.

## Verification Plan
1. Run `route_bench` and compare EE ms/frame and vsync/s against baseline (and against `PS2X_DCALL=0`).
2. Verify the file-load sequence in logs is identical between `PS2X_DCALL=0` and default (`PS2X_DCALL=1`).
3. Capture and inspect a gameplay/title screenshot to confirm identical rendering.
