import os

path = r'PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = '    const uint32_t slot36ef00 = (0x0036EF00u - g_ps2RecompiledFunctionTableBase) >> 2;'
end_marker = '    replaceFunction(0x00428C48u, [](uint8_t *rdram, R5900Context *ctx, PS2Runtime *runtime) {'

assert start_marker in content, 'start marker not found'
assert end_marker in content, 'end marker not found'

idx_start = content.find(start_marker)
idx_end = content.find(end_marker)
idx_close = content.find('    });', idx_end) + len('    });')

header = '    const char *traceExdbEnv = std::getenv("PS2X_TRACE_EXDB");\n    if (traceExdbEnv && std::strcmp(traceExdbEnv, "1") == 0)\n    {\n'
footer = '\n    }\n'

hook_code = content[idx_start:idx_close]
content = content[:idx_start] + header + hook_code + footer + content[idx_close:]

with open(path, 'w', encoding='utf-8', newline='') as f:
    f.write(content)
print('ps2_runtime.cpp successfully wrapped with PS2X_TRACE_EXDB gate.')
