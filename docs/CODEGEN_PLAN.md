# Codegen speed plan (EE recompiler output) - draft for review

## Context (facts, with evidence)
- Project: static recomp of Ape Escape 3 (PS2, SCUS_975.01). The PS2 EE (MIPS R5900, 294 MHz) code is translated by
  `PS2Recomp/ps2xRecomp` into ~23k C++ files in `recomp_source/` (one function per file, MSVC /O2 /arch:AVX2, ~40 min full build).
- Goal: 60 fps. Now: ~23 vsync/s at the title menu / in gameplay (Vulkan GS, async GS + VU1 workers).
- The EE thread is the limiter: ~78% busy, ~33 ms per vsync. Host sampler shows a flat tail of guest code (no function > ~4%);
  identified runtime overheads (present conversion ~7%, VU0 inline ~5%, misc ~4%) are not enough for 60 fps.
- PCSX2 (real game) at the menu: EE ~85-90% busy per frame (vsync busy-wait only ~12% of samples). So the real EE does the same
  work in ~14 ms; our generated code is ~2.3x slower than a 294 MHz R5900 on a 4+ GHz Ryzen. Lever = shape of the generated code.
- Already done (Task IH, headers): store-trace probes compiled out, RAM fast path (`addr < 32MB` skips the special-address test),
  GPR lane-0 read/write as scalar 32/64-bit moves. Gain ~7%.

## What one guest instruction costs today (generated code, e.g. sub_00101618, sub_003D5D40)
```
ctx->pc = 0x10161cu;                                          // EVERY instruction (function_emitter.cpp:203)
WRITE64(ADD32(GPR_U32(ctx, 29), 0), GPR_U64(ctx, 16));        // regs live in ctx->r[32] (__m128i) in memory
SET_GPR_S32(ctx, 14, (int32_t)READ32(ADD32(GPR_U32(ctx, 4), 0)));
// JAL: ctx->pc/in_delay_slot/branch_pc stores, then
if (!runtime->dispatchGuestBranch(rdram, ctx, 0x43FBA0u, 0x101630u, 0x101638u, DirectCall, "JAL")) return;
```
- READ/WRITE macros: `isSpecialAddress(addr) ? runtime->LoadN/StoreN(...) : fast RAM access`. The slow path may call
  `SignalException` (reads ctx->pc for EPC) or touch MMIO.
- Every register operand is a load from / store to `ctx->r[n]`; MSVC cannot keep values in host registers because opaque
  calls (slow paths, dispatch) can read/write ctx.
- Every call goes through `PS2Runtime::dispatchGuestBranch` (ps2_runtime.cpp ~3893): profiler scope, probes, vf0 reset,
  accountCycles (EE timers + IOP step), hasFunction + lookupFunction table lookups, fallthrough/chain loop.
- Backward branches: `ctx->pc = target; if (runtime->eeCheckpointDue()) return; goto label;` (preemption point; the function's
  entry `switch (ctx->pc)` resumes at labels).

## Proposed changes (phased; each phase = one regen + full build + verification)
### Phase 1 - drop per-instruction `ctx->pc` stores (low risk)
- Emit `ctx->pc = X` only where something can observe it: branches/calls/returns (already emitted by control_flow_emitter),
  syscalls/COP0/trap and overflow-trapping ops (ADD/ADDI/SUB/DADD/DADDI/DSUB, TEQ/TGE/..., BREAK), VU macro-mode ops that
  call the runtime (VCALLMS etc.), cache/sync, and anything not on a whitelist of pure ALU/FPU/MMI ops.
- Loads/stores: new macro variants `READ32_PC(addr, pc)` / `WRITE32_PC(addr, val, pc)` that set `ctx->pc = pc` only inside the
  slow (special-address) branch, so the RAM fast path has no pc store.
- Default-safe rule: an instruction class not on the whitelist keeps today's `ctx->pc` store.
- Expected: removes ~1 store per instruction; estimate 5-15% EE (unmeasured).

### Phase 2 - direct calls to known functions (medium risk)
- For JAL/JALR with a statically known target that has a recompiled function, emit a call through a small inline helper
  (header) that keeps the required semantics: accountCycles(kGuestDispatchCycles), g_currentExecutingFunction, call the
  function pointer directly (no lookup), the "ctx->pc == entry -> fallthrough" rule and the chain loop, checkpoint/stop checks.
  Everything else (probes, profiler scope, missing-function handling) stays in dispatchGuestBranch for indirect/unknown targets.
- Expected: depends on call frequency; removes table lookups + ~30-60 host instructions per call.

