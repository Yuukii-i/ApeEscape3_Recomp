with open('PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp', 'rb') as f:
    content = f.read()

target = b'''    static auto wrapperSyscall4 = [](uint8_t *rdram, R5900Context *ctx, PS2Runtime *runtime) {
        ps2xSafeLog( "[syscall-wrapper] Dispatching syscall 4 at pc=0x%08x (ra=0x%08x)\\n", ctx->pc, getRegU32(ctx, 31));
        fflush(stderr);
        ps2_syscalls::dispatchNumericSyscall(4, rdram, ctx, runtime);
        ctx->pc = getRegU32(ctx, 31);
    };'''.replace(b'\n', b'\r\n')

replacement = b'''    static auto wrapperSyscall4 = [](uint8_t *rdram, R5900Context *ctx, PS2Runtime *runtime) {
        uint32_t sp = getRegU32(ctx, 29);
        uint32_t ra = getRegU32(ctx, 31);
        uint32_t a0 = getRegU32(ctx, 4);
        uint32_t a1 = getRegU32(ctx, 5);
        uint32_t v0 = getRegU32(ctx, 2);
        ps2xSafeLog("[syscall-wrapper] Dispatching syscall 4 (ExitThread) at pc=0x%08x ra=0x%08x sp=0x%08x a0=0x%08x a1=0x%08x v0=0x%08x\\n",
                    ctx->pc, ra, sp, a0, a1, v0);
        if (sp >= 0x100000 && sp + 0x100 <= PS2_RAM_SIZE) {
            for (uint32_t off = 0; off < 0x100; off += 16) {
                uint32_t w0 = *reinterpret_cast<const uint32_t *>(rdram + sp + off);
                uint32_t w1 = *reinterpret_cast<const uint32_t *>(rdram + sp + off + 4);
                uint32_t w2 = *reinterpret_cast<const uint32_t *>(rdram + sp + off + 8);
                uint32_t w3 = *reinterpret_cast<const uint32_t *>(rdram + sp + off + 12);
                ps2xSafeLog("  [stack sp+0x%02x] 0x%08x 0x%08x 0x%08x 0x%08x\\n", off, w0, w1, w2, w3);
            }
        }
        fflush(stderr);
        ps2_syscalls::dispatchNumericSyscall(4, rdram, ctx, runtime);
        ctx->pc = getRegU32(ctx, 31);
    };'''.replace(b'\n', b'\r\n')

assert target in content, 'target not found!'
content = content.replace(target, replacement, 1)

with open('PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp', 'wb') as f:
    f.write(content)
print('Updated wrapperSyscall4')
