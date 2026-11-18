import struct, os
iso = next(p for p in (r"C:\ApeEscape3_Recomp\build\PS2Recomp\ps2xRuntime\ApeEscape3.iso", r"C:\ApeEscape3_Recomp\ApeEscape3.iso") if os.path.exists(p))
f = open(iso, "rb")
def sec(lsn, n=1):
    f.seek(lsn * 2048); return f.read(2048 * n)
pvd = sec(16)
root = pvd[156:156 + 34]
rlsn, rsize = struct.unpack_from("<I", root, 2)[0], struct.unpack_from("<I", root, 10)[0]
d = sec(rlsn, (rsize + 2047) // 2048); p = 0; lsn = None
while p < len(d):
    L = d[p]
    if L == 0: p = (p // 2048 + 1) * 2048; continue
    nm = d[p + 33:p + 33 + d[p + 32]].decode("ascii", "replace")
    if nm.upper().startswith("DATA.BIN"): lsn = struct.unpack_from("<I", d, p + 2)[0]
    p += L
idx = sec(lsn, 63)
assert idx[:4] == b"VFI\0"
fileTab, dirTab, dirEnd = struct.unpack_from("<III", idx, 0x14)
dirs = {}; pos = dirTab
while pos + 8 <= dirEnd:
    recLen, subEnd, parent, first = struct.unpack_from("<HHHH", idx, pos)
    if recLen == 0: break
    name = idx[pos + 8:pos + recLen].split(b"\0")[0].decode("ascii", "replace")
    dirs[pos - dirTab] = (name, parent); pos += recLen
def full(o):
    parts = []; seen = 0
    while o in dirs and seen < 16:
        n, par = dirs[o]; parts.append(n); seen += 1
        if par == o: break
        o = par
    return "/".join(reversed(parts))
paths = sorted(full(o) for o in dirs)
st = sorted({p.split("/stage/")[1].split("/")[0] for p in paths if "/stage/" in p and len(p.split("/stage/")[1]) > 0})
print(len(st), "stage folders:")
print(" ".join(st))
