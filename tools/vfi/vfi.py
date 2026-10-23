#!/usr/bin/env python3
"""
VFI (Virtual File Index) Tool for Ape Escape 3 (DATA.BIN).

Parses the 63-sector VFI index stored at LSN 3576 in ApeEscape3.iso,
providing full inspection, path resolution, CRC-16 hash verification,
and file extraction capabilities.
"""

import argparse
import os
import struct
import sys

DATA_BIN_DEFAULT_LSN = 3576
SECTOR_SIZE = 2048
VFI_SECTOR_COUNT = 63
VFI_INDEX_SIZE = VFI_SECTOR_COUNT * SECTOR_SIZE  # 129,024 bytes (0x1F800)

# 256-entry CRC-16 table extracted directly from file3.irx (.data:0x3BE0)
CRC16_TABLE = [
    0x0000, 0x1189, 0x2312, 0x329B, 0x4624, 0x57AD, 0x6536, 0x74BF,
    0x8C48, 0x9DC1, 0xAF5A, 0xBED3, 0xCA6C, 0xDBE5, 0xE97E, 0xF8F7,
    0x1081, 0x0108, 0x3393, 0x221A, 0x56A5, 0x472C, 0x75B7, 0x643E,
    0x9CC9, 0x8D40, 0xBFDB, 0xAE52, 0xDAED, 0xCB64, 0xF9FF, 0xE876,
    0x2102, 0x308B, 0x0210, 0x1399, 0x6726, 0x76AF, 0x4434, 0x55BD,
    0xAD4A, 0xBCC3, 0x8E58, 0x9FD1, 0xEB6E, 0xFAE7, 0xC87C, 0xD9F5,
    0x3183, 0x200A, 0x1291, 0x0318, 0x77A7, 0x662E, 0x54B5, 0x453C,
    0xBDCB, 0xAC42, 0x9ED9, 0x8F50, 0xFBEF, 0xEA66, 0xD8FD, 0xC974,
    0x4204, 0x538D, 0x6116, 0x709F, 0x0420, 0x15A9, 0x2732, 0x36BB,
    0xCE4C, 0xDFC5, 0xED5E, 0xFCD7, 0x8868, 0x99E1, 0xAB7A, 0xBAF3,
    0x5285, 0x430C, 0x7197, 0x601E, 0x14A1, 0x0528, 0x37B3, 0x263A,
    0xDECD, 0xCF44, 0xFDDF, 0xEC56, 0x98E9, 0x8960, 0xBBFB, 0xAA72,
    0x6306, 0x728F, 0x4014, 0x519D, 0x2522, 0x34AB, 0x0630, 0x17B9,
    0xEF4E, 0xFEC7, 0xCC5C, 0xDDD5, 0xA96A, 0xB8E3, 0x8A78, 0x9BF1,
    0x7387, 0x620E, 0x5095, 0x411C, 0x35A3, 0x242A, 0x16B1, 0x0738,
    0xFFCF, 0xEE46, 0xDCDD, 0xCD54, 0xB9EB, 0xA862, 0x9AF9, 0x8B70,
    0x8408, 0x9581, 0xA71A, 0xB693, 0xC22C, 0xD3A5, 0xE13E, 0xF0B7,
    0x0840, 0x19C9, 0x2B52, 0x3ADB, 0x4E64, 0x5FED, 0x6D76, 0x7CFF,
    0x9489, 0x8500, 0xB79B, 0xA612, 0xD2AD, 0xC324, 0xF1BF, 0xE036,
    0x18C1, 0x0948, 0x3BD3, 0x2A5A, 0x5EE5, 0x4F6C, 0x7DF7, 0x6C7E,
    0xA50A, 0xB483, 0x8618, 0x9791, 0xE32E, 0xF2A7, 0xC03C, 0xD1B5,
    0x2942, 0x38CB, 0x0A50, 0x1BD9, 0x6F66, 0x7EEF, 0x4C74, 0x5DFD,
    0xB58B, 0xA402, 0x9699, 0x8710, 0xF3AF, 0xE226, 0xD0BD, 0xC134,
    0x39C3, 0x284A, 0x1AD1, 0x0B58, 0x7FE7, 0x6E6E, 0x5CF5, 0x4D7C,
    0xC60C, 0xD785, 0xE51E, 0xF497, 0x8028, 0x91A1, 0xA33A, 0xB2B3,
    0x4A44, 0x5BCD, 0x6956, 0x78DF, 0x0C60, 0x1DE9, 0x2F72, 0x3EFB,
    0xD68D, 0xC704, 0xF59F, 0xE416, 0x90A9, 0x8120, 0xB3BB, 0xA232,
    0x5AC5, 0x4B4C, 0x79D7, 0x685E, 0x1CE1, 0x0D68, 0x3FF3, 0x2E7A,
    0xE70E, 0xF687, 0xC41C, 0xD595, 0xA12A, 0xB0A3, 0x8238, 0x93B1,
    0x6B46, 0x7ACF, 0x4854, 0x59DD, 0x2D62, 0x3CEB, 0x0E70, 0x1FF9,
    0xF78F, 0xE606, 0xD49D, 0xC514, 0xB1AB, 0xA022, 0x92B9, 0x8330,
    0x7BC7, 0x6A4E, 0x58D5, 0x495C, 0x3DE3, 0x2C6A, 0x1EF1, 0x0F78
]


