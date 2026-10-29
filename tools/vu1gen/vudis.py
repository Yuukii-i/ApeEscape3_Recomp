#!/usr/bin/env python3
"""Tiny VU1 disassembler for the hot-block work (names + fields only)."""
import sys

BC = 'xyzw'
UP = {}
for i, n in enumerate(['ADD', 'SUB', 'MADD', 'MSUB', 'MAX', 'MINI']):
    for b in range(4):
        UP[i * 4 + b] = n + BC[b]
for b in range(4):
    UP[0x18 + b] = 'MUL' + BC[b]
UP.update({0x1C: 'MULq', 0x1D: 'MAXi', 0x1E: 'MULi', 0x1F: 'MINIi', 0x20: 'ADDq', 0x21: 'MADDq', 0x22: 'ADDi', 0x23: 'MADDi',
           0x24: 'SUBq', 0x25: 'MSUBq', 0x26: 'SUBi', 0x27: 'MSUBi', 0x28: 'ADD', 0x29: 'MADD', 0x2A: 'MUL', 0x2B: 'MAX',
           0x2C: 'SUB', 0x2D: 'MSUB', 0x2E: 'OPMSUB', 0x2F: 'MINI'})
SP = {}
for i, n in enumerate(['ADDA', 'SUBA', 'MADDA', 'MSUBA']):
    for b in range(4):
        SP[i * 4 + b] = n + BC[b]
for k, n in enumerate(['ITOF0', 'ITOF4', 'ITOF12', 'ITOF15', 'FTOI0', 'FTOI4', 'FTOI12', 'FTOI15']):
    SP[0x10 + k] = n
for b in range(4):
    SP[0x18 + b] = 'MULA' + BC[b]
SP.update({0x1C: 'MULAq', 0x1D: 'ABS', 0x1E: 'MULAi', 0x1F: 'CLIP', 0x20: 'ADDAq', 0x21: 'MADDAq', 0x22: 'ADDAi', 0x23: 'MADDAi',
           0x24: 'SUBAq', 0x25: 'MSUBAq', 0x26: 'SUBAi', 0x27: 'MSUBAi', 0x28: 'ADDA', 0x29: 'MADDA', 0x2A: 'MULA', 0x2C: 'SUBA',
           0x2D: 'MSUBA', 0x2E: 'OPMULA', 0x2F: 'NOP'})


def dest_s(d):
    return ''.join(c for c, bit in zip('xyzw', (8, 4, 2, 1)) if d & bit) or '-'


def upper(u):
    op = u & 0x3F
    dest = (u >> 21) & 15
    ft = (u >> 16) & 31
    fs = (u >> 11) & 31
    fd = (u >> 6) & 31
    if op >= 0x3C:
        e = (u & 3) | ((u >> 4) & 0x7C)
        n = SP.get(e, 'SP?%02X' % e)
        if n == 'NOP':
            return 'NOP'
        return '%s.%s ACC, vf%d, vf%d' % (n, dest_s(dest), fs, ft)
    n = UP.get(op, 'UP?%02X' % op)
    return '%s.%s vf%d, vf%d, vf%d' % (n, dest_s(dest), fd, fs, ft)


LOW = {0x00: 'LQ', 0x01: 'SQ', 0x04: 'ILW', 0x05: 'ISW', 0x08: 'IADDIU', 0x09: 'ISUBIU', 0x10: 'FCEQ', 0x11: 'FCSET', 0x12: 'FCAND', 0x13: 'FCOR',
       0x14: 'FSEQ', 0x15: 'FSSET', 0x16: 'FSAND', 0x17: 'FSOR', 0x18: 'FMEQ', 0x1A: 'FMAND', 0x1B: 'FMOR', 0x1C: 'FCGET',
       0x20: 'B', 0x21: 'BAL', 0x24: 'JR', 0x25: 'JALR', 0x28: 'IBEQ', 0x29: 'IBNE', 0x2C: 'IBLTZ', 0x2D: 'IBGTZ', 0x2E: 'IBLEZ', 0x2F: 'IBGEZ'}
