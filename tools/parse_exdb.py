import struct

with open('logs/exdb_sound.pck', 'rb') as f:
    pck = f.read()

magic, count_or_offset, name_count = struct.unpack_from('<4sII', pck, 0)
print(f"Magic={magic}, word1=0x{count_or_offset:X} ({count_or_offset}), word2=0x{name_count:X} ({name_count})")

table_off = count_or_offset
print(f"table_off = 0x{table_off:X}")

for i in range(name_count):
    entry_off = table_off + i * 8
    w0, w1 = struct.unpack_from('<II', pck, entry_off)
    name_str = pck[w1:w1+40].split(b'\x00')[0].decode('latin1', errors='ignore')
    if 'bgm' in name_str.lower() or i < 5:
        print(f"Entry {i:3d} (0x{entry_off:X}): w0=0x{w0:X} ({w0}), w1=0x{w1:X} ({w1}) -> name='{name_str}'")

# How does PCK store file offsets?
# Let's inspect where 0x48390 (bgm_desc offset) is in the table!
for i in range(0, count_or_offset, 4):
    val = struct.unpack_from('<I', pck, i)[0]
    if val == 0x48390:
        print(f"Found offset 0x48390 stored at PCK offset 0x{i:X}")
