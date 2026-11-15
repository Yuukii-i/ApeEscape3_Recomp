#pragma once
// PERF-CG2: Direct-call fast path for static JAL targets.
//
// Diagnostics kept in slow mode only (not required for guest correctness):
//   - EeProfilerScope: outermost dispatch rdtsc timing for [prof] log line
//     (every JAL inside a guest function is already nested inside an outer dispatchGuestBranch).
//   - pushDispatchPc / g_dispatchHistory: ring buffer used only by dumpEeDiagnostics() on crash/stall.
//   - g_lastDistinctFns: 5-entry MRU used only by stall diagnostics (onBlStallDiag / probe_getNewestDistinctFn).
// Set PS2X_DCALL=0 (or enable any dispatch probe / PS2X_PROF_COUNTS=1) to route all calls through dispatchGuestBranch.

#include <cstdint>
#include <xmmintrin.h>
#include "ps2_runtime.h"

extern const bool g_ps2DcallSlowMode;
extern thread_local uint32_t g_acctPending;
extern thread_local uint32_t g_currentExecutingFunction;

constexpr uint32_t kPs2DcallDispatchCycles = 8u; // == EeScheduler::kGuestDispatchCycles

void ps2DcallFlushAcct(PS2Runtime *runtime);
bool ps2DcallContinue(uint8_t *rdram,
                      R5900Context *ctx,
                      PS2Runtime *runtime,
                      uint32_t target,
                      uint32_t fallthrough);

inline bool ps2Dcall(uint8_t *rdram,
                     R5900Context *ctx,
                     PS2Runtime *runtime,
                     uint32_t target,
                     uint32_t fallthrough)
{
    if (g_ps2DcallSlowMode)
    {
        return runtime->dispatchGuestBranch(
            rdram, ctx, target, fallthrough - 8u, fallthrough,
            PS2Runtime::GuestBranchKind::DirectCall, "JAL");
    }

    const uint32_t off = target - g_ps2RecompiledFunctionTableBase;
    const uint32_t slot = off >> 2;
    if (target < g_ps2RecompiledFunctionTableBase ||
        target >= g_ps2RecompiledFunctionTableEnd ||
        slot >= g_ps2RecompiledFunctionTableSlotCount)
    {
        return runtime->dispatchGuestBranch(
            rdram, ctx, target, fallthrough - 8u, fallthrough,
            PS2Runtime::GuestBranchKind::DirectCall, "JAL");
    }

    const PS2Runtime::RecompiledFunction fn = g_ps2RecompiledFunctionTable[slot];
    if (fn == nullptr)
    {
        return runtime->dispatchGuestBranch(
            rdram, ctx, target, fallthrough - 8u, fallthrough,
            PS2Runtime::GuestBranchKind::DirectCall, "JAL");
    }

    g_acctPending += kPs2DcallDispatchCycles;
    if (g_acctPending >= 256u)
    {
        ps2DcallFlushAcct(runtime);
    }

    if (ctx)
    {
        ctx->vu0_vf[0] = _mm_set_ps(1.0f, 0.0f, 0.0f, 0.0f);
    }

    const uint32_t prevExecutingFn = g_currentExecutingFunction;
    g_currentExecutingFunction = target;

    fn(rdram, ctx, runtime);

    g_currentExecutingFunction = prevExecutingFn;

    if (ctx->pc == target)
    {
        ctx->pc = fallthrough;
    }
    if (ctx->pc == fallthrough)
    {
        return true;
    }

    return ps2DcallContinue(rdram, ctx, runtime, target, fallthrough);
}

#define PS2_DCALL(target, fallthrough) ps2Dcall(rdram, ctx, runtime, (target), (fallthrough))