L2 = {0x30: 'IADD', 0x31: 'ISUB', 0x32: 'IADDI', 0x34: 'IAND', 0x35: 'IOR'}
L2S = {0x30: 'MOVE', 0x31: 'MR32', 0x34: 'LQI', 0x35: 'SQI', 0x36: 'LQD', 0x37: 'SQD', 0x38: 'DIV', 0x39: 'SQRT', 0x3A: 'RSQRT', 0x3B: 'WAITQ',
       0x3C: 'MTIR', 0x3D: 'MFIR', 0x3E: 'ILWR', 0x3F: 'ISWR', 0x40: 'RNEXT', 0x41: 'RGET', 0x42: 'RINIT', 0x43: 'RXOR', 0x64: 'MFP', 0x68: 'XTOP',
       0x69: 'XITOP', 0x6C: 'XGKICK', 0x70: 'ESADD', 0x71: 'ERSADD', 0x72: 'ELENG', 0x73: 'ERLENG', 0x74: 'EATANxy', 0x75: 'EATANxz',
       0x76: 'ESUM', 0x78: 'ESQRT', 0x79: 'ERSQRT', 0x7A: 'ERCPR', 0x7B: 'ESIN', 0x7C: 'EATAN', 0x7D: 'EEXP', 0x7E: 'ERLENG'}


def lower(lo):
    op = (lo >> 25) & 0x7F
    dest = (lo >> 21) & 15
    ft = (lo >> 16) & 31
    fs = (lo >> 11) & 31
    fd = (lo >> 6) & 31
    imm11 = lo & 0x7FF
    if imm11 & 0x400:
        imm11 -= 0x800
    imm15 = (lo & 0x7FF) | ((lo >> 10) & 0x7800)
    if op == 0x00:
        return 'LQ.%s vf%d, %d(vi%d)' % (dest_s(dest), ft, imm11, fs)
    if op == 0x01:
        return 'SQ.%s vf%d, %d(vi%d)' % (dest_s(dest), fs, imm11, ft)
    if op == 0x04:
        return 'ILW.%s vi%d, %d(vi%d)' % (dest_s(dest), ft, imm11, fs)
    if op == 0x05:
        return 'ISW.%s vi%d, %d(vi%d)' % (dest_s(dest), ft, imm11, fs)
    if op == 0x08:
        return 'IADDIU vi%d, vi%d, %d' % (ft, fs, imm15)
    if op == 0x09:
        return 'ISUBIU vi%d, vi%d, %d' % (ft, fs, imm15)
    if op in (0x28, 0x29, 0x2C, 0x2D, 0x2E, 0x2F):
        return '%s vi%d, vi%d, %d' % (LOW[op], ft, fs, imm11)
    if op == 0x20 or op == 0x21:
        return '%s %d' % (LOW[op], imm11)
    if op in LOW:
        return '%s ...' % LOW[op]
    if op == 0x40:
        o6 = lo & 0x3F
        if o6 >= 0x3C:
            e = (lo & 3) | ((lo >> 4) & 0x7C)
            n = L2S.get(e, 'LS?%02X' % e)
            return '%s.%s ft=%d fs=%d' % (n, dest_s(dest), ft, fs)
        n = L2.get(o6, 'L2?%02X' % o6)
        return '%s vi%d, vi%d, vi%d' % (n, fd, fs, ft)
    return 'L?%02X' % op


if __name__ == '__main__':
    pairs = {}
    for l in open(sys.argv[1]):
        if not l.startswith('P '):
            continue
        t = l.split()
        pairs[int(t[1], 16)] = (int(t[2], 16), int(t[3], 16), dict(x.split('=', 1) for x in t[4:] if '=' in x))
    for a in sys.argv[2:]:
        pc, n = a.split(':')
        pc = int(pc, 16)
        n = int(n)
        for k in range(n):
            u, lo, kv = pairs[pc + 8 * k]
            print('%04X  %-34s | %s' % (pc + 8 * k, upper(u), 'IMM %08X' % lo if kv['i'] == '1' else lower(lo)))
        print()
