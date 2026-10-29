#!/usr/bin/env python3
"""VU1 native pair executor generator (stage 1).

Input : logs/vuusage_u1_<hash>.txt (dumped by the interpreter, PROBE-GC/HC): per-pair scheduler usage tables.
Output: PS2Recomp/ps2xRuntime/src/lib/vu/generated/vu1_native_exec_<k>.cpp   (plain functions, literal constants)
        PS2Recomp/ps2xRuntime/src/lib/vu/generated/vu1_native_dispatch.cpp  (pc -> function table + vu1NativeRun)

Every function is the production path of one interpreter loop iteration (no probes) with the pair's decode values
partially evaluated: it uses the interpreter's real scheduler state (ready arrays, pipelines) through direct data access
and calls back into the interpreter (via VuNativeOps) for the pipelined queues and the generic op executors.
The A/B verifier (PS2X_VU1_VERIFY=1: native vs interpreter reference path) must report 0 mismatches.
"""
import os
import re
import sys

OUT_DIR = 'PS2Recomp/ps2xRuntime/src/lib/vu/generated/'
CHUNKS = 4

# PERF-IM: unit parameters. VU1 main image by default; a logs/vuusage_u0_* dump generates the VU0 executors instead.
UC = {'unit': 1, 'name': 'vu1', 'Name': 'Vu1', 'step': 'vuS', 'pclim': 0x4000, 'pcmask': 0x3FFF, 'slots': 2048, 'chunks': CHUNKS, 'hot': 'hot'}


def configure(src):
    if '_u0_' in os.path.basename(src):
        UC.update(unit=0, name='vu0', Name='Vu0', step='vu0S', pclim=0x1000, pcmask=0x0FFF, slots=512, chunks=1, hot='hot0')


def lane(c):
    return 1 << (3 - c)


def kv(chunk):
    out = {}
    for t in chunk.split():
        if '=' in t:
            k, v = t.split('=', 1)
            out[k] = v
    return out


def parse_usage(d):
    r = [int(x) for x in d['r'].split(':')]
    w = [int(x) for x in d['w'].split(':')]
    return {
        'rc': r[0], 'reads': [(r[1], r[2]), (r[3], r[4])][:r[0]],
        'wreg': w[0], 'wlanes': w[1],
        'vir': int(d['vir'], 16), 'viw': int(d['viw'], 16),
        'ar': int(d['ar']), 'aw': int(d['aw']),
        'lat': int(d['lat']), 'vfl': int(d['vfl']), 'vil': int(d['vil']),
        'pipe': int(d['pipe']), 'wq': int(d['wq']), 'wp': int(d['wp']),
        'dnb': int(d['dnb']), 'rsv': int(d['rsv']),
    }


