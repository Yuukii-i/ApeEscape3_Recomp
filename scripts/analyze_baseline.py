import re

distinct_hashes = set()
cid1_paths = set()
last_tick = None
last_stats = None

with open('logs/run_20261020_023238.log', 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if '[frame:upload]' in line:
            parts = line.split()
            for p in parts:
                if p.startswith('tick='):
                    last_tick = int(p.split('=')[1])
                elif p.startswith('hash=0x'):
                    distinct_hashes.add(p.split('=')[1])
        if '[vfi:open]' in line or '[vfi:getstat]' in line:
            idx = line.find('path=')
            if idx != -1:
                path = line[idx+5:].split()[0].strip('"')
                cid1_paths.add(path)
        if '[dma:stats]' in line:
            last_stats = line.strip()

print(f"Distinct frame hashes ({len(distinct_hashes)}): {sorted(list(distinct_hashes))}")
print(f"Unique CID1 paths ({len(cid1_paths)}):")
for p in sorted(cid1_paths):
    print("  ", p)
print(f"Last tick: {last_tick}")
print(f"Last stats: {last_stats}")
