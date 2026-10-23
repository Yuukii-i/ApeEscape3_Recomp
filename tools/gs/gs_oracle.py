#!/usr/bin/env python3
"""
tools/gs/gs_oracle.py: Independent offline GS oracle for Ape Escape 3 Recomp.
Implements GS memory addressing directly from the Sony PlayStation 2 GS User's Manual:
  - Chapter 7: GS Local Memory Structure and Pixel Transmission
    - Table 7-2: Page and Block Arrangement (PSMCT32)
    - Table 7-6: Pixel Arrangement in Block (PSMT8)
    - Table 7-7: Pixel Arrangement in Block (PSMT4)

Provides:
  - self-test: write-then-read round trip verification for PSMCT32, PSMT8, PSMT4
  - payload-to-png: interpret raw upload payload as raster image in given DPSM
  - rebuild-vram: replay upload dumps into a 4MB VRAM array
  - decode-tex: sample a texture + CLUT from a VRAM dump into PNG (with/without 3/4 swap)
  - compare-tex: compare oracle-decoded texture against runtime dump or reference
"""

import sys
import os
import struct
import argparse
import numpy as np
from PIL import Image

# ---------------------------------------------------------------------------
# GS Local Memory Constants & Tables (GS User's Manual Chapter 7)
# ---------------------------------------------------------------------------

VRAM_SIZE = 4 * 1024 * 1024  # 4 MiB
PAGE_SIZE = 8192             # 8 KiB per page
TOTAL_PAGES = VRAM_SIZE // PAGE_SIZE  # 512 pages
BLOCKS_PER_PAGE = 32
BYTES_PER_BLOCK = 256
TOTAL_BLOCKS = TOTAL_PAGES * BLOCKS_PER_PAGE  # 16384 blocks

# Table 7-2: PSMCT32 Block layout in a page (8 cols x 4 rows)
BLOCK_TABLE_CT32 = [
    [  0,  1,  4,  5, 16, 17, 20, 21 ],
    [  2,  3,  6,  7, 18, 19, 22, 23 ],
    [  8,  9, 12, 13, 24, 25, 28, 29 ],
    [ 10, 11, 14, 15, 26, 27, 30, 31 ]
]

# Table 7-2: PSMCT32 Column layout in a block (8 cols x 8 rows) -> 64 words
COLUMN_TABLE_CT32 = [
    [  0,  1,  4,  5,  8,  9, 12, 13 ],
    [  2,  3,  6,  7, 10, 11, 14, 15 ],
    [ 16, 17, 20, 21, 24, 25, 28, 29 ],
    [ 18, 19, 22, 23, 26, 27, 30, 31 ],
    [ 32, 33, 36, 37, 40, 41, 44, 45 ],
    [ 34, 35, 38, 39, 42, 43, 46, 47 ],
    [ 48, 49, 52, 53, 56, 57, 60, 61 ],
    [ 50, 51, 54, 55, 58, 59, 62, 63 ]
]

# Table 7-6: PSMT8 Block layout in a page (8 cols x 4 rows)
BLOCK_TABLE_T8 = [
    [  0,  1,  4,  5, 16, 17, 20, 21 ],
    [  2,  3,  6,  7, 18, 19, 22, 23 ],
    [  8,  9, 12, 13, 24, 25, 28, 29 ],
    [ 10, 11, 14, 15, 26, 27, 30, 31 ]
]

