import os, re

os.makedirs('tools/tests', exist_ok=True)
with open('PS2Recomp/ps2xRuntime/include/ps2_runtime_macros.h', 'r') as f:
    content = f.read()

match = re.search(r'(// PMFHL function implementations[\s\S]*?)(?=// FPU)', content)
if not match:
    raise Exception('PMFHL block not found!')

macro_text = match.group(1).strip()
is_2_args = 'PS2_PMFHL_LW(hi, lo)' in macro_text

with open('tools/tests/extracted_macros.h', 'w') as f:
    f.write('#pragma once\n#include <immintrin.h>\n#include <cstdint>\n\n')
    if is_2_args:
        f.write('#define TEST_MACRO_TAKES_2_ARGS 1\n\n')
    f.write(macro_text + '\n')

print(f"Extracted macro text (is_2_args={is_2_args}):\n{macro_text}")
