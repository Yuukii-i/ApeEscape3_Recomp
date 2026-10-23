import sys

with open('PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp', 'r') as f:
    content = f.read()

target = '''    if (!isCall)
    {
        if (!hasFunction(targetPc))
        {
            reportMissingFunction(rdram, ctx, targetPc, sourcePc, kind, debugName);
        }

        ctx->pc = targetPc;
        return false;
    }'''

replacement = '''    if (!isCall)
    {
        if ((kind == GuestBranchKind::DirectJump || kind == GuestBranchKind::IndirectJump) && hasFunction(targetPc))
        {
            RecompiledFunction targetFn = lookupFunction(targetPc);
            ctx->pc = targetPc;
            targetFn(rdram, ctx, this);
            return false;
        }

        if (!hasFunction(targetPc))
        {
            reportMissingFunction(rdram, ctx, targetPc, sourcePc, kind, debugName);
        }

        ctx->pc = targetPc;
        return false;
    }'''

if target not in content:
    print("ERROR: Target not found")
    sys.exit(1)

content = content.replace(target, replacement, 1)
with open('PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp', 'w', newline='\r\n') as f:
    f.write(content)
print("SUCCESS: Patched dispatchGuestBranch")
