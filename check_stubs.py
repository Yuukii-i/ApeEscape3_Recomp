import re

with open("config.toml", "r") as f:
    config_lines = [l.strip().strip('",') for l in f if "@0x" in l]

with open("PS2Recomp/ps2xRuntime/include/ps2_call_list.h", "r") as f:
    call_list = f.read()

known_stubs = set(re.findall(r"X\s*\(\s*([a-zA-Z0-9_]+)\s*\)", call_list))

matched = []
unmatched = []

for entry in config_lines:
    parts = entry.split("@0x")
    if len(parts) == 2:
        name = parts[0].strip('" ')
        addr = int(parts[1], 16)
        if name in known_stubs:
            matched.append((name, addr))
        else:
            unmatched.append((name, addr))

print(f"Total stubs in config.toml: {len(config_lines)}")
print(f"Matched with ps2_stubs / syscalls: {len(matched)}")
print(f"Unmatched: {len(unmatched)}")
print(f"First 10 matched: {matched[:10]}")
print(f"First 10 unmatched: {unmatched[:10]}")