def vfi_hash(path: str) -> int:
    """Computes the 16-bit CRC hash used by file3.irx with consecutive slash collapsing."""
    i = 0
    while i < len(path) and path[i] == '/':
        i += 1
    crc = 0xFFFF
    while i < len(path):
        b = ord(path[i])
        idx = (crc ^ b) & 0xFF
        crc = CRC16_TABLE[idx] ^ (crc >> 8)
        if b == 47:  # '/'
            while i + 1 < len(path) and path[i + 1] == '/':
                i += 1
        i += 1
    return crc & 0xFFFF


def normalize_game_path(raw_path: str) -> str:
    """Normalizes device prefixes (cdrom0:, host0:) and slashes."""
    p = raw_path.strip()
    # Strip device prefixes
    for prefix in ('cdrom0:', 'host0:', 'cdrom:', 'host:'):
        if p.lower().startswith(prefix):
            p = p[len(prefix):]
            break
    # Replace backslashes with forward slashes
    p = p.replace('\\', '/')
    # Strip leading slashes
    p = p.lstrip('/')
    return p


class VfiArchive:
    def __init__(self, iso_path: str, data_bin_lsn: int = DATA_BIN_DEFAULT_LSN):
        self.iso_path = iso_path
        self.data_bin_lsn = data_bin_lsn
        self.header = {}
        self.dirs = {}         # rel_off -> dir_dict
        self.files = []        # list of file_dict
        self.files_by_path = {} # normalized_path -> file_dict
        self.hash_entries = [] # list of (hash_key, word_idx)
        self._load()

    def _load(self):
        if not os.path.exists(self.iso_path):
            raise FileNotFoundError(f"ISO file not found: {self.iso_path}")

        with open(self.iso_path, 'rb') as f:
            f.seek(self.data_bin_lsn * SECTOR_SIZE)
            vfi_bytes = f.read(VFI_INDEX_SIZE)

        if len(vfi_bytes) < VFI_INDEX_SIZE:
            raise ValueError(f"Truncated VFI index: expected {VFI_INDEX_SIZE} bytes, got {len(vfi_bytes)}")

        magic, ver, sec_count, res, b_id, file_tab_off, dir_tab_off, dir_end_off = struct.unpack_from('<4sIIIIIII', vfi_bytes, 0)
        if magic != b'VFI\x00':
            raise ValueError(f"Invalid VFI magic: {magic} (expected b'VFI\\x00')")

        self.header = {
            'magic': magic,
            'version': ver,
            'sector_count': sec_count,
            'build_id': b_id,
            'file_tab_off': file_tab_off,
            'dir_tab_off': dir_tab_off,
            'dir_end_off': dir_end_off
        }

        # 1. Parse Directory Tree Table
        pos = dir_tab_off
        while pos < dir_end_off:
            rec_len, subtree_end, parent_off, first_file = struct.unpack_from('<HHHH', vfi_bytes, pos)
            if rec_len == 0:
                break
            name = vfi_bytes[pos + 8 : pos + rec_len].split(b'\0')[0].decode('latin1')
            rel_off = pos - dir_tab_off
            self.dirs[rel_off] = {
                'rel_off': rel_off,
                'rec_len': rec_len,
                'subtree_end': subtree_end,
                'parent_off': parent_off,
                'first_file': first_file,
                'name': name
            }
            pos += rec_len

        # 2. Parse File Record Table
        pos = file_tab_off
        file_idx = 0
        while pos < dir_tab_off:
            rec_len, dir_rel_off, start_sector, file_size = struct.unpack_from('<HHII', vfi_bytes, pos)
            if rec_len == 0:
                break
            name = vfi_bytes[pos + 12 : pos + rec_len].split(b'\0')[0].decode('latin1')
            dir_path = self._get_dir_path(dir_rel_off)
            full_path = f"{dir_path}/{name}" if dir_path else name
            f_record = {
                'idx': file_idx,
                'offset': pos,
                'rec_len': rec_len,
                'dir_rel_off': dir_rel_off,
                'start_sector': start_sector,
                'iso_lsn': self.data_bin_lsn + start_sector,
                'file_size': file_size,
                'name': name,
                'path': full_path
            }
            self.files.append(f_record)
            self.files_by_path[full_path.lower()] = f_record
            pos += rec_len
            file_idx += 1

        # 3. Parse Hash Table
        hash_tab_bytes = vfi_bytes[0x20 : file_tab_off]
        for i in range(len(hash_tab_bytes) // 4):
            val = struct.unpack_from('<I', hash_tab_bytes, i * 4)[0]
            self.hash_entries.append((val & 0xFFFF, val >> 16))

    def _get_dir_path(self, rel_off: int) -> str:
        parts = []
        curr = rel_off
        while True:
            if curr not in self.dirs:
                break
            d = self.dirs[curr]
            parts.append(d['name'])
            if curr == 0:
                break
            p = d['parent_off']
            if p == curr or (p == 0 and curr >= 36):
                break
            curr = p
        return '/'.join(reversed(parts))

    def find(self, target_path: str):
        norm = normalize_game_path(target_path).lower()
        return self.files_by_path.get(norm)

    def extract(self, target_path: str, output_base_dir: str):
        record = self.find(target_path)
        if not record:
            raise KeyError(f"File not found in VFI archive: '{target_path}'")

        # Guarantee destination is strictly inside output_base_dir
        clean_rel_path = normalize_game_path(record['path'])
        out_full_path = os.path.abspath(os.path.join(output_base_dir, clean_rel_path))
        real_base = os.path.abspath(output_base_dir)

        if not out_full_path.startswith(real_base):
            raise PermissionError(f"Extraction path escape detected: {out_full_path}")

        os.makedirs(os.path.dirname(out_full_path), exist_ok=True)

        with open(self.iso_path, 'rb') as f_iso:
            f_iso.seek(record['iso_lsn'] * SECTOR_SIZE)
            data = f_iso.read(record['file_size'])

        with open(out_full_path, 'wb') as f_out:
            f_out.write(data)

        return out_full_path, len(data)


def find_default_iso() -> str:
    env_iso = os.environ.get('PS2X_ISO')
    if env_iso and os.path.exists(env_iso):
        return env_iso
    candidates = [
        os.path.join('build', 'PS2Recomp', 'ps2xRuntime', 'ApeEscape3.iso'),
        'ApeEscape3.iso',
        os.path.join('..', 'build', 'PS2Recomp', 'ps2xRuntime', 'ApeEscape3.iso')
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]


def main():
    parser = argparse.ArgumentParser(description="VFI Inspection & Extraction Tool for Ape Escape 3")
    parser.add_argument('--iso', default=find_default_iso(), help="Path to ApeEscape3.iso")
    parser.add_argument('--lsn', type=int, default=DATA_BIN_DEFAULT_LSN, help="DATA.BIN starting LSN")

    subparsers = parser.add_subparsers(dest='command', required=True)

    # list
    subparsers.add_parser('list', help="List all files in VFI archive")

    # stats
    subparsers.add_parser('stats', help="Show VFI archive summary statistics")

    # verify
    subparsers.add_parser('verify', help="Verify CRC16 hash table matches all files")

    # find
    p_find = subparsers.add_parser('find', help="Find file entry by path")
    p_find.add_argument('path', help="File path (e.g. cdrom0:debug/us/etc/font/seurat_20x20.apefnt)")

    # extract
    p_ext = subparsers.add_parser('extract', help="Extract file to tools/vfi/_out/")
    p_ext.add_argument('path', help="File path to extract")
    p_ext.add_argument('--out-dir', default=os.path.join(os.path.dirname(__file__), '_out'),
                       help="Destination base folder (defaults strictly to tools/vfi/_out/)")

    args = parser.parse_args()

    vfi = VfiArchive(args.iso, args.lsn)

    if args.command == 'list':
        print(f"{'Sector (Rel/Hex)':<18} {'ISO LSN':<10} {'Size (Bytes)':<14} {'Path'}")
        print("-" * 80)
        for f in vfi.files:
            rel_sec_str = f"0x{f['start_sector']:05X} ({f['start_sector']:<6})"
            print(f"{rel_sec_str:<18} {f['iso_lsn']:<10} {f['file_size']:<14} {f['path']}")
        print("-" * 80)
        print(f"Total Files: {len(vfi.files)}")

    elif args.command == 'stats':
        total_size = sum(f['file_size'] for f in vfi.files)
        print("=== VFI Archive Statistics ===")
        print(f"ISO Image:         {vfi.iso_path}")
        print(f"DATA.BIN LSN:      {vfi.data_bin_lsn} (0x{vfi.data_bin_lsn:X})")
        print(f"VFI Index Sectors: {vfi.header['sector_count']} ({vfi.header['sector_count'] * 2048} bytes)")
        print(f"Build ID:          0x{vfi.header['build_id']:08X}")
        print(f"Total Directories: {len(vfi.dirs)}")
        print(f"Total Files:       {len(vfi.files)}")
        print(f"Total Data Volume: {total_size:,} bytes ({total_size / (1024*1024):.2f} MB)")
        print(f"Hash Table Slots:  {len(vfi.hash_entries)}")

    elif args.command == 'verify':
        print(f"Verifying {len(vfi.files)} files against {len(vfi.hash_entries)} hash table slots...")
        matched = 0
        file_tab_off = vfi.header['file_tab_off']
        for expected_hash, word_idx in vfi.hash_entries:
            foff = file_tab_off + word_idx * 4
            rec = next((x for x in vfi.files if x['offset'] == foff), None)
            if rec:
                chash = vfi_hash(rec['path'])
                if chash == expected_hash:
                    matched += 1
                else:
                    print(f"MISMATCH: {rec['path']} expected 0x{expected_hash:04X}, got 0x{chash:04X}")
            else:
                print(f"Invalid record word offset: {word_idx}")
        print(f"Result: {matched} / {len(vfi.hash_entries)} hash matches verified successfully!")

    elif args.command == 'find':
        rec = vfi.find(args.path)
        if not rec:
            print(f"NOT FOUND: '{args.path}'", file=sys.stderr)
            sys.exit(1)
        h = vfi_hash(rec['path'])
        print(f"Found:        {rec['path']}")
        print(f"Filename:     {rec['name']}")
        print(f"Start Sector: 0x{rec['start_sector']:05X} ({rec['start_sector']})")
        print(f"Absolute LSN: {rec['iso_lsn']}")
        print(f"File Size:    {rec['file_size']} bytes")
        print(f"CRC16 Hash:   0x{h:04X} ({h})")

    elif args.command == 'extract':
        target_path = args.path
        out_base = os.path.abspath(args.out_dir)
        print(f"Extracting '{target_path}' to {out_base}...")
        try:
            out_path, sz = vfi.extract(target_path, out_base)
            print(f"Extracted {sz} bytes successfully to:")
            print(f"  {out_path}")
        except Exception as e:
            print(f"Extraction failed: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    main()
