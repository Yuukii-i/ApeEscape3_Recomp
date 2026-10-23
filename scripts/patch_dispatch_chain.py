import sys

with open('PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp', 'r') as f:
    content = f.read()

target = '''    RecompiledFunction targetFn = lookupFunction(targetPc);
    const uint32_t entryPc = ctx->pc;
    targetFn(rdram, ctx, this);

    if (isStopRequested() || ctx->pc == 0u)
    {
        return false;
    }

    if (ctx->pc == entryPc)
    {
        ctx->pc = fallthroughPc;
    }

    return ctx->pc == fallthroughPc;'''

replacement = '''    RecompiledFunction targetFn = lookupFunction(targetPc);
    const uint32_t entryPc = ctx->pc;
    targetFn(rdram, ctx, this);

    if (ctx->pc == entryPc)
    {
        ctx->pc = fallthroughPc;
    }

    // If the target function fell through or tail-jumped to another function,
    // continue dispatching chained functions until it returns to fallthroughPc.
    uint32_t dispatchChainSteps = 0;
    while (ctx->pc != fallthroughPc && !isStopRequested() && ctx->pc != 0u && hasFunction(ctx->pc))
    {
        if (++dispatchChainSteps > 1000)
        {
            // Safety bound against runaway dispatch chains
            break;
        }
        if (m_eeScheduler && m_eeScheduler->checkpointDue(EeScheduler::kGuestDispatchCycles))
        {
            return false;
        }
        const uint32_t nextPc = ctx->pc;
        RecompiledFunction nextFn = lookupFunction(nextPc);
        nextFn(rdram, ctx, this);
        if (ctx->pc == nextPc)
        {
            break;
        }
    }

    if (isStopRequested() || ctx->pc == 0u)
    {
        return false;
    }

    return ctx->pc == fallthroughPc;'''

if target not in content:
    print("ERROR: Target not found")
    sys.exit(1)

content = content.replace(target, replacement, 1)
with open('PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp', 'w', newline='\r\n') as f:
    f.write(content)
print("SUCCESS: Patched dispatchGuestBranch with chained dispatch")