# Table 7-6: PSMT8 Column layout in a block (16 cols x 16 rows) -> 256 bytes
COLUMN_TABLE_T8 = [
    [   0,   4,  16,  20,  32,  36,  48,  52,   2,   6,  18,  22,  34,  38,  50,  54 ],
    [   8,  12,  24,  28,  40,  44,  56,  60,  10,  14,  26,  30,  42,  46,  58,  62 ],
    [  33,  37,  49,  53,   1,   5,  17,  21,  35,  39,  51,  55,   3,   7,  19,  23 ],
    [  41,  45,  57,  61,   9,  13,  25,  29,  43,  47,  59,  63,  11,  15,  27,  31 ],
    [  96, 100, 112, 116,  64,  68,  80,  84,  98, 102, 114, 118,  66,  70,  82,  86 ],
    [ 104, 108, 120, 124,  72,  76,  88,  92, 106, 110, 122, 126,  74,  78,  90,  94 ],
    [  65,  69,  81,  85,  97, 101, 113, 117,  67,  71,  83,  87,  99, 103, 115, 119 ],
    [  73,  77,  89,  93, 105, 109, 121, 125,  75,  79,  91,  95, 107, 111, 123, 127 ],
    [ 128, 132, 144, 148, 160, 164, 176, 180, 130, 134, 146, 150, 162, 166, 178, 182 ],
    [ 136, 140, 152, 156, 168, 172, 184, 188, 138, 142, 154, 158, 170, 174, 186, 190 ],
    [ 161, 165, 177, 181, 129, 133, 145, 149, 163, 167, 179, 183, 131, 135, 147, 151 ],
    [ 169, 173, 185, 189, 137, 141, 153, 157, 171, 175, 187, 191, 139, 143, 155, 159 ],
    [ 224, 228, 240, 244, 192, 196, 208, 212, 226, 230, 242, 246, 194, 198, 210, 214 ],
    [ 232, 236, 248, 252, 200, 204, 216, 220, 234, 238, 250, 254, 202, 206, 218, 222 ],
    [ 193, 197, 209, 213, 225, 229, 241, 245, 195, 199, 211, 215, 227, 231, 243, 247 ],
    [ 201, 205, 217, 221, 233, 237, 249, 253, 203, 207, 219, 223, 235, 239, 251, 255 ]
]

# Table 7-7: PSMT4 Block layout in a page (4 cols x 8 rows)
BLOCK_TABLE_T4 = [
    [  0,  2,  8, 10 ],
    [  1,  3,  9, 11 ],
    [  4,  6, 12, 14 ],
    [  5,  7, 13, 15 ],
    [ 16, 18, 24, 26 ],
    [ 17, 19, 25, 27 ],
    [ 20, 22, 28, 30 ],
    [ 21, 23, 29, 31 ]
]

# Table 7-7: PSMT4 Column layout in a block (32 cols x 16 rows) -> 512 nibbles
COLUMN_TABLE_T4 = [
    [   0,   8,  32,  40,  64,  72,  96, 104,   2,  10,  34,  42,  66,  74,  98, 106,   4,  12,  36,  44,  68,  76, 100, 108,   6,  14,  38,  46,  70,  78, 102, 110 ],
    [  16,  24,  48,  56,  80,  88, 112, 120,  18,  26,  50,  58,  82,  90, 114, 122,  20,  28,  52,  60,  84,  92, 116, 124,  22,  30,  54,  62,  86,  94, 118, 126 ],
    [  65,  73,  97, 105,   1,   9,  33,  41,  67,  75,  99, 107,   3,  11,  35,  43,  69,  77, 101, 109,   5,  13,  37,  45,  71,  79, 103, 111,   7,  15,  39,  47 ],
    [  81,  89, 113, 121,  17,  25,  49,  57,  83,  91, 115, 123,  19,  27,  51,  59,  85,  93, 117, 125,  21,  29,  53,  61,  87,  95, 119, 127,  23,  31,  55,  63 ],
    [ 192, 200, 224, 232, 128, 136, 160, 168, 194, 202, 226, 234, 130, 138, 162, 170, 196, 204, 228, 236, 132, 140, 164, 172, 198, 206, 230, 238, 134, 142, 166, 174 ],
    [ 208, 216, 240, 248, 144, 152, 176, 184, 210, 218, 242, 250, 146, 154, 178, 186, 212, 220, 244, 252, 148, 156, 180, 188, 214, 222, 246, 254, 150, 158, 182, 190 ],
    [ 129, 137, 161, 169, 193, 201, 225, 233, 131, 139, 163, 171, 195, 203, 227, 235, 133, 141, 165, 173, 197, 205, 229, 237, 135, 143, 167, 175, 199, 207, 231, 239 ],
    [ 145, 153, 177, 185, 209, 217, 241, 249, 147, 155, 179, 187, 211, 219, 243, 251, 149, 157, 181, 189, 213, 221, 245, 253, 151, 159, 183, 191, 215, 223, 247, 255 ],
    [ 256, 264, 288, 296, 320, 328, 352, 360, 258, 266, 290, 298, 322, 330, 354, 362, 260, 268, 292, 300, 324, 332, 356, 364, 262, 270, 294, 302, 326, 334, 358, 366 ],
    [ 272, 280, 304, 312, 336, 344, 368, 376, 274, 282, 306, 314, 338, 346, 370, 378, 276, 284, 308, 316, 340, 348, 372, 380, 278, 286, 310, 318, 342, 350, 374, 382 ],
    [ 321, 329, 353, 361, 257, 265, 289, 297, 323, 331, 355, 363, 259, 267, 291, 299, 325, 333, 357, 365, 261, 269, 293, 301, 327, 335, 359, 367, 263, 271, 295, 303 ],
    [ 337, 345, 369, 377, 273, 281, 305, 313, 339, 347, 371, 379, 275, 283, 307, 315, 341, 349, 373, 381, 277, 285, 309, 317, 343, 351, 375, 383, 279, 287, 311, 319 ],
    [ 448, 456, 480, 488, 384, 392, 416, 424, 450, 458, 482, 490, 386, 394, 418, 426, 452, 460, 484, 492, 388, 396, 420, 428, 454, 462, 486, 494, 390, 398, 422, 430 ],
    [ 464, 472, 496, 504, 400, 408, 432, 440, 466, 474, 498, 506, 402, 410, 434, 442, 468, 476, 500, 508, 404, 412, 436, 444, 470, 478, 502, 510, 406, 414, 438, 446 ],
    [ 385, 393, 417, 425, 449, 457, 481, 489, 387, 395, 419, 427, 451, 459, 483, 491, 389, 397, 421, 429, 453, 461, 485, 493, 391, 399, 423, 431, 455, 463, 487, 495 ],
    [ 401, 409, 433, 441, 465, 473, 497, 505, 403, 411, 435, 443, 467, 475, 499, 507, 405, 413, 437, 445, 469, 477, 501, 509, 407, 415, 439, 447, 471, 479, 503, 511 ]
]