def emit_pair(pc, p):
    L, U = p['L'], p['U']
    o = []
    A = o.append
    A('int %s_%04X(VU1Interpreter &vu, VuNativeCtx &c)' % (UC['step'], pc))
    A('{')
    A('    const VuNativeOps &op = *c.ops;')
    A('    if (vu.m_cycle >= *c.nextReady) op.commit(vu); // PERF-IC: same early-out as commitReadyPipelines')
    A('    ++c.instrs;')

    # ---- readiness (calculatePairReadyCycle, partially evaluated) ----
    vf = []
    for us in (U, L):
        for reg, lanes in us['reads']:
            for comp in range(4):
                if lanes & lane(comp) and reg != 0 and (reg, comp) not in vf:
                    vf.append((reg, comp))
    vi = sorted({r for r in range(1, 16) if (U['vir'] | L['vir']) & (1 << r)})
    acc = [c for c in range(4) if (U['ar'] | L['ar']) & lane(c)]
    extra = []
    if L['pipe'] == 3 or L['wq']:
        extra.append('    if (vu.m_fdiv.valid) ready = (std::max)(ready, vu.m_fdiv.readyCycle);')
    if L['pipe'] == 4:
        extra.append('    ready = (std::max)(ready, vu.m_efuResourceReady);')
    if L['wp']:
        extra.append('    for (const auto &e : vu.m_efu) if (e.valid) ready = (std::max)(ready, e.readyCycle);')
    if L['pipe'] == 7:
        extra.append('    if (vu.m_xgkick.active) ready = (std::max)(ready, vu.m_cycle + 1u);')
    if vf or vi or acc or extra:
        A('    for (;;)')
        A('    {')
        A('        uint64_t ready = vu.m_cycle;')
        for reg, comp in vf:
            A('        ready = (std::max)(ready, vu.m_vfReady[%d][%d]);' % (reg, comp))
        for r in vi:
            A('        ready = (std::max)(ready, vu.m_viReady[%d]);' % r)
        for cmp_ in acc:
            A('        ready = (std::max)(ready, vu.m_accReady[%d]);' % cmp_)
        for e in extra:
            A('    ' + e)
        A('        if (ready <= vu.m_cycle) break;')
        A('        if (ready >= c.budgetEnd) { op.advanceTo(vu, c.budgetEnd); break; }')
        A('        op.advanceTo(vu, ready);')
        A('    }')
    A('    if (vu.m_cycle >= c.budgetEnd) return 1;')

    # ---- written vi / old copies ----
    viw_mask = L['viw'] & 0xFFFE
    written = 0
    if viw_mask:
        written = (viw_mask & -viw_mask).bit_length() - 1
        if L['dnb']:
            A('    const int32_t oldVi = vu.m_state.vi[%d];' % written)
    has_up = U['wreg'] != 0
    has_low = L['wreg'] != 0 and p['supp'] != L['wreg']
    has_dlow = has_low and (not has_up or L['wreg'] != U['wreg'])
    # PERF-IC: since PERF-HT vf/vi/acc writes are applied at issue, so the old-copy / restore / queue dance is a no-op except for the
    # quirk where lower and upper write the same register (the interpreter requeues only the upper lanes of the final value).
    same_reg_quirk = has_up and L['wreg'] != 0 and L['wreg'] == U['wreg']
    if same_reg_quirk:
        A('    float oldUp[4]; std::memcpy(oldUp, vu.m_state.vf[%d], 16);' % U['wreg'])

    # ---- execute ----
    def upper_stmt(u):
        o = u & 0x3F
        e = o
        if o >= 0x3C:
            e = (u & 3) | ((u >> 4) & 0x7C)
            if e in (0x2F, 0x30):
                return '    vu.m_currentUpperInstruction = 0x%08xu; // NOP' % u
        return '    op.execUpper(vu, 0x%08xu);' % u

    if p['i']:
        A(upper_stmt(p['upper']))
        A('    { const uint32_t lb = 0x%08xu; float imm; std::memcpy(&imm, &lb, 4); vu.m_state.i = vuNormalizeOperand(imm); }' % p['lower'])
    elif p['shadow']:
        sh = p['shadow']
        A('    { float oldVf[4], upVf[4];')
        A('      std::memcpy(oldVf, vu.m_state.vf[%d], 16);' % sh)
        A('  ' + upper_stmt(p['upper']))
        A('      std::memcpy(upVf, vu.m_state.vf[%d], 16);' % sh)
        A('      std::memcpy(vu.m_state.vf[%d], oldVf, 16);' % sh)
        A('      op.execLower(vu, 0x%08xu, c.vuData, c.dataSize, *c.gs, c.memory, 0x%08xu);' % (p['lower'], p['upper']))
        A('      std::memcpy(vu.m_state.vf[%d], upVf, 16); }' % sh)
    else:
        A(upper_stmt(p['upper']))
        A('    op.execLower(vu, 0x%08xu, c.vuData, c.dataSize, *c.gs, c.memory, 0x%08xu);' % (p['lower'], p['upper']))
    A('    vu.m_viBranchBackupValid = false;')

    # ---- writes were applied at issue (PERF-HT); only the same-register quirk needs the requeue of the upper lanes ----
    if same_reg_quirk:
        lat = U['vfl'] if U['vfl'] else U['lat']
        A('    { float nv[4]; std::memcpy(nv, vu.m_state.vf[%d], 16); std::memcpy(vu.m_state.vf[%d], oldUp, 16); op.qVf(vu, %d, %d, nv, %d); }'
          % (U['wreg'], U['wreg'], U['wreg'], U['wlanes'], lat))

    # ---- markPairWrites ----
    if has_low:
        lat = L['vfl'] if L['vfl'] else L['lat']
        for comp in range(4):
            if L['wlanes'] & lane(comp):
                A('    vu.m_vfReady[%d][%d] = vu.m_cycle + %du;' % (L['wreg'], comp, lat))
    if has_up:
        lat = U['vfl'] if U['vfl'] else U['lat']
        for comp in range(4):
            if U['wlanes'] & lane(comp):
                A('    vu.m_vfReady[%d][%d] = vu.m_cycle + %du;' % (U['wreg'], comp, lat))
    if viw_mask:
        lat = L['vil'] if L['vil'] else L['lat']
        for r in range(1, 16):
            if viw_mask & (1 << r):
                A('    vu.m_viReady[%d] = vu.m_cycle + %du;' % (r, lat))
    if U['aw']:
        for comp in range(4):
            if U['aw'] & lane(comp):
                A('    vu.m_accReady[%d] = vu.m_cycle + 1u;' % comp)
    if viw_mask and L['dnb']:
        A('    vu.m_viBranchBackupValue = oldVi; vu.m_viBranchBackupReg = %d; vu.m_viBranchBackupValid = true;' % written)

    A('    vu.m_state.vf[0][0] = 0.0f; vu.m_state.vf[0][1] = 0.0f; vu.m_state.vf[0][2] = 0.0f; vu.m_state.vf[0][3] = 1.0f; vu.m_state.vi[0] = 0;')

    nxt = pc + 8
    if nxt >= UC['pclim']:
        nxt = 0
    A('    vu.m_state.pc = 0x%04Xu;' % nxt)
    A('    if (vu.m_state.branchPending)')
    A('    {')
    A('        if (vu.m_state.branchDelay == 0u) { vu.m_state.pc = vu.m_state.branchTarget & 0x%04Xu; vu.m_state.branchPending = false; }' % UC['pcmask'])
    A('        else { --vu.m_state.branchDelay; }')
    A('    }')

    d_expr = 'vu.m_state.dBitEnabled' if p['d'] else 'false'
    t_expr = 'vu.m_state.tBitEnabled' if p['t'] else 'false'
    A('    {')
    A('        const bool dHalt = %s; const bool tHalt = %s; const bool haltBit = dHalt || tHalt;' % (d_expr, t_expr))
    A('        const bool haltBranch = haltBit && %s;' % ('true' if L['pipe'] == 6 else 'false'))
    A('        if (vu.m_state.haltAfterDelaySlot) { vu.m_state.stoppedByD = vu.m_pendingHaltD; vu.m_state.stoppedByT = vu.m_pendingHaltT; c.programEnded = true; }')
    A('        else if (vu.m_state.ebit) c.programEnded = true;')
    A('        else if (haltBit && !haltBranch) { vu.m_state.stoppedByD = dHalt; vu.m_state.stoppedByT = tHalt; c.programEnded = true; }')
    if p['e']:
        A('        else vu.m_state.ebit = true;')
    else:
        A('        else if (haltBranch) { vu.m_state.haltAfterDelaySlot = true; vu.m_pendingHaltD = dHalt; vu.m_pendingHaltT = tHalt; }')
    A('    }')
    A('    ++vu.m_cycle; vu.m_state.cycles = vu.m_cycle; // PERF-IC: inline advanceOneCycle')
    A('    if (vu.m_cycle >= *c.nextReady) op.commit(vu);')
    A('    if (vu.m_xgkick.active) op.xgProgress(vu);')
    A('    return c.programEnded ? 1 : 0;')
    A('}')
    A('')
    return o


