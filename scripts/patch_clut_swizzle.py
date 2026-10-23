with open('PS2Recomp/ps2xRuntime/src/lib/gs/gs_cpu_backend.cpp', 'rb') as f:
    content = f.read()

target = b'''            const char *env = std::getenv("PS2X_GS_CLUT32_SWIZZLE");
            s_clut32Swizzle = (env && (std::strcmp(env, "1") == 0 || std::strcmp(env, "true") == 0)) ? 1 : 0;'''

replacement = b'''            const char *env = std::getenv("PS2X_GS_CLUT32_SWIZZLE");
            s_clut32Swizzle = (env && (std::strcmp(env, "0") == 0 || std::strcmp(env, "false") == 0)) ? 0 : 1;'''

if b'\r\n' in content:
    target = target.replace(b'\n', b'\r\n')
    replacement = replacement.replace(b'\n', b'\r\n')

assert target in content, 'Target not found in gs_cpu_backend.cpp!'
content = content.replace(target, replacement, 1)

with open('PS2Recomp/ps2xRuntime/src/lib/gs/gs_cpu_backend.cpp', 'wb') as f:
    f.write(content)
print('Successfully enabled 32-bit CLUT swizzle by default!')
