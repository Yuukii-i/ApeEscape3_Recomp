"""Unpack a PCSX2 raw memory card image (Mcd001.ps2, 528-byte pages with ECC or 512-byte pages) into a host folder tree
(the layout the runtime expects under mc0/: <save folder>/<files>).
Usage: python tools/mcd_extract.py Mcd001.ps2 mc0 [--list]"""
import os
import struct
import sys


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    listing = "--list" in sys.argv
    src, dst = args[0], args[1]
    raw = open(src, "rb").read()
    if raw[:28] != b"Sony PS2 Memory Card Format ":
        sys.exit("not a PS2 memory card image")
    page_len, pages_per_cluster, pages_per_block, _, clusters_per_card, alloc_off, alloc_end, rootdir = struct.unpack_from("<HHHHIIII", raw, 0x28)
    stride = 528 if len(raw) % 528 == 0 and len(raw) // 528 >= 16384 else 512
    spp = page_len
    pages = len(raw) // stride
    data = bytearray()
    for p in range(pages):
        data += raw[p * stride:p * stride + spp]  # drop the 16 ECC bytes of each page
    cl_size = spp * pages_per_cluster
    ifc = struct.unpack_from("<32I", data, 0x50)
    # FAT: the indirect FAT cluster list gives the clusters holding FAT cluster numbers, which hold the 32-bit FAT entries
    fat = []
    per = cl_size // 4
    for icl in ifc:
        if icl == 0xFFFFFFFF or len(fat) >= clusters_per_card:
            break
        ind = struct.unpack_from("<%dI" % per, data, icl * cl_size)
        for fcl in ind:
            if fcl == 0xFFFFFFFF or len(fat) >= clusters_per_card:
                break
            fat.extend(struct.unpack_from("<%dI" % per, data, fcl * cl_size))

    def chain(first):
        out, cur, guard = [], first, 0
        while cur != 0xFFFFFFFF and guard < 100000:
            out.append(cur)
            ent = fat[cur] if cur < len(fat) else 0
            if not (ent & 0x80000000):
                break
            nxt = ent & 0x7FFFFFFF
            if nxt == 0x7FFFFFFF:
                break
            cur = nxt
            guard += 1
        return out

    def read_chain(first, length=None):
        buf = bytearray()
        for cl in chain(first):
            o = (alloc_off + cl) * cl_size
            buf += data[o:o + cl_size]
        return bytes(buf if length is None else buf[:length])

    def entries(first, count):
        blob = read_chain(first)
        ents = []
        for i in range(count):
            e = blob[i * 512:(i + 1) * 512]
            if len(e) < 512:
                break
            mode, _, length, _c, cluster, dir_entry = struct.unpack_from("<HHI8sII", e, 0)
            name = e[0x40:0x60].split(b"\0")[0].decode("latin-1")
            ents.append((mode, length, cluster, name))
        return ents

    files = dirs = 0

    def walk(first, count, out_dir, depth):
        nonlocal files, dirs
        for mode, length, cluster, name in entries(first, count):
            if not (mode & 0x8000) or name in (".", ".."):  # bit 15 = entry exists
                continue
            path = os.path.join(out_dir, name)
            if mode & 0x20:  # directory: length = number of entries
                dirs += 1
                if listing:
                    print("  " * depth + name + "/ (%d entries)" % length)
                else:
                    os.makedirs(path, exist_ok=True)
                walk(cluster, length, path, depth + 1)
            elif mode & 0x10:  # file
                files += 1
                if listing:
                    print("  " * depth + "%s  %d bytes" % (name, length))
                else:
                    with open(path, "wb") as f:
                        f.write(read_chain(cluster, length))

    root = entries(rootdir, 1)
    root_count = root[0][1] if root else 0
    walk(rootdir, root_count, dst, 0)
    print("card: page %d, %d pages, cluster %d bytes, FAT entries %d | %d dirs, %d files%s" % (spp, pages, cl_size, len(fat), dirs, files, " (listing only)" if listing else " extracted to " + dst))


if __name__ == "__main__":
    main()
