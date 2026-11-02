#!/usr/bin/env python3
"""Pair executors for the pcs where a variant microcode image differs from the main image (PERF-VAR).

Usage: python tools/vu1gen/gen_vu1_native_t.py <variant hash> <tag>      e.g.  4020410124328442 t4020
Reads   logs/vuusage_u1_<variant>.txt and logs/vuusage_u1_86503d3905e35276.txt
Writes  generated/vu1_native_exec_<tag>.cpp: functions vuT_<pc>(...) for every differing, executable pair + the table
        int (*const kVu1Step_<tag>[2048])(VU1Interpreter &, VuNativeCtx &)   (nullptr = interpreter)
"""
import sys

import gen_vu1_native as g

MAIN = "86503d3905e35276"
variant, tag = sys.argv[1], sys.argv[2]
UC = g.UC
UC['step'] = 'vuT_' + tag
base = g.load_pairs('logs/vuusage_u1_%s.txt' % MAIN)
var = g.load_pairs('logs/vuusage_u1_%s.txt' % variant)


def rec(p):
    return p
diff = [pc for pc in sorted(var) if pc not in base or base[pc] != var[pc]]
native = []
for pc in diff:
    p = var[pc]
    if p['L']['rsv'] or p['U']['rsv'] or (p['upper'] == 0 and p['lower'] == 0):
        continue
    native.append(pc)
src = 'logs/vuusage_u1_%s.txt' % variant
out = g.OUT_DIR + 'vu1_native_exec_%s.cpp' % tag
with open(out, 'w', newline='\n') as f:
    f.write(g.FILE_HEAD % {'src': src})
    for pc in native:
        f.write('\n'.join(g.emit_pair(pc, var[pc])))
        f.write('\n')
    f.write('\nextern int (*const kVu1Step_%s[2048])(VU1Interpreter &, VuNativeCtx &);\n' % tag)
    f.write('int (*const kVu1Step_%s[2048])(VU1Interpreter &, VuNativeCtx &) = {\n' % tag)
    nset = set(native)
    for i in range(2048):
        f.write('  %s,\n' % ('%s_%04X' % (UC['step'], i * 8) if i * 8 in nset else 'nullptr'))
    f.write('};\n')
print('variant %s: %d differing pairs, %d native executors -> %s' % (variant, len(diff), len(native), out))
