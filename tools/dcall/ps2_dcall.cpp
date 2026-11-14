// PERF-CG2: Out-of-line helpers and startup configuration for PS2_DCALL.

#include "ps2_dcall.h"
#include "runtime/ee_scheduler.h"

#include <cstdlib>
#include <cstring>

static_assert(kPs2DcallDispatchCycles == EeScheduler::kGuestDispatchCycles,
              "kPs2DcallDispatchCycles must match EeScheduler::kGuestDispatchCycles");

extern const bool g_profCounts;

extern const bool g_ps2DcallSlowMode = []() {
    const char *dcall = std::getenv("PS2X_DCALL");
    if (dcall && dcall[0] == '0')
    {
        return true;
    }
    if (g_profCounts)
    {
        return true;
    }
    if (std::getenv("PS2X_DISPATCH_PROBES") != nullptr)
    {
        return true;
    }
    const char *vu3d = std::getenv("PS2X_PROBE_VU3D");
    if (vu3d && std::strcmp(vu3d, "1") == 0)
    {
        return true;
    }
    const char *acctBatch = std::getenv("PS2X_ACCT_BATCH");
    if (acctBatch && acctBatch[0] == '0')
    {
        return true;
    }
    const char *dispatchLean = std::getenv("PS2X_DISPATCH_LEAN");
    if (dispatchLean && dispatchLean[0] == '0')
    {
        return true;
    }
    return false;
}();

void ps2DcallFlushAcct(PS2Runtime *runtime)
{
    const uint32_t p = g_acctPending;
    g_acctPending = 0;
    runtime->eeScheduler().accountCycles(p);
}

bool ps2DcallContinue(uint8_t *rdram,
                      R5900Context *ctx,
                      PS2Runtime *runtime,
                      uint32_t target,
                      uint32_t fallthrough)
{
    (void)target;
    uint32_t chainSteps = 0;
    while (ctx->pc != fallthrough && !runtime->isStopRequested() && ctx->pc != 0u)
    {
        const uint32_t nextPc = ctx->pc;
        if ((nextPc & 3u) != 0u ||
            nextPc < g_ps2RecompiledFunctionTableBase ||
            nextPc >= g_ps2RecompiledFunctionTableEnd)
        {
            break;
        }
        const uint32_t slot = (nextPc - g_ps2RecompiledFunctionTableBase) >> 2;
        if (slot >= g_ps2RecompiledFunctionTableSlotCount ||
            g_ps2RecompiledFunctionTable[slot] == nullptr)
        {
            break;
        }
        if (++chainSteps > 1000u)
        {
            break;
        }
        g_acctPending += kPs2DcallDispatchCycles;
        if (g_acctPending >= 256u)
        {
            ps2DcallFlushAcct(runtime);
        }
        g_ps2RecompiledFunctionTable[slot](rdram, ctx, runtime);
        if (ctx->pc == nextPc)
        {
            break;
        }
    }

    if (runtime->isStopRequested() || ctx->pc == 0u)
    {
        return false;
    }
    return ctx->pc == fallthrough;
}
