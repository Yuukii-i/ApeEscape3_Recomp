import sys

with open('PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp', 'r') as f:
    content = f.read()

target = '''    const uint32_t slot41b6a8 = (0x0041B6A8u - g_ps2RecompiledFunctionTableBase) >> 2;
    static RecompiledFunction s_orig41b6a8 = g_ps2RecompiledFunctionTable[slot41b6a8];
    replaceFunction(0x0041B6A8u, [](uint8_t *rdram, R5900Context *ctx, PS2Runtime *runtime) {
        uint32_t a0 = getRegU32(ctx, 4);
        uint32_t a1 = getRegU32(ctx, 5);
        uint32_t a2 = getRegU32(ctx, 6);
        uint32_t ra = getRegU32(ctx, 31);
        uint32_t sp = getRegU32(ctx, 29);
        ps2xSafeLog("[cxa_throw:ENTER] obj=0x%08x typeinfo=0x%08x dtor=0x%08x ra=0x%08x sp=0x%08x\\n", a0, a1, a2, ra, sp);
        fflush(stderr);
        if (s_orig41b6a8) s_orig41b6a8(rdram, ctx, runtime);
    });'''

replacement = '''    const uint32_t slot41b6a8 = (0x0041B6A8u - g_ps2RecompiledFunctionTableBase) >> 2;
    static RecompiledFunction s_orig41b6a8 = g_ps2RecompiledFunctionTable[slot41b6a8];
    replaceFunction(0x0041B6A8u, [](uint8_t *rdram, R5900Context *ctx, PS2Runtime *runtime) {
        uint32_t a0 = getRegU32(ctx, 4);
        uint32_t a1 = getRegU32(ctx, 5);
        uint32_t a2 = getRegU32(ctx, 6);
        uint32_t ra = getRegU32(ctx, 31);
        uint32_t sp = getRegU32(ctx, 29);
        ps2xSafeLog("[cxa_throw:ENTER] obj=0x%08x typeinfo=0x%08x dtor=0x%08x ra=0x%08x sp=0x%08x\\n", a0, a1, a2, ra, sp);
        fflush(stderr);
        if (s_orig41b6a8) s_orig41b6a8(rdram, ctx, runtime);
    });

    const uint32_t slot4159f8 = (0x004159F8u - g_ps2RecompiledFunctionTableBase) >> 2;
    static RecompiledFunction s_orig4159f8 = g_ps2RecompiledFunctionTable[slot4159f8];
    replaceFunction(0x004159F8u, [](uint8_t *rdram, R5900Context *ctx, PS2Runtime *runtime) {
        uint32_t strAddr = getRegU32(ctx, 4);
        uint32_t ra = getRegU32(ctx, 31);
        uint32_t sp = getRegU32(ctx, 29);
        const char *msg = strAddr ? reinterpret_cast<const char *>(rdram + (strAddr & 0x01FFFFFFu)) : "<null>";
        ps2xSafeLog("[throw_exception:ENTER] msg=\\"%s\\" (strAddr=0x%08x) ra=0x%08x sp=0x%08x\\n", msg, strAddr, ra, sp);
        fflush(stderr);
        if (s_orig4159f8) s_orig4159f8(rdram, ctx, runtime);
    });'''

if target not in content:
    print("ERROR: Target not found")
    sys.exit(1)

content = content.replace(target, replacement, 1)
with open('PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp', 'w', newline='\r\n') as f:
    f.write(content)
print("SUCCESS: Patched throw_exception hook")
