# VFI Archive Tool (`tools/vfi/vfi.py`)

A tool to parse, search, verify, and extract assets from the `DATA.BIN` VFI archive of *Ape Escape 3* (`SCUS_975.01`).

---

## 1. Overview

`DATA.BIN` begins with a 63-sector (`129,024` bytes = `0x1F800` bytes) Virtual File Index (VFI).
The archive contains **3,994 files** organized in a tree of **266 directories**, totaling **2,140,143,946 bytes** (~2.04 GB) of data.

`vfi.py` provides:
1. **Directory Tree Traversal**: Resolves full paths from directory records without ambiguity.
2. **Hash Table Lookup**: Implements the authentic CRC-16-CCITT algorithm used by `file3.irx`.
3. **Target Validation**: Confirms start sectors and byte lengths of game assets.
4. **Data Extraction**: Extracts assets directly from `ApeEscape3.iso` into `tools/vfi/_out/`.

---

## 2. Usage

### 2.1 Summary Statistics
```bash
python tools/vfi/vfi.py stats
```
Displays total files, directories, data volume, and header fields.

### 2.2 Verify All Hash Table Entries
```bash
python tools/vfi/vfi.py verify
```
Computes the CRC-16 hash for all 3,994 file paths and verifies 100% match against the archive's internal sorted hash table.

### 2.3 Search for a File
Accepts game path formats with or without `cdrom0:` or `host0:` prefixes, and handles forward or backward slashes:
```bash
python tools/vfi/vfi.py find "cdrom0:debug/us/etc/font/seurat_20x20.apefnt"
python tools/vfi/vfi.py find "debug/us/etc/font/seurat_20x20.ttxbin"
```

### 2.4 List All Files
```bash
python tools/vfi/vfi.py list
```
Prints all 3,994 files with relative sector, ISO LSN, byte size, and full path.

### 2.5 Extract File to `_out/`
Extracts file contents into `tools/vfi/_out/` (ignored by git):
```bash
python tools/vfi/vfi.py extract "cdrom0:debug/us/etc/font/seurat_20x20.apefnt"
python tools/vfi/vfi.py extract "cdrom0:debug/us/etc/font/seurat_20x20.ttxbin"
```

---

## 3. VFI Binary Format Reference

### Header (`0x00..0x1F`, 32 bytes)
| Offset | Type | Value / Purpose |
| :--- | :--- | :--- |
| `+0x00` | `char[4]` | Magic `"VFI\0"` (`0x00494656`) |
| `+0x04` | `uint32` | Version (`1`) |
| `+0x08` | `uint32` | Sector count of VFI index (`63` = `0x3F` sectors = `129,024` bytes) |
| `+0x0C` | `uint32` | Reserved (`0`) |
| `+0x10` | `uint32` | Build ID / Metadata (`0x010A0F9A`) — low 16 bits is entry count (`3,994`) |
| `+0x14` | `uint32` | File Record Table offset (`0x00003E88`) |
| `+0x18` | `uint32` | Directory Tree Table offset (`0x0001E340`) |
| `+0x1C` | `uint32` | Directory Tree Table end offset (`0x0001F47C`) |

### Section 1: Hash Lookup Table (`0x00020..0x03E88`, 3,994 entries)
- Sorted ascending by 16-bit CRC hash key.
- Each 32-bit entry:
  - `bits 0..15`: 16-bit CRC hash key
  - `bits 16..31`: `(file_record_offset - 0x3E88) >> 2` (word offset into File Record Table)

### Section 2: File Record Table (`0x03E88..0x1E340`, 3,994 variable-length records)
- Quadword/dword aligned.
  - `+0x00` (`uint16`): Record length in bytes
  - `+0x02` (`uint16`): Parent directory relative offset (relative to `0x1E340`)
  - `+0x04` (`uint32`): Start sector relative to `DATA.BIN` LSN 3576 (`absolute_lsn = 3576 + start_sector`)
  - `+0x08` (`uint32`): File size in bytes
  - `+0x0C..`: Null-terminated ASCII filename (basename only)

### Section 3: Directory Tree Table (`0x1E340..0x1F47C`, 266 variable-length records)
  - `+0x00` (`uint16`): Record length in bytes
  - `+0x02` (`uint16`): Subtree end byte offset relative to record start
  - `+0x04` (`uint16`): Parent directory relative offset (`0` for roots `bin` and `debug`)
  - `+0x06` (`uint16`): First file word offset
  - `+0x08..`: Null-terminated ASCII directory name

---

## 4. Validated Target Entries
- `debug/us/etc/font/seurat_20x20.apefnt`:
  - Relative Sector: `0x1ADF4` (`110068`)
  - Absolute LSN: `113644`
  - Size: `6,728` bytes
  - CRC16 Hash: `0x6038`
- `debug/us/etc/font/seurat_20x20.ttxbin`:
  - Relative Sector: `0x1ADF8` (`110072`)
  - Absolute LSN: `113648`
  - Size: `7,156` bytes
  - CRC16 Hash: `0xC283`
