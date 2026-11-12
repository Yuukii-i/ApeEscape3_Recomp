#!/usr/bin/env python3
"""Disassemble the VU1 code image(s) stored in a corpus file (CODE chunks) to a text listing.
Usage: python -I tools/vu1gen/dump_image.py logs/vu1corpus_shop.bin out.txt [maxpc_hex]"""
import struct, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vudis

f = open(sys.argv[1], 'rb')
out = open(sys.argv[2], 'w')
maxpc = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0x4000
while True:
    h = f.read(8)
    if len(h) < 8:
        break
    tag, n = struct.unpack('<II', h)
    p = f.read(n)
    if struct.pack('<I', tag) != b'CODE':
        continue
    # CODE payload: optional header before the 16 KB image; take the last 16384 bytes
    img = p[-16384:]
    out.write('== CODE chunk, payload %d bytes, header %s\n' % (n, p[:max(0, n - 16384)][:32].hex()))
    for pc in range(0, min(maxpc, 0x4000), 8):
        lo, up = struct.unpack_from('<II', img, pc)
        try:
            u = vudis.upper(up)
        except Exception as e:
            u = '?upper %08x' % up
        try:
            l = vudis.lower(lo)
        except Exception as e:
            l = '?lower %08x' % lo
        out.write('%04X: %08x %08x  %-34s | %s\n' % (pc, up, lo, u, l))
    break
out.close()
