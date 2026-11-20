#!/usr/bin/env python3
"""Parse a PS2 memory card (.ps2) and print name, size, CRC32, and head16hex for BASCUS-97501-0 and BASCUS-97501-M*."""

import struct
import sys
import zlib

RAW_PAGE_SIZE = 528
DATA_PAGE_SIZE = 512
DIR_ENTRY_SIZE = 512

DF_EXISTS = 0x8000
DF_FILE = 0x0010
DF_DIR = 0x0020
FAT_EOF = 0xFFFFFFFF
FAT_ALLOC_BIT = 0x80000000


def read_cluster(raw: bytes, cluster_idx: int, pages_per_cluster: int) -> bytes:
    start_page = cluster_idx * pages_per_cluster
    out = bytearray()
    for p in range(pages_per_cluster):
        off = (start_page + p) * RAW_PAGE_SIZE
        out.extend(raw[off : off + DATA_PAGE_SIZE])
    return bytes(out)


def build_fat(raw: bytes, sb: bytes) -> list[int]:
    pages_per_cluster = struct.unpack_from("<H", sb, 0x2A)[0]
    clusters_per_card = struct.unpack_from("<I", sb, 0x30)[0]
    ifc_list = struct.unpack_from("<32I", sb, 0x50)

    fat: list[int] = []
    for ifc_cluster in ifc_list:
        if ifc_cluster == FAT_EOF or ifc_cluster >= clusters_per_card:
            continue
        ifc_data = read_cluster(raw, ifc_cluster, pages_per_cluster)
        fat_clusters = struct.unpack_from(f"<{len(ifc_data) // 4}I", ifc_data, 0)
        for fat_cluster in fat_clusters:
            if fat_cluster == FAT_EOF or fat_cluster >= clusters_per_card:
                continue
            fat_data = read_cluster(raw, fat_cluster, pages_per_cluster)
            entries = struct.unpack_from(f"<{len(fat_data) // 4}I", fat_data, 0)
            fat.extend(entries)
    return fat


def read_chain(
    raw: bytes,
    fat: list[int],
    alloc_offset: int,
    pages_per_cluster: int,
    start_rel_cluster: int,
    byte_limit: int | None = None,
) -> bytes:
    out = bytearray()
    cur = start_rel_cluster
    visited: set[int] = set()
    while True:
        if cur in visited:
            raise ValueError(f"FAT loop at relative cluster {cur}")
        visited.add(cur)
        out.extend(read_cluster(raw, alloc_offset + cur, pages_per_cluster))
        if byte_limit is not None and len(out) >= byte_limit:
            return bytes(out[:byte_limit])
        if cur >= len(fat):
            break
        nxt = fat[cur]
        if nxt == FAT_EOF or (nxt & FAT_ALLOC_BIT) == 0:
            break
        cur = nxt & 0x7FFFFFFF
    return bytes(out[:byte_limit]) if byte_limit is not None else bytes(out)


def parse_dir_entries(data: bytes, count: int) -> list[dict]:
    entries = []
    for i in range(min(count, len(data) // DIR_ENTRY_SIZE)):
        chunk = data[i * DIR_ENTRY_SIZE : (i + 1) * DIR_ENTRY_SIZE]
        mode, _, length = struct.unpack_from("<HHI", chunk, 0x00)
        cluster = struct.unpack_from("<I", chunk, 0x10)[0]
        raw_name = chunk[0x40:0x60]
        name = raw_name.split(b"\x00", 1)[0].decode("ascii", errors="replace")
        if not (mode & DF_EXISTS):
            continue
        entries.append(
            {
                "name": name,
                "mode": mode,
                "length": length,
                "cluster": cluster,
                "is_dir": bool(mode & DF_DIR),
                "is_file": bool(mode & DF_FILE),
            }
        )
    return entries


def read_dir(
    raw: bytes,
    fat: list[int],
    alloc_offset: int,
    pages_per_cluster: int,
    start_cluster: int,
    entry_count: int | None = None,
) -> list[dict]:
    if entry_count is None:
        first = read_cluster(raw, alloc_offset + start_cluster, pages_per_cluster)
        entry_count = struct.unpack_from("<I", first, 0x04)[0]
    full = read_chain(raw, fat, alloc_offset, pages_per_cluster, start_cluster, entry_count * DIR_ENTRY_SIZE)
    return parse_dir_entries(full, entry_count)


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <card.ps2>", file=sys.stderr)
        return 1

    with open(sys.argv[1], "rb") as f:
        raw = f.read()

    sb = raw[:DATA_PAGE_SIZE]
    if not sb.startswith(b"Sony PS2 Memory Card Format "):
        print("Not a valid PS2 memory card image", file=sys.stderr)
        return 1

    pages_per_cluster = struct.unpack_from("<H", sb, 0x2A)[0]
    alloc_offset = struct.unpack_from("<I", sb, 0x34)[0]
    root_cluster = struct.unpack_from("<I", sb, 0x3C)[0]
    fat = build_fat(raw, sb)

    root_entries = read_dir(raw, fat, alloc_offset, pages_per_cluster, root_cluster)
    target_dirs = [
        e for e in root_entries
        if e["is_dir"] and (e["name"] == "BASCUS-97501-0" or e["name"].startswith("BASCUS-97501-M"))
    ]

    for d in target_dirs:
        sub_entries = read_dir(raw, fat, alloc_offset, pages_per_cluster, d["cluster"], d["length"])
        for e in sub_entries:
            if not e["is_file"]:
                continue
            data = read_chain(raw, fat, alloc_offset, pages_per_cluster, e["cluster"], e["length"])
            crc = zlib.crc32(data) & 0xFFFFFFFF
            head = data[:16].hex()
            print(f"{d['name']}/{e['name']} {len(data)} {crc:08x} {head}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
