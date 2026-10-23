import os
import glob
import re

funcs = [
    'sub_00406C08', 'sub_00406C68', 'sub_00406CC0', 'sub_00407008',
    'sub_00407078', 'sub_004071A8', 'sub_00407268', 'sub_00407A60',
    'sub_00407D68', 'sub_00407E90', 'sub_00407EB8'
]

for name in funcs:
    matches = glob.glob(f'recomp_source/{name}*.cpp')
    for path in matches:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        fnos = re.findall(r'0x13[0-9a-fA-F]{2}', code)
        calls = re.findall(r'func_439[0-9a-fA-F]{3}', code)
        print(f"=== {name} ===")
        print(f"  Fnos found: {sorted(set(fnos))}")
        print(f"  Calls: {sorted(set(calls))}")
