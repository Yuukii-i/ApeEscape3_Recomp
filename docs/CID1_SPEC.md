# Ape Escape 3 (`SCUS_975.01`) `CID1` (`file3.irx`) & `DATA.BIN` VFI Technical Specification

> **Status Tag Legend**:
> - `[CONFIRMED file:line]` / `[CONFIRMED log:line]`: Verified directly against disassembly, source code, ISO bytes, or execution logs.
> - `[INFERRED: reason]`: Logical deduction from confirmed code or data structures.
> - `[UNKNOWN]`: Not yet determined from code or logs.

---

## 1. Executive Summary & Purpose

In *Ape Escape 3*, all file assets (IOP modules, fonts, scripts, stage models, textures, animations, audio) are packaged inside `DATA.BIN` at LSN `3576` (`0x006FC000`) of `ApeEscape3.iso`.
At startup, the EE loads the 63-sector (`129,024` bytes = `0x1F800` bytes) Virtual File Index (VFI) and communicates with `file3.irx` running on the IOP using **SIF Command ID 1** (`CID 1`).

Currently in [`RPC.cpp:1201-1256`](file:///c:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/Kernel/Syscalls/RPC.cpp#L1201-L1256), the `cid == 1` handler returns dummy zeroed reply packets and reads **zero bytes** from `DATA.BIN`. Consequently:
1. `debug/us/etc/font/seurat_20x20.apefnt` and `seurat_20x20.ttxbin` are never loaded into guest RDRAM.
2. The EE wait loop in `sub_001DC578` (`0x1DC5A4`) passes only because fake completion flags are set, but the game displays missing text or halts later when dereferencing empty font/asset buffers.
3. The ring tail pointer (`instance + 0x20`) is clobbered with `0` because `reply.unk24` is hardcoded to `0`.

This specification provides the exact, byte-level specification for implementing native high-level emulation (HLE) of `file3.irx` and serving files from `DATA.BIN` directly within `ps2xRuntime`.

---

## 2. VFI (`DATA.BIN`) Binary Archive Format

The archive begins at ISO sector `3576` (`3576 * 2048 = 0x006FC000`). The first `63` sectors (`0x00000..0x1F7FF`) contain the VFI header and lookup structures.

```
+-------------------------------------------------------------------------+
| Header (0x00000..0x0001F) [32 bytes]                                     |
+-------------------------------------------------------------------------+
| Section 1: Hash Lookup Table (0x00020..0x03E87) [3,994 entries * 4 B]   |
+-------------------------------------------------------------------------+
| Section 2: File Record Table (0x03E88..0x1E33F) [3,994 variable records]|
+-------------------------------------------------------------------------+
| Section 3: Directory Tree Table (0x1E340..0x1F47B) [266 variable records]|
+-------------------------------------------------------------------------+
| Zero Padding (0x1F47C..0x1F7FF) [900 bytes]                             |
+-------------------------------------------------------------------------+
| File Payload 0: bin/irx/3.0/dbcman.irx (starts at sector 63 = 0x1F800)  |
+-------------------------------------------------------------------------+
```
`[CONFIRMED ApeEscape3.iso:LSN_3576, tools/iop/file3.irx:0x3068-0x3200]`.

### 2.1 VFI Header (`0x00000..0x0001F`, 32 bytes)
| Offset | Type | Value (Ape Escape 3) | Description |
| :--- | :--- | :--- | :--- |
| `+0x00` | `char[4]` | `"VFI\0"` (`0x00494656`) | Archive magic bytes `[CONFIRMED ApeEscape3.iso:LSN_3576]`. |
| `+0x04` | `uint32` | `0x00000001` | Format version `1` `[CONFIRMED ApeEscape3.iso:LSN_3576]`. |
| `+0x08` | `uint32` | `0x0000003F` (`63`) | VFI index size in 2048-byte sectors (`63 * 2048 = 129,024` bytes) and relative start sector of first file payload `[CONFIRMED ApeEscape3.iso:LSN_3576]`. |
| `+0x0C` | `uint32` | `0x00000000` | Reserved `[CONFIRMED ApeEscape3.iso:LSN_3576]`. |
| `+0x10` | `uint32` | `0x010A0F9A` | Build ID / Metadata. Low 16 bits (`0x0F9A` = `3,994`) is the exact entry count read by `file3.irx:0x30A4` `[CONFIRMED tools/iop/file3.irx:0x30A4]`. |
| `+0x14` | `uint32` | `0x00003E88` | Byte offset of **File Record Table** `[CONFIRMED ApeEscape3.iso:LSN_3576]`. |
| `+0x18` | `uint32` | `0x0001E340` | Byte offset of **Directory Tree Table** `[CONFIRMED ApeEscape3.iso:LSN_3576]`. |
| `+0x1C` | `uint32` | `0x0001F47C` | End byte offset of Directory Tree Table `[CONFIRMED ApeEscape3.iso:LSN_3576]`. |

### 2.2 Section 1: Hash Lookup Table (`0x00020..0x03E88`, 3,994 entries)
- Entry count: `(0x3E88 - 0x20) / 4 = 3,994` entries `[CONFIRMED tools/vfi/vfi.py:stats]`.
- Array of `uint32_t` sorted ascending by 16-bit CRC hash key:
  - `bits 0..15` (`lo16`): 16-bit CRC hash key `[CONFIRMED tools/iop/file3.irx:0x30E0]`.
  - `bits 16..31` (`hi16`): `(file_record_byte_offset - 0x3E88) >> 2` (word offset into File Record Table) `[CONFIRMED tools/iop/file3.irx:0x311C]`.

### 2.3 Section 2: File Record Table (`0x03E88..0x1E340`, 3,994 variable-length records)
Records are contiguous and 4-byte aligned:
- `+0x00` (`uint16`): `rec_len` — Total record byte length (multiple of 4) `[CONFIRMED ApeEscape3.iso:LSN_3576]`.
- `+0x02` (`uint16`): `dir_rel_off` — Byte offset of parent directory in Directory Tree Table (relative to `0x1E340`) `[CONFIRMED ApeEscape3.iso:LSN_3576]`.
- `+0x04` (`uint32`): `start_sector` — 2048-byte sector offset relative to `DATA.BIN` LSN `3576` (`absolute_iso_lsn = 3576 + start_sector`) `[CONFIRMED tools/iop/file3.irx:0x32FC]`.
- `+0x08` (`uint32`): `file_size` — Exact uncompressed file size in bytes `[CONFIRMED tools/iop/file3.irx:0x3310]`.
- `+0x0C..rec_len`: Null-terminated ASCII filename (basename only, e.g. `"seurat_20x20.apefnt"`), zero-padded to 4-byte alignment `[CONFIRMED ApeEscape3.iso:LSN_3576]`.

### 2.4 Section 3: Directory Tree Table (`0x1E340..0x1F47C`, 266 variable-length records)
Total size is `4,412` bytes (`0x113C`):
- `+0x00` (`uint16`): `rec_len` — Record length in bytes `[CONFIRMED ApeEscape3.iso:LSN_3576]`.
- `+0x02` (`uint16`): `subtree_end` — Subtree span in bytes relative to record start `[CONFIRMED tools/vfi/vfi.py:stats]`.
- `+0x04` (`uint16`): `parent_off` — Byte offset of parent directory relative to `0x1E340`. For root directories (`bin` at `0` with `subtree_end=36` and `debug` at `36` with `subtree_end=4376`), `parent_off == 0` `[CONFIRMED tools/vfi/vfi.py:stats]`.
- `+0x06` (`uint16`): `first_file_word_off` — First file record word offset `[CONFIRMED ApeEscape3.iso:LSN_3576]`.
- `+0x08..rec_len`: Null-terminated ASCII directory name (e.g. `"bin"`, `"irx"`, `"3.0"`, `"debug"`, `"us"`, `"etc"`, `"font"`) `[CONFIRMED ApeEscape3.iso:LSN_3576]`.

---

## 3. Path Resolution & CRC-16 Hashing Algorithms

### 3.1 Path Resolution via Directory Tree Walk (`[CONFIRMED]`)
Every file record stores `dir_rel_off`. The full path is reconstructed deterministically by walking up the directory parent chain:
```python
def get_dir_path(dirs, rel_off):
    parts = []
    curr = rel_off
    while True:
        d = dirs[curr]
        parts.append(d['name'])
        if curr == 0:
            break
        p = d['parent_off']
        if p == curr or (p == 0 and curr >= 36):
            break
        curr = p
    return '/'.join(reversed(parts))
```
`[CONFIRMED tools/vfi/vfi.py:175-188]`.
All 3,994 files resolve to valid paths with 0 errors.

### 3.2 Authentic CRC-16 Hash Algorithm (`[CONFIRMED file3.irx:0x2DA0-0x2E10]`)
`file3.irx` computes a 16-bit CRC using a 256-word table at `file3.irx:.data:0x3BE0`.
Key properties:
- Initial value: `0xFFFF`.
- Polynomial: Kermit / CRC-16-CCITT reverse (`table[1] = 0x1189`).
- Consecutive forward slashes (`//...`) are collapsed to a single `/`.
- Leading slashes are stripped.
```cpp
uint16_t vfi_hash(const char* path) {
    while (*path == '/') path++;
    uint16_t crc = 0xFFFF;
    while (*path) {
        uint8_t b = (uint8_t)*path;
        uint8_t idx = (crc ^ b) & 0xFF;
        crc = CRC16_TABLE[idx] ^ (crc >> 8);
        if (b == '/') {
            while (*(path + 1) == '/') path++;
        }
        path++;
    }
    return crc;
}
```
`[CONFIRMED tools/iop/file3.irx:0x2DA0-0x2E10, tools/vfi/vfi.py:verify]`.
Verified: **3,994 / 3,994** files match the hash table with 100.00% precision.

---

## 4. `CID1` (`file3.irx`) EE/IOP Protocol Specification

### 4.1 EE SIF Command Registration
The EE client initializes two `file3` instances via `sub_001DA880`:
- **Instance 0**: Handler `sub_001DCEE0`, `data = 0x00771798` (16 FCFD slots at `0x007717CC..0x007718BC`) `[CONFIRMED recomp_source/sub_001DA880_0x1da880.cpp:175-210]`.
- **Instance 1**: Handler `sub_001DCEE0`, `data = 0x00771B88` (16 FCFD slots at `0x00771BBC..0x00771CBC`) `[CONFIRMED task-4396.log:133]`.

### 4.2 16-Byte FCFD Slot Layout (in Guest RAM at `instance + 0x34 + 16 * slot_idx`)
| Offset | Type | Name | Purpose |
| :--- | :--- | :--- | :--- |
| `+0x00` | `uint32` | `magic` | `'DFCF'` (`0x46434644`) `[CONFIRMED recomp_source/sub_001DCEE0_0x1dcee0.cpp:60-72]`. |
| `+0x04` | `uint32` | `seq` | Monotonic sequence number matching request `[CONFIRMED recomp_source/sub_001DCEE0_0x1dcee0.cpp:73-77]`. |
| `+0x08` | `uint32` | `status` | Packed state word: byte `+0x0B` holds `(cmd_opcode << 1)` while pending; bit 7 (`0x80`) is set when complete (`0x80 | (cmd_opcode << 1)`). The EE waits on `*(int32_t*)(slot + 8) < 0` `[CONFIRMED recomp_source/sub_001DCEE0_0x1dcee0.cpp:124-156]`. |
| `+0x0C` | `int32` | `result` | Operation result written by `sub_001DCEE0` from `reply + 0x20` (`bytes_read`, `file_size`, `fd`, or error `< 0`) `[CONFIRMED recomp_source/sub_001DCEE0_0x1dcee0.cpp:83-85]`. |

### 4.3 IOP Ring-Buffer Advancement & Command Alignment
- Commands are aligned to **16 bytes** (`(cmd_len + 15) & ~15`) `[CONFIRMED recomp_source/sub_001DC33C_0x1dc33c.cpp:108-121]`.
- The EE provides destination ring offset `destExtra` in `sceSifSendCmd` (`0x80`, `0xC0`, `0x110`, ...) `[CONFIRMED logs/baseline.log:268-275]`.
- **Tail Pointer Advance Rule**: In the reply packet, `reply + 0x24` **MUST** be set to `destExtra + aligned_cmdSize`.
  - When `sub_001DCEE0` processes the reply (`recomp_source/sub_001DCEE0_0x1dcee0.cpp:304-322`), it reads `reply + 0x24` and updates the ring tail at `instance + 0x20`. Setting `reply + 0x24 = 0` clobbers the ring allocator and causes future requests to overwrite active buffers `[CONFIRMED recomp_source/sub_001DCEE0_0x1dcee0.cpp:304-322]`.

---

## 5. Per-Command Detailed Specification

### 5.1 Command `0x03` (`Open`)
- **EE Sender**: `sub_001DBD6C_0x1dbd6c.cpp:120-320` `[CONFIRMED]`.
- **Request Layout (`srcExtra`)**:
  - `+0x00` (`uint32`): `cmdSize` (aligned, typically `0x30` or `0x40`)
  - `+0x04` (`uint32`): `0x00000003` (`cmd_opcode`)
  - `+0x08` (`uint32`): `slot_ptr`
  - `+0x0C` (`uint32`): `seq`
  - `+0x10` (`uint32`): `open_flags` (e.g. read-only `1`)
  - `+0x14` (`uint16`): `sub_flags`
  - `+0x16` (`uint16`): `priority`
  - `+0x18..`: Null-terminated path string
- **Pending Status**: `0x06` (`0x03 << 1`).
- **Reply Layout**: Standard 48-byte header (`reply + 0x20 = fd`).
- **Result Convention**: Non-negative file descriptor `fd >= 0` (`0..15`) on success, `< 0` on error `[CONFIRMED tools/iop/file3.irx:0x09B4]`.

### 5.2 Command `0x04` (`Close`)
- **EE Sender**: `sub_001DBEC4_0x1dbec4.cpp:80-260` `[CONFIRMED]`.
- **Request Layout (`srcExtra`, 32 bytes)**:
  - `+0x00` (`uint32`): `0x00000020` (`cmdSize = 32`)
  - `+0x04` (`uint32`): `0x00000004` (`cmd_opcode`)
  - `+0x08` (`uint32`): `slot_ptr`
  - `+0x0C` (`uint32`): `seq`
  - `+0x10` (`uint32`): `fd` (file descriptor to close)
- **Pending Status**: `0x08` (`0x04 << 1`).
- **Reply Layout**: Standard 48-byte header (`reply + 0x20 = 0`).
- **Result Convention**: `0` on success, `< 0` on error `[CONFIRMED tools/iop/file3.irx:0x0A24]`.

### 5.3 Command `0x06` (`Read by fd`)
- **EE Sender**: `sub_001DC044_0x1dc044.cpp:170-290` `[CONFIRMED]`.
- **Request Layout (`srcExtra`, 32 bytes)**:
  - `+0x00` (`uint32`): `0x00000020` (`cmdSize = 32`)
  - `+0x04` (`uint32`): `0x00000006` (`cmd_opcode`)
  - `+0x08` (`uint32`): `slot_ptr`
  - `+0x0C` (`uint32`): `seq`
  - `+0x10` (`uint32`): `fd`
  - `+0x14` (`uint32`): `ee_dst_buf` (guest RDRAM address)
  - `+0x18` (`uint32`): `read_size` (bytes to read)
- **Pending Status**: `0x0C` (`0x06 << 1`).
- **Reply Layout**: Standard 48-byte header (`reply + 0x20 = bytes_read`).
- **Result Convention**: Number of bytes transferred `bytes_read >= 0`, `< 0` on error `[CONFIRMED recomp_source/sub_001DCEE0_0x1dcee0.cpp:83-85]`.

### 5.4 Command `0x07` (`Seek`)
- **EE Sender**: `sub_001DC134_0x1dc134.cpp:190-300` `[CONFIRMED]`.
- **Request Layout (`srcExtra`, 32 bytes)**:
  - `+0x00` (`uint32`): `0x00000020` (`cmdSize = 32`)
  - `+0x04` (`uint32`): `0x00000007` (`cmd_opcode`)
  - `+0x08` (`uint32`): `slot_ptr`
  - `+0x0C` (`uint32`): `seq`
  - `+0x10` (`uint32`): `fd`
  - `+0x14` (`int32`):  `offset`
  - `+0x18` (`uint32`): `whence` (`0` = SET, `1` = CUR, `2` = END)
  - `+0x1C` (`uint32`): `flags`
- **Pending Status**: `0x0E` (`0x07 << 1`).
- **Reply Layout**: Standard 48-byte header (`reply + 0x20 = new_offset`).
- **Result Convention**: Resulting file offset from beginning of file `new_offset >= 0`, `< 0` on error `[CONFIRMED recomp_source/sub_001DCEE0_0x1dcee0.cpp:167-219]`.

### 5.5 Command `0x09` (`Getstat / FileInfo by path`)
- **EE Senders**: `sub_001DB31C_0x1db31c.cpp:60-240`, `sub_001DBB00_0x1dbb00.cpp:50-300` `[CONFIRMED]`.
- **Request Layout (`srcExtra`)**:
  - `+0x00` (`uint32`): `cmdSize` (aligned, e.g. `64`)
  - `+0x04` (`uint32`): `0x00000009` (`cmd_opcode`)
  - `+0x08` (`uint32`): `slot_ptr` (e.g. `0x00771BBC`)
  - `+0x0C` (`uint32`): `seq`
  - `+0x10` (`uint32`): `stat_dst_ptr` (guest RDRAM address where 64-byte stat struct is copied!)
  - `+0x14` (`uint32`): `flags / mode`
  - `+0x18..`: Null-terminated path string (e.g. `"debug/us/etc/font/seurat_20x20.apefnt"`)
- **Pending Status**: `0x12` (`0x09 << 1`).
- **Reply Layout (112 bytes total: 48 bytes header + 64 bytes stat)**:
  - `+0x00..+0x0F`: SIF reply envelope header
  - `+0x10` (`uint32`): `'DFCF'` (`0x46434644`)
  - `+0x14` (`uint32`): `0x00000009` (`cmd_opcode`)
  - `+0x18` (`uint32`): `slot_ptr`
  - `+0x1C` (`uint32`): `seq`
  - `+0x20` (`int32`):  `result` (`0` on success, `< 0` on file not found)
  - `+0x24` (`uint32`): `destExtra + aligned_cmdSize` (updated ring tail)
  - `+0x28` (`int32`):  `is_done = 1`
  - `+0x2C` (`uint32`): `stat_dst_ptr` (must match request `stat_dst_ptr`!)
  - `+0x30..+0x6F` (64 bytes): **Stat Struct** copied to `stat_dst_ptr` via `memcpy` in `sub_001DCEE0:124-142`!
- **Stat Struct Field Mapping (`reply + 0x30..0x6F`)**:
  - `+0x00` (`uint32`): `mode` (`0x1000` for regular file, `0x2000` for directory) `[CONFIRMED tools/iop/file3.irx:0x0D88, 0x0DBC]`.
  - `+0x04` (`uint32`): `start_sector` (relative to `DATA.BIN` LSN 3576) `[CONFIRMED tools/iop/file3.irx:0x32FC]`.
  - `+0x08` (`uint32`): `file_size` (exact 32-bit byte count) `[CONFIRMED tools/iop/file3.irx:0x3310]`.
  - `+0x0C..+0x3F`: Zero-filled.
- **Fields Actually Read by EE Callers**:
  - Offset `+0x00`: File mode / type (checked for regular file vs directory).
  - Offset `+0x08`: File size in bytes (used for memory allocations and load sizing).
  - Other offsets (`+0x04`, `+0x0C..+0x3F`) are ignored or kept internal `[CONFIRMED recomp_source/sub_001DC33C_0x1dc33c.cpp:258-350]`.

### 5.6 Command `0x0B` (`Read / Load file by path`)
- **EE Sender**: `sub_001DC33C_0x1dc33c.cpp:258-375` (invoked via `sub_001DC7BC`) `[CONFIRMED]`.
- **Request Layout (`srcExtra`, typically 80 bytes)**:
  - `+0x00` (`uint32`): `cmdSize` (e.g. `80`)
  - `+0x04` (`uint32`): `0x0000000B` (`cmd_opcode`)
  - `+0x08` (`uint32`): `slot_ptr` (e.g. `0x00771BBC`)
  - `+0x0C` (`uint32`): `seq`
  - `+0x10` (`uint32`): `ee_dst_buf` (destination buffer in guest RDRAM, e.g. `0x00A0F380`)
  - `+0x14` (`uint32`): `offset` (byte offset into file)
  - `+0x18` (`uint32`): `size` (bytes to read; `0` = read whole file to EOF!)
  - `+0x1C` (`uint16`): `flags` (e.g. `4`)
  - `+0x1E` (`uint16`): `priority`
  - `+0x20..`: Null-terminated path string (e.g. `"debug/us/etc/font/seurat_20x20.apefnt"`)
- **Pending Status**: `0x16` (`0x0B << 1`).
- **Reply Layout**: Standard 48-byte header (`reply + 0x20 = bytes_read`).
- **Result Convention**: Number of bytes read `bytes_read >= 0`, or error `< 0`.

---

## 6. Execution Semantics for Command `0x0B`

1. **Size Semantics (`size == 0`)**:
   - When requested `size == 0`, `file3.irx:0x178C-0x17A0` calculates `size = file_size - offset`.
   - The runtime **MUST** read the entire remaining file from `offset` to EOF `[CONFIRMED tools/iop/file3.irx:0x178C-0x17A0]`.
2. **Partial Reads & EOF Handling**:
   - If `offset >= file_size`, 0 bytes are read, result is `0`.
   - If `offset + size > file_size`, size is clamped to `file_size - offset` `[CONFIRMED tools/iop/file3.irx:0x179C]`.
3. **Guest RAM Memory Delivery Order**:
   - The file payload bytes **MUST** be written to `rdram + ee_dst_buf` **before** (or synchronously during) the completion handler callback `sub_001DCEE0`.
   - Rationale: The moment `sub_001DCEE0` sets bit 7 of `slot + 0x0B`, `sub_001DC578:65` exits its wait loop and returns `1`, and the caller immediately parses the data structure at `ee_dst_buf`. If bytes are delivered asynchronously after the completion bit is set, the game reads uninitialized memory `[CONFIRMED recomp_source/sub_001DC578_0x1dc578.cpp:61-115]`.
4. **Synchronous vs Asynchronous Completion Tolerance**:
   - The EE **100% tolerates synchronous completion** inside `sceSifSendCmd`.
   - Evidence: `sub_001DC578:62-68` checks `if (*(int32_t*)(slot + 8) < 0) return 1;` **before** entering the spin loop! If `sceSifSendCmd` invokes `sub_001DCEE0` synchronously before returning, `sub_001DC578` exits on its first check without spinning `[CONFIRMED recomp_source/sub_001DC578_0x1dc578.cpp:62-78, logs/baseline.log:268-280]`.

---

## 7. C++ Runtime HLE Implementation Guide (for `RPC.cpp`)

Below is the exact, complete C++ logic to replace lines 1201–1256 of [`RPC.cpp`](file:///c:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/Kernel/Syscalls/RPC.cpp#L1201-L1256):

```cpp
// Structure of 112-byte Reply Packet sent to EE handler sub_001DCEE0
struct SifReplyPacketCid1Full {
    uint32_t envelope[4];   // 0x00..0x0F: SIF RPC envelope header
    uint32_t magic;         // 0x10: 'DFCF' (0x46434644)
    uint32_t cmd;           // 0x14: Command opcode (9, 11, etc.)
    uint32_t slotPtr;       // 0x18: EE FCFD slot address (e.g. 0x00771BBC)
    uint32_t seq;           // 0x1C: Sequence number matching request
    int32_t  result;        // 0x20: bytes_read / file_size / fd / error
    uint32_t ringTail;      // 0x24: Updated ring tail (destExtra + aligned_cmdSize)
    int32_t  isDone;        // 0x28: 1 = complete, 0 = pending/stream chunk
    uint32_t statDstPtr;    // 0x2C: stat_dst_ptr for cmd 9
    uint8_t  statData[64];  // 0x30..0x6F: 64-byte stat struct (mode at +0, size at +8)
};

// In syscallSceSifSendCmd when (cid == 1):
if (cid == 1) {
    if (size >= 16) {
        uint32_t cmdSize  = *reinterpret_cast<const uint32_t*>(rdram + srcExtra + 0x00);
        uint32_t opcode   = *reinterpret_cast<const uint32_t*>(rdram + srcExtra + 0x04);
        uint32_t slotPtr  = *reinterpret_cast<const uint32_t*>(rdram + srcExtra + 0x08);
        uint32_t seq      = *reinterpret_cast<const uint32_t*>(rdram + srcExtra + 0x0C);
        uint32_t alignedCmd = (cmdSize + 15u) & ~15u;

        SifReplyPacketCid1Full reply{};
        reply.magic     = 0x46434644u; // 'DFCF'
        reply.cmd       = opcode;
        reply.slotPtr   = slotPtr;
        reply.seq       = seq;
        reply.ringTail  = destExtra + alignedCmd; // Advance IOP ring buffer tail
        reply.isDone    = 1;

        if (opcode == 0x09) { // Getstat / FileInfo by path
            uint32_t statDst = *reinterpret_cast<const uint32_t*>(rdram + srcExtra + 0x10);
            const char* pathStr = reinterpret_cast<const char*>(rdram + srcExtra + 0x18);
            std::string normPath = normalizeVfiPath(pathStr);

            reply.statDstPtr = statDst;
            const VfiEntry* entry = findVfiEntry(normPath);
            if (entry) {
                reply.result = 0;
                *reinterpret_cast<uint32_t*>(&reply.statData[0]) = 0x1000u; // Regular file mode
                *reinterpret_cast<uint32_t*>(&reply.statData[4]) = entry->startSector;
                *reinterpret_cast<uint32_t*>(&reply.statData[8]) = entry->fileSize;
            } else {
                reply.result = -1; // File not found
            }
        }
        else if (opcode == 0x0B) { // Read / Load file by path
            uint32_t eeDst   = *reinterpret_cast<const uint32_t*>(rdram + srcExtra + 0x10);
            uint32_t offset  = *reinterpret_cast<const uint32_t*>(rdram + srcExtra + 0x14);
            uint32_t reqSize = *reinterpret_cast<const uint32_t*>(rdram + srcExtra + 0x18);
            const char* pathStr = reinterpret_cast<const char*>(rdram + srcExtra + 0x20);
            std::string normPath = normalizeVfiPath(pathStr);

            const VfiEntry* entry = findVfiEntry(normPath);
            if (entry && offset < entry->fileSize) {
                uint32_t readSize = (reqSize == 0 || (offset + reqSize > entry->fileSize))
                                    ? (entry->fileSize - offset)
                                    : reqSize;

                // Read exact bytes from ISO DATA.BIN into guest RDRAM
                readIsoSectors(3576 + entry->startSector, offset, readSize, rdram + eeDst);
                reply.result = static_cast<int32_t>(readSize);
            } else {
                reply.result = -1;
            }
        }

        // Write reply packet to designated async stack buffer and invoke sub_001DCEE0
        uint32_t replyGuestAddr = 0x01F10000u; // Safe region in async SIF stack
        std::memcpy(rdram + replyGuestAddr, &reply, sizeof(reply));

        // Call EE handler sub_001DCEE0(replyGuestAddr, instancePtr)
        uint32_t instancePtr = (slotPtr >= 0x00771BBCu) ? 0x00771B88u : 0x00771798u;
        invokeEeSifCallback(0x001DCEE0u, replyGuestAddr, instancePtr);
    }
    return 1;
}
```

---

## 8. Verification & Exit Criteria

When the future prompt implements the above logic:
1. **Font Files Loaded**:
   - `debug/us/etc/font/seurat_20x20.apefnt`: `6,728` bytes loaded into guest RDRAM (at `0x00A0F380`).
   - `debug/us/etc/font/seurat_20x20.ttxbin`: `7,156` bytes loaded into guest RDRAM.
   - Verified via non-zero memory checks at `0x00A0F380` and log output `[CID1:read] seurat_20x20.apefnt loaded 6728 bytes`.
2. **Text & 2D Graphics Rendered**:
   - The on-screen text "Now Loading" and the font textures are fully populated.
   - Non-black pixels in `frame_200.png` increase significantly from the baseline `5,099` pixels.
3. **Main Loop Progress**:
   - `STREAM:0` prints advance past 0 (`STREAM:>0` or stage script loading), unblocking the next stage transition.

---

## 9. Directory Stat (0x0A) & Compressed `.sz` Fallback (`[CONFIRMED]`)

### 9.1 Directory Stat Handling
- The EE issues CID1 Getstat commands for directory paths:
  - `0x09`: path at offset `+0x18`
  - `0x0A`: path at offset `+0x20`
- Querying paths such as `debug/us/static` and `debug/us/startup` returns:
  - `mode = 0x2000` (`[CONFIRMED tools/iop/file3.irx:0x0DBC]`)
  - `startSector = 0`
  - `fileSize = 0`
  - `result = 0` (success)
- Live verification:
  - `[CID1:Getstat-0x0A] 'debug/us/static' -> DIR (mode=0x2000)` `[CONFIRMED logs/run_20261019_234141.log:885]`
  - `[CID1:Getstat-0x0A] 'debug/us/startup' -> DIR (mode=0x2000)` `[CONFIRMED logs/run_20261019_234141.log:886]`

### 9.2 Transparent `.sz` Resolution
- In `DATA.BIN`, disk assets in `debug/us/static/` and `debug/us/startup/` are stored with a `.sz` extension (e.g. `exdb_sound.pck.sz`, size 40,448 bytes at LSN 1051154).
- The sound engine initiates queries using logical names (e.g. `debug/us/static/exdb_sound.pck`).
- If an exact file match fails, `VfiArchive::find` transparently checks `path + ".sz"`.
- Live verification:
  - `[CID1:Getstat] 'debug/us/static/exdb_sound.pck' -> FILE size=40448 startSec=1047578` `[CONFIRMED logs/run_20261019_234141.log:889]`
  - `[CID1:ReadPath] 'debug/us/static/exdb_sound.pck' off=0 reqSize=40448 -> read 40448 bytes to 0x0111c480 (CRC32=0x4FCD48BE)` `[CONFIRMED logs/run_20261019_234141.log:890]`
- Unblocked execution: With `exdb_sound.pck` successfully resolved and loaded, the task loop at `0x0024FA50` in `sub_0024FA04` fully advanced, unblocking the engine main loop (`sub_0026D228`) rendering 73+ frames.

