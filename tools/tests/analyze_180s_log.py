import re

log_file = r'logs/run_taskE_180s.log'
with open(log_file, 'r', errors='ignore') as f:
    lines = [l.strip() for l in f]

print(f"Total lines in 180s log: {len(lines)}")

# a. capture_flag registration loop
flags = []
for l in lines:
    m = re.search(r'capture_flag_(\d+)', l)
    if m:
        flags.append(int(m.group(1)))
if flags:
    print(f"Flags found: count={len(flags)}, min={min(flags)}, max={max(flags)}")
    print(f"Last flag registered: capture_flag_{flags[-1]}")
else:
    print("No capture flags found.")

# Also check shop_items or other flags
shop_items = []
for l in lines:
    m = re.search(r'shop_item_(\d+)', l)
    if m:
        shop_items.append(int(m.group(1)))
if shop_items:
    print(f"Shop items found: count={len(shop_items)}, min={min(shop_items)}, max={max(shop_items)}")
    print(f"Last shop item: shop_item_{shop_items[-1]}")

# Check other registration loops
last_guest_logs = [l for l in lines if '[guest-log]' in l][-20:]
print("\nLast 20 guest logs:")
for l in last_guest_logs:
    print("  ", l)

# b & c: Thread 2 and Thread 3 waking / status
print("\n--- Thread checks ---")
thread_lines = [l for l in lines if 'thread' in l.lower() and not '[run:tick]' in l]
print(f"Thread lines found: {len(thread_lines)}")
for l in thread_lines[:20]:
    print("  ", l)

# Check run:tick samples
print("\n--- run:tick samples (first 3, middle 3, last 5) ---")
tick_lines = [l for l in lines if '[run:tick]' in l]
print(f"Total run:tick entries: {len(tick_lines)}")
for l in tick_lines[:3]:
    print("  ", l)
if len(tick_lines) > 6:
    for l in tick_lines[len(tick_lines)//2 - 1 : len(tick_lines)//2 + 2]:
        print("  ", l)
for l in tick_lines[-5:]:
    print("  ", l)

# d: Counters (dma, gif, vif)
print("\n--- run:sec samples (last 5) ---")
sec_lines = [l for l in lines if '[run:sec]' in l]
for l in sec_lines[-5:]:
    print("  ", l)

# f: Crashes or exceptions
print("\n--- Crashes / Exceptions ---")
exc_lines = [l for l in lines if any(w in l.lower() for w in ['exception', 'fatal', 'abort', 'crash', 'throw', 'error'])]
print(f"Exception-related lines: {len(exc_lines)}")
for l in exc_lines:
    print("  ", l)