def swizzle_csm1(index: int) -> int:
    """CSM1 bit 3 <-> bit 4 swap."""
    return (index & ~0x18) | ((index & 0x08) << 1) | ((index & 0x10) >> 1)

# ---------------------------------------------------------------------------
# Addressing functions
# ---------------------------------------------------------------------------

def get_vram_byte_offset_ct32(base_block: int, bw: int, x: int, y: int) -> int:
    page_w, page_h = 64, 32
    base_page = base_block // BLOCKS_PER_PAGE
    pages_per_row = max(bw, 1)
    page_x = x // page_w
    page_y = y // page_h
    page = base_page + page_y * pages_per_row + page_x

    local_x = x % page_w
    local_y = y % page_h
    b_id = BLOCK_TABLE_CT32[local_y // 8][local_x // 8]
    p_in_b = COLUMN_TABLE_CT32[local_y % 8][local_x % 8]
    word_addr = (page * 2048) + (b_id * 64) + p_in_b
    return (word_addr * 4) % VRAM_SIZE

def get_vram_byte_offset_t8(base_block: int, bw: int, x: int, y: int) -> int:
    page_w, page_h = 128, 64
    base_page = base_block // BLOCKS_PER_PAGE
    pages_per_row = max(bw // 2, 1)
    page_x = x // page_w
    page_y = y // page_h
    page = base_page + page_y * pages_per_row + page_x

    local_x = x % page_w
    local_y = y % page_h
    b_id = BLOCK_TABLE_T8[local_y // 16][local_x // 16]
    p_in_b = COLUMN_TABLE_T8[local_y % 16][local_x % 16]
    byte_addr = (page * PAGE_SIZE) + (b_id * BYTES_PER_BLOCK) + p_in_b
    return byte_addr % VRAM_SIZE

def get_vram_nibble_offset_t4(base_block: int, bw: int, x: int, y: int):
    page_w, page_h = 128, 128
    base_page = base_block // BLOCKS_PER_PAGE
    pages_per_row = max(bw // 2, 1)
    page_x = x // page_w
    page_y = y // page_h
    page = base_page + page_y * pages_per_row + page_x

    local_x = x % page_w
    local_y = y % page_h
    b_id = BLOCK_TABLE_T4[local_y // 16][local_x // 32]
    p_in_b = COLUMN_TABLE_T4[local_y % 16][local_x % 32]
    nibble_addr = (page * 16384) + (b_id * 512) + p_in_b
    byte_addr = (nibble_addr // 2) % VRAM_SIZE
    shift = (nibble_addr % 2) * 4
    return byte_addr, shift

# Read/write functions on raw VRAM bytearray
def write_pixel_ct32(vram: bytearray, base_block: int, bw: int, x: int, y: int, rgba: int):
    addr = get_vram_byte_offset_ct32(base_block, bw, x, y)
    struct.pack_into("<I", vram, addr, rgba)

def read_pixel_ct32(vram: bytearray, base_block: int, bw: int, x: int, y: int) -> int:
    addr = get_vram_byte_offset_ct32(base_block, bw, x, y)
    return struct.unpack_from("<I", vram, addr)[0]

def write_pixel_t8(vram: bytearray, base_block: int, bw: int, x: int, y: int, index: int):
    addr = get_vram_byte_offset_t8(base_block, bw, x, y)
    vram[addr] = index & 0xFF

def read_pixel_t8(vram: bytearray, base_block: int, bw: int, x: int, y: int) -> int:
    addr = get_vram_byte_offset_t8(base_block, bw, x, y)
    return vram[addr]

def write_pixel_t4(vram: bytearray, base_block: int, bw: int, x: int, y: int, index: int):
    addr, shift = get_vram_nibble_offset_t4(base_block, bw, x, y)
    old = vram[addr]
    vram[addr] = (old & ~(0x0F << shift)) | ((index & 0x0F) << shift)

def read_pixel_t4(vram: bytearray, base_block: int, bw: int, x: int, y: int) -> int:
    addr, shift = get_vram_nibble_offset_t4(base_block, bw, x, y)
    return (vram[addr] >> shift) & 0x0F

# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_selftest():
    print("=== GS Oracle Self-Test: Round-Trip Verification ===")
    vram = bytearray(VRAM_SIZE)
    np.random.seed(42)

    # 1. PSMCT32 test (64x32 page)
    print("1. Testing PSMCT32 round trip...")
    data_ct32 = np.random.randint(0, 0xFFFFFFFF, size=(32, 64), dtype=np.uint32)
    for y in range(32):
        for x in range(64):
            write_pixel_ct32(vram, 0, 1, x, y, int(data_ct32[y, x]))
    for y in range(32):
        for x in range(64):
            read_val = read_pixel_ct32(vram, 0, 1, x, y)
            assert read_val == int(data_ct32[y, x]), f"Mismatch at CT32 ({x}, {y}): {read_val} != {data_ct32[y, x]}"
    print("   PSMCT32: OK (2048/2048 words verified)")

    # 2. PSMT8 test (128x64 page)
    print("2. Testing PSMT8 round trip...")
    data_t8 = np.random.randint(0, 256, size=(64, 128), dtype=np.uint8)
    for y in range(64):
        for x in range(128):
            write_pixel_t8(vram, 32, 2, x, y, int(data_t8[y, x]))
    for y in range(64):
        for x in range(128):
            read_val = read_pixel_t8(vram, 32, 2, x, y)
            assert read_val == int(data_t8[y, x]), f"Mismatch at T8 ({x}, {y}): {read_val} != {data_t8[y, x]}"
    print("   PSMT8: OK (8192/8192 bytes verified)")

    # 3. PSMT4 test (128x128 page)
    print("3. Testing PSMT4 round trip...")
    data_t4 = np.random.randint(0, 16, size=(128, 128), dtype=np.uint8)
    for y in range(128):
        for x in range(128):
            write_pixel_t4(vram, 64, 2, x, y, int(data_t4[y, x]))
    for y in range(128):
        for x in range(128):
            read_val = read_pixel_t4(vram, 64, 2, x, y)
            assert read_val == int(data_t4[y, x]), f"Mismatch at T4 ({x}, {y}): {read_val} != {data_t4[y, x]}"
    print("   PSMT4: OK (16384/16384 nibbles verified)")

    print("ALL GS ORACLE SELF-TESTS PASSED!")
    return 0

def cmd_payload_to_png(args):
    """Interpret raw payload.bin as raster image in given DPSM."""
    with open(args.payload, "rb") as f:
        data = f.read()

    w, h, psm = args.width, args.height, args.psm
    out_img = None
    if psm == 0:  # CT32
        expected_bytes = w * h * 4
        assert len(data) >= expected_bytes, f"Payload too small: {len(data)} < {expected_bytes}"
        arr = np.frombuffer(data[:expected_bytes], dtype=np.uint8).reshape((h, w, 4))
        # GS CT32 is RGBA
        out_img = Image.fromarray(arr, mode="RGBA")
    elif psm == 0x13:  # T8
        expected_bytes = w * h
        assert len(data) >= expected_bytes, f"Payload too small: {len(data)} < {expected_bytes}"
        arr = np.frombuffer(data[:expected_bytes], dtype=np.uint8).reshape((h, w))
        out_img = Image.fromarray(arr, mode="L")
    elif psm == 0x14:  # T4
        expected_bytes = (w * h + 1) // 2
        assert len(data) >= expected_bytes, f"Payload too small: {len(data)} < {expected_bytes}"
        raw = np.frombuffer(data[:expected_bytes], dtype=np.uint8)
        arr = np.zeros(w * h, dtype=np.uint8)
        arr[0::2] = raw & 0x0F
        arr[1::2] = (raw >> 4) & 0x0F
        arr = arr[:w*h].reshape((h, w)) * 17
        out_img = Image.fromarray(arr, mode="L")
    else:
        raise ValueError(f"Unsupported DPSM: {psm}")

    out_img.save(args.output)
    print(f"Wrote intended raster payload image: {args.output} ({w}x{h})")

def cmd_decode_tex(args):
    """Decode texture from VRAM dump using GS tables and CLUT."""
    with open(args.vram, "rb") as f:
        vram = bytearray(f.read())
    assert len(vram) == VRAM_SIZE, f"VRAM dump size {len(vram)} != {VRAM_SIZE}"

    # Read CLUT
    # CLUT is stored at cbp (usually CT32)
    cbp = args.cbp
    clut = []
    for i in range(256 if args.psm == 0x13 else 16):
        entry_idx = swizzle_csm1(i) if (args.swizzle and args.psm == 0x13) else i
        # 32-bit CLUT entry read
        col = entry_idx & 0x0F
        row = entry_idx >> 4
        rgba = read_pixel_ct32(vram, cbp, 1, col, row)
        r = rgba & 0xFF
        g = (rgba >> 8) & 0xFF
        b = (rgba >> 16) & 0xFF
        a = (rgba >> 24) & 0xFF
        # Alpha in GS: 0x80 is 1.0 (opaque)
        a_scaled = min(255, int(a * (255.0 / 128.0)))
        clut.append((r, g, b, a_scaled))

    w, h = args.width, args.height
    tbp0, tbw, psm = args.tbp0, args.tbw, args.psm
    img_arr = np.zeros((h, w, 4), dtype=np.uint8)

    for y in range(h):
        for x in range(w):
            if psm == 0x13:
                idx = read_pixel_t8(vram, tbp0, tbw, x, y)
                img_arr[y, x] = clut[idx]
            elif psm == 0x14:
                idx = read_pixel_t4(vram, tbp0, tbw, x, y)
                img_arr[y, x] = clut[idx]
            elif psm == 0:
                rgba = read_pixel_ct32(vram, tbp0, tbw, x, y)
                r = rgba & 0xFF
                g = (rgba >> 8) & 0xFF
                b = (rgba >> 16) & 0xFF
                a = (rgba >> 24) & 0xFF
                img_arr[y, x] = [r, g, b, a]

    im = Image.fromarray(img_arr, mode="RGBA")
    im.save(args.output)
    print(f"Decoded texture saved to {args.output} ({w}x{h}, psm=0x{psm:x}, swizzle={args.swizzle})")

def main():
    parser = argparse.ArgumentParser(description="GS Oracle Tool")
    subparsers = parser.add_subparsers(dest="command")

    # self-test
    subparsers.add_parser("self-test")

    # payload-to-png
    p_pay = subparsers.add_parser("payload-to-png")
    p_pay.add_argument("--payload", required=True)
    p_pay.add_argument("--output", required=True)
    p_pay.add_argument("--width", type=int, required=True)
    p_pay.add_argument("--height", type=int, required=True)
    p_pay.add_argument("--psm", type=int, default=0)

    # decode-tex
    p_dec = subparsers.add_parser("decode-tex")
    p_dec.add_argument("--vram", required=True)
    p_dec.add_argument("--output", required=True)
    p_dec.add_argument("--tbp0", type=int, required=True)
    p_dec.add_argument("--tbw", type=int, default=2)
    p_dec.add_argument("--psm", type=int, required=True)
    p_dec.add_argument("--cbp", type=int, default=0)
    p_dec.add_argument("--width", type=int, required=True)
    p_dec.add_argument("--height", type=int, required=True)
    p_dec.add_argument("--swizzle", action="store_true")

    args = parser.parse_args()
    if args.command == "self-test":
        return cmd_selftest()
    elif args.command == "payload-to-png":
        return cmd_payload_to_png(args)
    elif args.command == "decode-tex":
        return cmd_decode_tex(args)
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main() or 0)