FILE_HEAD = '''// GENERATED by tools/vu1gen/gen_vu1_native.py from %(src)s -- do not edit.
// The class is viewed with public access in this translation unit only to read/write the scheduler state directly
// (data members only; every private member FUNCTION is reached through VuNativeOps).
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#define private public
#include "runtime/ps2_vu1.h"
#undef private
#include "../vu1_native_api.h"

namespace
{
inline float vuNormalizeOperand(float value)
{
    uint32_t bits = 0;
    std::memcpy(&bits, &value, sizeof(bits));
    const uint32_t exponent = (bits >> 23) & 0xFFu;
    if (exponent == 0u)
        bits &= 0x80000000u;
    else if (exponent == 0xFFu)
        bits = (bits & 0x80000000u) | 0x7F7FFFFFu;
    std::memcpy(&value, &bits, sizeof(value));
    return value;
}
}

'''


def load_pairs(src):
    pairs = {}
    for line in open(src):
        if not line.startswith('P '):
            continue
        head, rest = line.split(' L ', 1)
        lpart, upart = rest.split(' U ', 1)
        hv = head.split()
        pc = int(hv[1], 16)
        d = kv(head)
        pairs[pc] = {
            'upper': int(hv[2], 16), 'lower': int(hv[3], 16),
            'i': int(d['i']), 'e': int(d['e']), 'm': int(d['m']), 'd': int(d['d']), 't': int(d['t']),
            'shadow': int(d['shadow']), 'supp': int(d['supp']),
            'L': parse_usage(kv(lpart)), 'U': parse_usage(kv(upart)),
        }
    return pairs