### Phase 3 - cache guest registers in C++ locals within a basic block (high risk, biggest potential)
- At block start load the used GPRs into locals; operate on locals; write back dirty ones before any slow path, runtime call,
  branch, label, delay slot, or block end. Lets MSVC keep them in host registers.
- Needs exact flush points; slow paths must flush before calling the runtime and reload after (or flush only dirty regs).

### Phase 4 (optional) - static RAM proof for $sp-relative accesses
- If the stack is in RAM (AE3: sp ~0x01FFFxxx), sp-based loads/stores can use the fast path without the special-address test.
  Needs a runtime guard (debug assert / one check per function entry) because some PS2 games put stacks in scratchpad.

## Risks
- recomp_source is NOT in git; it carries hand edits (recomp_hand_edits.patch, 18 files, ~190 added lines) and
  `// PROBE-<task>` lines. Regeneration overwrites them. Must snapshot first and re-apply.
- Unknown hidden readers of ctx->pc inside runtime slow paths (61 uses in ps2_runtime.cpp, more in Kernel stubs).
- Preemption/resume: any place that returns to the scheduler must have an exact ctx->pc and a resume label.
- Exceptions/EPC correctness (address errors, overflow traps) - rare in this game but must stay exact.
- MSVC compile memory (C1002 seen with __forceinline) - Phase 3 grows function bodies.

## Validation per phase
1. Before any change: regenerate with the CURRENT generator into a temp dir, diff vs recomp_source -> exact list of hand edits.
2. ps2xTest (code_generator_tests etc.) updated + run (today it is built but never run).
3. Determinism check: compare RAM dumps (existing PROBE-FQ ram_ours_N.bin, gated by PS2X_DISPATCH_PROBES) old vs new build
   at the same draw counts; plus title -> gameplay visual run by the user.
4. Speed: fixed benchmark = title menu, vsync/s median + EE ms per vsync vs log jl (23 vsync/s, ~33 ms).

## Open questions for reviewers
- Is the "keep pc only on non-whitelisted ops + slow paths" rule sufficient, or are there other ctx->pc readers to expect
  (interrupt delivery inside MMIO stores, thread switches inside syscalls)?
- Phase order: is Phase 3 (register caching) worth doing before Phase 2, given the flat profile?
- Any cheaper lever we are missing (compiler flags such as /Ob3, PGO on the generated code, unity builds, LTCG in parts)?

## Revised plan after review (docs/OPINIONS.md: GPT OSS, Claude Opus 5.5, Gemini 4 argon)
Verified facts added after review (2026-10-29):
- Release flags are only `/O2 /Ob2` (build/CMakeCache.txt): NO /arch:AVX2, NO /fp:fast for recomp_source or the runtime.
  /guard:cf and /Qspectre are not set (good).
- `eeCheckpointDue()` on every backward branch is an out-of-line call into EeScheduler::checkpointDue
  (EeScheduler.cpp:519): range checks + a 0x3D7000-0x3E5000 throttle hack + accountCycles (EE timers + IOP step) + atomics.
  So every guest loop iteration and every call steps the IOP. This matches Opus' "per-event, not per-instruction" estimate.
- Scratchpad (0x70000000) and the uncached RAM mirror take the slow path (runtime->LoadN/StoreN call). The game DMAs
  from SPR (fs/ft probes), so SPR is in hot use.

Order:
0a. MEASURE (.cpp only, no regen): per-vsync counters for dispatchGuestBranch calls, eeCheckpointDue calls (+ true),
    slow-path loads/stores by region (SPR / mirror / kseg / MMIO), time in accountCycles/IOP step. Decide from numbers.
0b. Infra: put recomp_source in its own git repo; move the 18 hand-edited functions into an override dir the generator
    skips; PROBE lines become a generator option. Unity builds (~150 functions per TU) to cut the 40-min build.
1.  Cheap per-event fixes (driven by 0a): inline fast checkpoint test; SPR + mirror inline fast paths; lean dispatcher
    (flat table, no probes/profiler); /arch:AVX2 experiment.
2.  Phase 2 direct calls (tiny call site, outlined post-call mismatch handler).
3.  Phase 1 pc stores, with outlined noinline slow helpers taking pc as an immediate.
4.  Phase 3 register caching at FUNCTION scope (load at entry before the resume switch; flush at calls/returns/
    checkpoints; flush+reload only inside cold slow paths), uint64_t locals; try __restrict on a few hot functions first.
Dropped: Phase 4 ($sp proof) - saving ~0 after the addr<32MB compare.
Validation additions: baseline determinism (same build twice, RAM dumps) before using RAM diffs; shadow-pc assert build.
