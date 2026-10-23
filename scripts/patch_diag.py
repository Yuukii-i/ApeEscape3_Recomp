import sys

with open('PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp', 'r') as f:
    content = f.read()

target = '''    replaceFunction(0x0036EF00u, [](uint8_t *rdram, R5900Context *ctx, PS2Runtime *runtime) {
        uint32_t size = getRegU32(ctx, 4);
        uint32_t ra = getRegU32(ctx, 31);
        if (s_orig36ef00) s_orig36ef00(rdram, ctx, runtime);
        uint32_t ret = getRegU32(ctx, 2);
        ps2xSafeLog("[MemoryManager:allocate_dlmalloc] size=0x%x (%u) ra=0x%08x -> ret=0x%08x\\n", size, size, ra, ret);
        fflush(stderr);
    });'''

replacement = '''    replaceFunction(0x0036EF00u, [](uint8_t *rdram, R5900Context *ctx, PS2Runtime *runtime) {
        uint32_t size = getRegU32(ctx, 4);
        uint32_t ra = getRegU32(ctx, 31);
        if (s_orig36ef00) s_orig36ef00(rdram, ctx, runtime);
        uint32_t ret = getRegU32(ctx, 2);
        ps2xSafeLog("[MemoryManager:allocate_dlmalloc] size=0x%x (%u) ra=0x%08x -> ret=0x%08x\\n", size, size, ra, ret);
        fflush(stderr);
    });

    const uint32_t slot36edac = (0x0036EDACu - g_ps2RecompiledFunctionTableBase) >> 2;
    static RecompiledFunction s_orig36edac = g_ps2RecompiledFunctionTable[slot36edac];
    replaceFunction(0x0036EDACu, [](uint8_t *rdram, R5900Context *ctx, PS2Runtime *runtime) {
        uint32_t a0 = getRegU32(ctx, 4);
        uint32_t a1 = getRegU32(ctx, 5);
        uint32_t a2 = getRegU32(ctx, 6);
        uint32_t ra = getRegU32(ctx, 31);
        if (s_orig36edac) s_orig36edac(rdram, ctx, runtime);
        uint32_t ret = getRegU32(ctx, 2);
        ps2xSafeLog("[func_36EDAC] a0=0x%x a1=0x%x a2=0x%x ra=0x%08x -> ret=0x%08x\\n", a0, a1, a2, ra, ret);
        fflush(stderr);
    });

    const uint32_t slot36ed64 = (0x0036ED64u - g_ps2RecompiledFunctionTableBase) >> 2;
    static RecompiledFunction s_orig36ed64 = g_ps2RecompiledFunctionTable[slot36ed64];
    replaceFunction(0x0036ED64u, [](uint8_t *rdram, R5900Context *ctx, PS2Runtime *runtime) {
        uint32_t a0 = getRegU32(ctx, 4);
        uint32_t ra = getRegU32(ctx, 31);
        if (s_orig36ed64) s_orig36ed64(rdram, ctx, runtime);
        uint32_t ret = getRegU32(ctx, 2);
        ps2xSafeLog("[func_36ED64] a0=0x%x ra=0x%08x -> ret=0x%08x\\n", a0, ra, ret);
        fflush(stderr);
    });

    const uint32_t slot36e368 = (0x0036E368u - g_ps2RecompiledFunctionTableBase) >> 2;
    static RecompiledFunction s_orig36e368 = g_ps2RecompiledFunctionTable[slot36e368];
    replaceFunction(0x0036E368u, [](uint8_t *rdram, R5900Context *ctx, PS2Runtime *runtime) {
        uint32_t a0 = getRegU32(ctx, 4);
        uint32_t ra = getRegU32(ctx, 31);
        if (s_orig36e368) s_orig36e368(rdram, ctx, runtime);
        uint32_t ret = getRegU32(ctx, 2);
        ps2xSafeLog("[func_36E368] a0=0x%x ra=0x%08x -> ret=0x%08x\\n", a0, ra, ret);
        fflush(stderr);
    });

    const uint32_t slot36ee4c = (0x0036EE4Cu - g_ps2RecompiledFunctionTableBase) >> 2;
    static RecompiledFunction s_orig36ee4c = g_ps2RecompiledFunctionTable[slot36ee4c];
    replaceFunction(0x0036EE4Cu, [](uint8_t *rdram, R5900Context *ctx, PS2Runtime *runtime) {
        uint32_t a0 = getRegU32(ctx, 4);
        uint32_t ra = getRegU32(ctx, 31);
        if (s_orig36ee4c) s_orig36ee4c(rdram, ctx, runtime);
        uint32_t ret = getRegU32(ctx, 2);
        ps2xSafeLog("[func_36EE4C] a0=0x%x ra=0x%08x -> ret=0x%08x\\n", a0, ra, ret);
        fflush(stderr);
    });

    const uint32_t slot36e178 = (0x0036E178u - g_ps2RecompiledFunctionTableBase) >> 2;
    static RecompiledFunction s_orig36e178 = g_ps2RecompiledFunctionTable[slot36e178];
    replaceFunction(0x0036E178u, [](uint8_t *rdram, R5900Context *ctx, PS2Runtime *runtime) {
        uint32_t a0 = getRegU32(ctx, 4);
        uint32_t a1 = getRegU32(ctx, 5);
        uint32_t a2 = getRegU32(ctx, 6);
        uint32_t ra = getRegU32(ctx, 31);
        if (s_orig36e178) s_orig36e178(rdram, ctx, runtime);
        uint32_t ret = getRegU32(ctx, 2);
        ps2xSafeLog("[func_36E178] a0=0x%x a1=0x%x a2=0x%x ra=0x%08x -> ret=0x%08x\\n", a0, a1, a2, ra, ret);
        fflush(stderr);
    });'''

if target not in content:
    print("ERROR: Target not found")
    sys.exit(1)

content = content.replace(target, replacement, 1)
with open('PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp', 'w', newline='\r\n') as f:
    f.write(content)
print("SUCCESS: Patched")