def main():
    src = sys.argv[1]
    configure(src)
    h = re.search(r'([0-9a-f]{16})', src).group(1)
    pairs = load_pairs(src)
    native = []
    for pc in sorted(pairs):
        p = pairs[pc]
        if p['L']['rsv'] or p['U']['rsv'] or (p['upper'] == 0 and p['lower'] == 0):
            continue
        native.append(pc)
    os.makedirs(OUT_DIR, exist_ok=True)
    chunks = UC['chunks']
    per = (len(native) + chunks - 1) // chunks
    files = []
    for k in range(chunks):
        part = native[k * per:(k + 1) * per]
        name = '%s_native_exec_%d.cpp' % (UC['name'], k)
        files.append(name)
        with open(OUT_DIR + name, 'w', newline='\n') as f:
            f.write(FILE_HEAD % {'src': src})
            for pc in part:
                f.write('\n'.join(emit_pair(pc, pairs[pc])))
                f.write('\n')
    with open(OUT_DIR + '%s_native_dispatch.cpp' % UC['name'], 'w', newline='\n') as f:
        f.write(FILE_HEAD % {'src': src})
        f.write('const uint64_t k%sNativeMainHash = 0x%sull;\n\n' % (UC['Name'], h))
        for pc in native:
            f.write('int %s_%04X(VU1Interpreter &, VuNativeCtx &);\n' % (UC['step'], pc))
        f.write('\nnamespace\n{\nusing StepFn = int (*)(VU1Interpreter &, VuNativeCtx &);\n')
        f.write('const StepFn kStep[%d] = {\n' % UC['slots'])
        nset = set(native)
        for i in range(UC['slots']):
            f.write('  %s,\n' % ('%s_%04X' % (UC['step'], i * 8) if i * 8 in nset else 'nullptr'))
        f.write('};\n}\n\n')
        f.write(RUN_TEMPLATE.replace('vu1NativeRun', UC['name'] + 'NativeRun').replace('0x4000u', '0x%04Xu' % UC['pclim'])
                .replace('kVu1HotStart', 'k%sHotStart' % UC['Name']).replace('vu1HotLookup', UC['name'] + 'HotLookup')
                .replace('[probe] hot blocks=', '[probe] %s blocks=' % UC['hot']))
    files.append('%s_native_dispatch.cpp' % UC['name'])
    print('image %s: %d native pairs, %d files' % (h, len(native), len(files)))
    print('CMake sources:')
    for n in files:
        print('    src/lib/vu/generated/' + n)


RUN_TEMPLATE = '''#include <cstdio>

namespace
{
uint64_t s_hotBlocks = 0, s_hotPairs = 0, s_slowPairs = 0;
}

int vu1NativeRun(VU1Interpreter &vu, VuNativeCtx &c)
{
    c.hashValid = false; // the interpreter may have executed pairs since the last hot block
    while (vu.m_cycle < c.budgetEnd && !vu.m_stopRequested)
    {
        const uint32_t pc = vu.m_state.pc;
        if ((pc & 7u) != 0u || pc >= 0x4000u)
            return 2;
        // PERF-IE: hot blocks with static timing (generated/vu1_hot_blocks.cpp); any unknown state falls back to the pair executors
        if (kVu1HotStart[pc >> 3] && !vu.m_xgkick.active && !vu.m_state.branchPending && !vu.m_state.ebit &&
            !vu.m_state.haltAfterDelaySlot && c.budgetEnd - vu.m_cycle > 160u)
        {
            if (!c.hashValid)
            {
                c.nextHash = c.ops->blkHash(vu);
                c.hashValid = true;
            }
            const VuHotFn hf = vu1HotLookup(pc, c.nextHash);
            if (hf)
            {
                const uint64_t i0 = c.instrs;
                const int hr = hf(vu, c);
                s_hotPairs += c.instrs - i0;
                ++s_hotBlocks;
                if (c.check && c.ops->blkHash(vu) != c.nextHash)
                {
                    ++c.checkFail;
                    if (c.checkFail <= 6)
                        std::printf("[probe] hot block exit-hash MISMATCH at pc=%04X (block entered at %04X)\\n", vu.m_state.pc, pc);
                    c.hashValid = false;
                }
                if ((s_hotBlocks & 0x7FFFFFull) == 0u)
                    std::printf("[probe] hot blocks=%llu hotPairs=%llu slowPairs=%llu hotShare=%.1f%% checkFail=%llu\\n", (unsigned long long)s_hotBlocks,
                                (unsigned long long)s_hotPairs, (unsigned long long)s_slowPairs,
                                100.0 * s_hotPairs / double(s_hotPairs + s_slowPairs + 1), (unsigned long long)c.checkFail);
                if (hr != 0)
                    return hr;
                continue;
            }
        }
        c.hashValid = false;
        const StepFn fn = kStep[pc >> 3];
        if (!fn)
            return 2;
        ++s_slowPairs;
        const int r = fn(vu, c);
        if (r != 0)
            return r;
    }
    return 1;
}
'''


if __name__ == '__main__':
    main()
