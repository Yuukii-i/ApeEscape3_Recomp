import os

path = r'PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add hook for 0x004369A8 in loadELF
hook_slot = '''
    const uint32_t slot4369a8 = (0x004369A8u - g_ps2RecompiledFunctionTableBase) >> 2;
    static RecompiledFunction s_orig4369a8 = g_ps2RecompiledFunctionTable[slot4369a8];
    replaceFunction(0x004369A8u, [](uint8_t *rdram, R5900Context *ctx, PS2Runtime *runtime) {
        const char *env = std::getenv("PS2X_TRACE_SYNC");
        if (env && std::strcmp(env, "1") == 0)
        {
            ps2xSafeLog("[sync:direct_iWakeupThread@0x4369A8] targetTid=%d ra=0x%08x\\n",
                        (int32_t)getRegU32(ctx, 4), getRegU32(ctx, 31));
            fflush(stderr);
        }
        if (s_orig4369a8) s_orig4369a8(rdram, ctx, runtime);
    });
'''

# Place right before static auto stub_sceSifGetSreg
target_sreg = '    static auto stub_sceSifGetSreg ='
assert target_sreg in content, 'target_sreg not found'
content = content.replace(target_sreg, hook_slot + '\n' + target_sreg)

# 2. Add sync logging in handleSyscall
target_syscall = '    const uint32_t syscallId = (encodedSyscallId != 0u)\n                                   ? encodedSyscallId\n                                   : getRegU32(ctx, 3); // $v1 / $3 is the EE kernel syscall number'
assert target_syscall in content, 'target_syscall not found'

sync_code = '''
    const uint32_t syscallId = (encodedSyscallId != 0u)
                                   ? encodedSyscallId
                                   : getRegU32(ctx, 3); // $v1 / $3 is the EE kernel syscall number

    static int s_traceSync = -1;
    if (s_traceSync == -1)
    {
        const char *env = std::getenv("PS2X_TRACE_SYNC");
        s_traceSync = (env && std::strcmp(env, "1") == 0) ? 1 : 0;
    }
    if (s_traceSync == 1)
    {
        if (syscallId == 0x20u)
        {
            uint32_t param = getRegU32(ctx, 4);
            uint32_t entry = *reinterpret_cast<const uint32_t *>(rdram + ((param + 4) & 0x01FFFFFFu));
            uint32_t stack = *reinterpret_cast<const uint32_t *>(rdram + ((param + 8) & 0x01FFFFFFu));
            uint32_t stackSize = *reinterpret_cast<const uint32_t *>(rdram + ((param + 12) & 0x01FFFFFFu));
            uint32_t prio = *reinterpret_cast<const uint32_t *>(rdram + ((param + 20) & 0x01FFFFFFu));
            ps2xSafeLog("[sync:CreateThread] param=0x%08x entry=0x%08x stack=0x%08x size=0x%x prio=%u ra=0x%08x\\n",
                        param, entry, stack, stackSize, prio, getRegU32(ctx, 31));
            fflush(stderr);
        }
        else if (syscallId == 0x32u)
        {
            static uint32_t s_sleepCount = 0;
            if (s_sleepCount++ < 30 || (s_sleepCount % 500) == 0)
            {
                ps2xSafeLog("[sync:SleepThread #%u] pc=0x%08x ra=0x%08x sp=0x%08x\\n",
                            s_sleepCount, ctx->pc, getRegU32(ctx, 31), getRegU32(ctx, 29));
                fflush(stderr);
            }
        }
        else if (syscallId == 0x33u)
        {
            ps2xSafeLog("[sync:WakeupThread] targetTid=%d ra=0x%08x\\n",
                        (int32_t)getRegU32(ctx, 4), getRegU32(ctx, 31));
            fflush(stderr);
        }
        else if (syscallId == (uint32_t)-52 || syscallId == 0xFFFFFFCCu)
        {
            ps2xSafeLog("[sync:iWakeupThread] targetTid=%d ra=0x%08x\\n",
                        (int32_t)getRegU32(ctx, 4), getRegU32(ctx, 31));
            fflush(stderr);
        }
    }'''

content = content.replace(target_syscall, sync_code)

with open(path, 'w', encoding='utf-8', newline='') as f:
    f.write(content)

print("ps2_runtime.cpp updated with PS2X_TRACE_SYNC diagnostics.")
