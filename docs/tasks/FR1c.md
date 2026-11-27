# Task FR1c: trace the replay dispatch loop (cpp only)
Budget: "[call N/12]", stop at 12. Edit ONLY ps2_runtime.cpp (ps2xFnReplay). No headers. DO NOT BUILD/RUN/COMMIT. Mark `// PROBE-FR1c`.
Why: recompiled code calls through PS2_DCALL(target, retPc) and may RETURN EARLY to the dispatcher (`if (!PS2_DCALL(...)) return;`) with ctx->pc = target; the dispatcher then runs the target and resumes the caller at retPc. Our replay of fn 0x340744 stops with pc=0x003bfbd0 sp=0x01ffed50 and the caller never resumes, so later stores are missing.
Do:
1. In the replay dispatch loop log EVERY step (first 300, then nothing but the final one): `[fnreplay] step %u pc=0x%08x sp=0x%08x ra=0x%08x` printed BEFORE calling the function at ctx->pc, and after the call `[fnreplay]   -> pc=0x%08x sp=0x%08x`.
2. When the loop ends because there is no generated function at ctx->pc (or pc unchanged), log why, plus the 8 most recent dispatch pcs (use the existing dispatch history: pushDispatchPc ring / g_lastDistinctFns if accessible) and, if a resume-at-address mechanism exists in the normal dispatcher (how does it resume a function at the retPc given to PS2_DCALL? look at ps2_dcall.cpp and the dispatcher code ~L5010-5100: e.g. lookup by `ctx->pc` inside a function range, a 'resume entry' table, generatedFunctionTableSlot for fallthrough entries), IMPLEMENT the same resume in the replay loop so the caller continues after the callee returns.
3. Report in <=6 lines how PS2_DCALL decline + resume works in the real dispatcher and what you implemented.
Acceptance: compiles; no header edits.
