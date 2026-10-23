import re

distinct_hashes = set()
cid1_paths = set()
last_tick = None
last_stats = None
sched_lines = 0
intc_stats = None

with open('logs/run_20261020_041902.log', 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if '[frame:upload]' in line:
            m = re.search(r'tick=(\d+)', line)
            if m:
                last_tick = int(m.group(1))
            m2 = re.search(r'hash=(0x[0-9a-fA-F]+)', line)
            if m2:
                distinct_hashes.add(m2.group(1))
        if '[vfi:open]' in line or '[vfi:getstat]' in line:
            idx = line.find('path=')
            if idx != -1:
                path = line[idx+5:].split()[0].strip('"')
                cid1_paths.add(path)
        if '[dma:stats]' in line:
            last_stats = line.strip()
        if '[sched:trace]' in line:
            sched_lines += 1
        if '[run:sec]' in line:
            intc_stats = line.strip()

print(f"Distinct frame hashes ({len(distinct_hashes)}): {sorted(list(distinct_hashes))}")
print(f"Unique CID1 paths ({len(cid1_paths)}):")
for p in sorted(cid1_paths):
    print("  ", p)
print(f"Last tick from [frame:upload]: {last_tick}")
print(f"Last dma stats: {last_stats}")
print(f"Last run:sec / intc stats: {intc_stats}")
print(f"Total scheduler trace lines: {sched_lines}")
