import sys

log_file = r'logs/run_20261020_173441.log'
with open(log_file, 'r', errors='ignore') as f:
    lines = [l.strip() for l in f]

print(f"Total lines: {len(lines)}")

print("\n--- 6a: Font CRCs ---")
for l in lines:
    if any(h in l for h in ['ED797CE4', 'E4D29CF2', 'C05DF086', 'ed797ce4', 'e4d29cf2', 'c05df086']):
        print(l)

print("\n--- 6b: atoi(\"115\"), 0x7406C8, dataPtr ---")
for l in lines:
    if '115' in l and ('atoi' in l or '0x7406c8' in l.lower() or 'records=' in l or 'dataPtr' in l):
        print(l)

print("\n--- 6b: BGM map node count ---")
for l in lines:
    if 'func_1BB508' in l and 'total nodes' in l:
        print(l)

print("\n--- 6c: Tick 44 check ---")
for l in lines:
    if 'tick=44' in l or 'throw_out_of_range' in l or 'out_of_range' in l:
        print(l)

print("\n--- 6d: Final progress / ticks reached ---")
for l in lines[-40:]:
    print(l)
