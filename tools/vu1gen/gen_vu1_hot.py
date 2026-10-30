#!/usr/bin/env python3
"""VU1 hot-block generator (PERF-IE).

Inputs : logs/vuusage_u1_<image>.txt   (per-pair decode/usage dump, also used by gen_vu1_native.py)
         logs/vublk2_u1_<image>.txt    (PROBE-BLK v3 records: entry hash, exit hash, issue cycles, commit flags per block)
         tools/vu1gen/hot_blocks.txt   (the blocks to compile: "pc sighex")
Output : PS2Recomp/ps2xRuntime/src/lib/vu/generated/vu1_hot_blocks.cpp   (block functions, vu1HotLookup, kVu1HotStart)

A block is a dynamic basic block: from a loop-top timing state to the end of the delay slot after a branch (or an XGKICK pair).
Its timing (stalls) and the points where delayed pipelines commit are constants recorded from the exact interpreter, so the block
code has no readiness checks, scoreboard reads, commit scans or per-pair epilogues. Everything else (unknown entry state, XGKICK
active, near the cycle budget) falls back to the verified per-pair executors.
Run from the repo root: python tools/vu1gen/gen_vu1_hot.py logs/vuusage_u1_<image>.txt logs/vublk2_u1_<image>.txt
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_vu1_native as g  # noqa: E402

OUT = 'PS2Recomp/ps2xRuntime/src/lib/vu/generated/vu1_hot_blocks.cpp'


def lane(c):
    return 1 << (3 - c)


def parse_blk(path):
    recs = []
    cur = None
    for line in open(path):
        if line.startswith('B '):
            kvd = dict(t.split('=', 1) for t in line.split()[1:])
            cur = {'pc': int(kvd['pc'], 16), 'sig': int(kvd['sig'], 16), 'exitsig': int(kvd['exitsig'], 16),
                   'n': int(kvd['n']), 'xg': int(kvd['xg']), 'next': int(kvd['next'], 16)}
            recs.append(cur)
        elif cur is not None:
            s = line.strip()
            if s.startswith('issue:'):
                cur['issue'] = [int(x) for x in s[6:].split()]
            elif s.startswith('cb:'):
                cur['cb'] = [int(x) for x in s[3:].split()]
            elif s.startswith('ca:'):
                cur['ca'] = [int(x) for x in s[3:].split()]
    return recs


# ---------------------------------------------------------------------------------------------------------------- upper ops
KIND_TABLE = {0x1C: (4, 1), 0x1E: (4, 2), 0x20: (0, 1), 0x21: (2, 1), 0x22: (0, 2), 0x23: (2, 2), 0x24: (1, 1), 0x25: (3, 1),
              0x26: (1, 2), 0x27: (3, 2), 0x28: (0, 3), 0x29: (2, 3), 0x2A: (4, 3), 0x2C: (1, 3), 0x2D: (3, 3)}


def fmac_info(u):
    """(kind, src, bc, to_acc, dest) when the upper word is an FMAC-family op handled by vuhot::fmac, else None."""
    op = u & 0x3F
    dest = (u >> 21) & 0xF
    to_acc = op >= 0x3C
    e = op
    if to_acc:
        e = (u & 3) | ((u >> 4) & 0x7C)
        if e in (0x2F, 0x30):
            return None
    if e <= 0x0F:
        return (e >> 2, 0, e & 3, to_acc, dest)
    if 0x18 <= e <= 0x1B:
        return (4, 0, e & 3, to_acc, dest)
    if e in KIND_TABLE:
        k, sr = KIND_TABLE[e]
        return (k, sr, 0, to_acc, dest)
    return None


def upper_stmts(u, keep_mac=True):
    """Native statements for an upper word; falls back to the generic executor."""
    op = u & 0x3F
    dest = (u >> 21) & 0xF
    ft = (u >> 16) & 0x1F
    fs = (u >> 11) & 0x1F
    fd = (u >> 6) & 0x1F
    to_acc = op >= 0x3C
    e = op
    if to_acc:
        e = (u & 3) | ((u >> 4) & 0x7C)
        if e in (0x2F, 0x30):
            return ['vu.m_currentUpperInstruction = 0x%08xu; // NOP' % u]
    pre = 'vu.m_currentUpperInstruction = 0x%08xu;' % u
    # FMAC family (== fastUpper)
    kind = src = None
    bc = 0
    if e <= 0x0F:
        kind, src, bc = e >> 2, 0, e & 3
    elif 0x18 <= e <= 0x1B:
        kind, src, bc = 4, 0, e & 3
    elif e in KIND_TABLE:
        kind, src = KIND_TABLE[e]
    if kind is not None:
        return [pre, 'vuhot::fmac<%d, %d, %d, %s, %d, %s>(vu, %du, %d, %d, %d);' % (kind, src, bc, 'true' if to_acc else 'false', dest, 'true' if keep_mac else 'false', g.UC['unit'], fs, ft, fd)]
    if not to_acc:
        # MAX / MINI (no flags)
        if 0x10 <= e <= 0x13:
            return [pre, 'vuhot::maxmini<true, 0, %d, %d>(st, %d, %d, %d);' % (e & 3, dest, fs, ft, fd)]
        if 0x14 <= e <= 0x17:
            return [pre, 'vuhot::maxmini<false, 0, %d, %d>(st, %d, %d, %d);' % (e & 3, dest, fs, ft, fd)]
        if e == 0x1D:
            return [pre, 'vuhot::maxmini<true, 2, 0, %d>(st, %d, %d, %d);' % (dest, fs, ft, fd)]
        if e == 0x1F:
            return [pre, 'vuhot::maxmini<false, 2, 0, %d>(st, %d, %d, %d);' % (dest, fs, ft, fd)]
        if e == 0x2B:
            return [pre, 'vuhot::maxmini<true, 3, 0, %d>(st, %d, %d, %d);' % (dest, fs, ft, fd)]
        if e == 0x2F:
            return [pre, 'vuhot::maxmini<false, 3, 0, %d>(st, %d, %d, %d);' % (dest, fs, ft, fd)]
    else:
        scale = {0x14: 1, 0x15: 16, 0x16: 4096, 0x17: 32768}.get(e)
        if scale:
            return [pre, 'vuhot::ftoi<%d, %d>(st, %d, %d);' % (scale, dest, fs, ft)]
    return ['op.execUpper(vu, 0x%08xu);' % u]


# ---------------------------------------------------------------------------------------------------------------- lower ops
def imm11(lo):
    v = lo & 0x7FF
    return v - 0x800 if v & 0x400 else v


def lower_stmts(lo, upper, pc):
    """Native statements for a lower word (not an immediate); falls back to the generic executor."""
    op7 = (lo >> 25) & 0x7F
    dest = (lo >> 21) & 0xF
    ft5 = (lo >> 16) & 0x1F
    fs5 = (lo >> 11) & 0x1F
    vit = (lo >> 16) & 0xF
    vis = (lo >> 11) & 0xF
    vid = (lo >> 6) & 0xF
    generic = ['op.execLower(vu, 0x%08xu, c.vuData, c.dataSize, *c.gs, c.memory, 0x%08xu);' % (lo, upper)]
    if op7 == 0x00:
        return ['vuhot::lq(st, c.vuData, c.dataSize, %d, %d, %d, %d);' % (dest, ft5, vis, imm11(lo))]
    if op7 == 0x01:
        return ['vuhot::sq(st, c.dataSize, %d, %d, %d, %d, qs);' % (dest, fs5, vit, imm11(lo))]
    if op7 == 0x04:
        return ['vuhot::ilw(st, c.vuData, c.dataSize, %d, %d, %d, %d);' % (dest, vit, vis, imm11(lo))]
    if op7 == 0x05:
        return ['vuhot::isw(st, c.dataSize, %d, %d, %d, %d, qs);' % (dest, vit, vis, imm11(lo))]
    if op7 == 0x08:
        imm = (lo & 0x7FF) | ((lo >> 10) & 0x7800)
        out = []
        if vit != 0:
            out.append('st.vi[%d] = static_cast<int16_t>(st.vi[%d] + %d);' % (vit, vis, imm))
        return out or ['// IADDIU to vi0']
    if op7 in (0x28, 0x29):
        cmp_ = '==' if op7 == 0x28 else '!='
        imm = imm11(lo)
        tgt = (pc + 8 + imm * 8) & g.UC['pcmask']
        return ['if (static_cast<int16_t>(vuhot::readBranchVi(vu, %d)) %s static_cast<int16_t>(vuhot::readBranchVi(vu, %d)))' % (vis, cmp_, vit),
                '{ st.branchPending = true; st.branchTarget = 0x%04Xu; st.branchDelay = 1; }' % tgt]
    if op7 == 0x40:
        f6 = lo & 0x3F
        if f6 == 0x30 or f6 == 0x31 or f6 == 0x34 or f6 == 0x35:
            if vid == 0:
                return ['// integer op to vi0']
            expr = {0x30: 'static_cast<int16_t>(st.vi[%d] + st.vi[%d])', 0x31: 'static_cast<int16_t>(st.vi[%d] - st.vi[%d])',
                    0x34: 'st.vi[%d] & st.vi[%d]', 0x35: 'st.vi[%d] | st.vi[%d]'}[f6] % (vis, vit)
            return ['st.vi[%d] = %s;' % (vid, expr)]
        if f6 == 0x32:
            imm5 = (lo >> 6) & 0x1F
            if imm5 & 0x10:
                imm5 -= 32
            if vit == 0:
                return ['// IADDI to vi0']
            return ['st.vi[%d] = static_cast<int16_t>(st.vi[%d] + %d);' % (vit, vis, imm5)]
        if f6 >= 0x3C:
            f2 = (lo & 3) | ((lo >> 4) & 0x7C)
            if f2 == 0x30:
                return ['vuhot::move(st, %d, %d, %d);' % (dest, ft5, fs5)]
            if f2 == 0x31:
                return ['vuhot::mr32(st, %d, %d, %d);' % (dest, ft5, fs5)]
            if f2 == 0x34:
                return ['vuhot::lqi(st, c.vuData, c.dataSize, %d, %d, %d);' % (dest, ft5, vis)]
            if f2 == 0x35:
                return ['vuhot::sqi(st, c.dataSize, %d, %d, %d, qs);' % (dest, fs5, vit)]
    return generic


# ---------------------------------------------------------------------------------------------------------------- pair body
def pair_body(i, pc, p, n, is_last, after_branch, keep_mac, indent='    '):
    L, U = p['L'], p['U']
    o = []
    A = o.append
    ind = indent
    A(ind + 'st.pc = 0x%04Xu;' % pc)
    viw_mask = L['viw'] & 0xFFFE
    written = 0
    if viw_mask:
        written = (viw_mask & -viw_mask).bit_length() - 1
        if L['dnb']:
            A(ind + 'const int32_t oldVi = st.vi[%d];' % written)
    has_up = U['wreg'] != 0
    same_reg_quirk = has_up and L['wreg'] != 0 and L['wreg'] == U['wreg']
    if same_reg_quirk:
        A(ind + 'float oldUp[4]; std::memcpy(oldUp, st.vf[%d], 16);' % U['wreg'])

    ups = upper_stmts(p['upper'], keep_mac)
    lows = None if p['i'] else lower_stmts(p['lower'], p['upper'], pc)
    if p['i']:
        for s_ in ups:
            A(ind + s_)
        A(ind + '{ const uint32_t lb = 0x%08xu; float imm; std::memcpy(&imm, &lb, 4); st.i = vuhot::N(imm); }' % p['lower'])
    elif p['shadow']:
        sh = p['shadow']
        A(ind + '{ float oldVf[4], upVf[4];')
        A(ind + '  std::memcpy(oldVf, st.vf[%d], 16);' % sh)
        for s_ in ups:
            A(ind + '  ' + s_)
        A(ind + '  std::memcpy(upVf, st.vf[%d], 16);' % sh)
        A(ind + '  std::memcpy(st.vf[%d], oldVf, 16);' % sh)
        for s_ in lows:
            A(ind + '  ' + s_)
        A(ind + '  std::memcpy(st.vf[%d], upVf, 16); }' % sh)
    else:
        for s_ in ups:
            A(ind + s_)
        for s_ in lows:
            A(ind + s_)
    A(ind + 'vu.m_viBranchBackupValid = false;')
    if same_reg_quirk:
        lat = U['vfl'] if U['vfl'] else U['lat']
        A(ind + '{ float nv[4]; std::memcpy(nv, st.vf[%d], 16); std::memcpy(st.vf[%d], oldUp, 16); op.qVf(vu, %d, %d, nv, %d); }'
          % (U['wreg'], U['wreg'], U['wreg'], U['wlanes'], lat))

    # ---- markPairWrites (scoreboards for the per-pair fallback path) ----
    has_low = L['wreg'] != 0 and p['supp'] != L['wreg']
    if has_low:
        lat = L['vfl'] if L['vfl'] else L['lat']
        for comp in range(4):
            if L['wlanes'] & lane(comp):
                A(ind + 'vu.m_vfReady[%d][%d] = vu.m_cycle + %du;' % (L['wreg'], comp, lat))
    if has_up:
        lat = U['vfl'] if U['vfl'] else U['lat']
        for comp in range(4):
            if U['wlanes'] & lane(comp):
                A(ind + 'vu.m_vfReady[%d][%d] = vu.m_cycle + %du;' % (U['wreg'], comp, lat))
    if viw_mask:
        lat = L['vil'] if L['vil'] else L['lat']
        for r_ in range(1, 16):
            if viw_mask & (1 << r_):
                A(ind + 'vu.m_viReady[%d] = vu.m_cycle + %du;' % (r_, lat))
    if U['aw']:
        for comp in range(4):
            if U['aw'] & lane(comp):
                A(ind + 'vu.m_accReady[%d] = vu.m_cycle + 1u;' % comp)
    if viw_mask and L['dnb']:
        A(ind + 'vu.m_viBranchBackupValue = oldVi; vu.m_viBranchBackupReg = %d; vu.m_viBranchBackupValid = true;' % written)
    A(ind + 'st.vf[0][0] = 0.0f; st.vf[0][1] = 0.0f; st.vf[0][2] = 0.0f; st.vf[0][3] = 1.0f; st.vi[0] = 0;')

    is_branch = L['pipe'] == 6
    if is_branch or after_branch or is_last:
        nxt = pc + 8
        if nxt >= g.UC['pclim']:
            nxt = 0
        A(ind + 'st.pc = 0x%04Xu;' % nxt)
        A(ind + 'if (st.branchPending)')
        A(ind + '{')
        A(ind + '    if (st.branchDelay == 0u) { st.pc = st.branchTarget & 0x%04Xu; st.branchPending = false; }' % g.UC['pcmask'])
        A(ind + '    else { --st.branchDelay; }')
        A(ind + '}')
    return o


def emit_block(name, rec, pairs):
    pc0, n = rec['pc'], rec['n']
    issue, cb, ca = rec['issue'], rec['cb'], rec['ca']
    assert len(issue) == n and len(cb) == n and len(ca) == n, (hex(pc0), n, len(issue), len(cb), len(ca))
    o = []
    A = o.append
    A('static int %s(VU1Interpreter &vu, VuNativeCtx &c) // pc=%04X entry=%016x exit=%016x n=%d cycles=%d' % (name, pc0, rec['sig'], rec['exitsig'], n, issue[-1] + 1))
    A('{')
    A('    const VuNativeOps &op = *c.ops;')
    A('    VU1State &st = vu.m_state;')
    A('    const uint64_t S = vu.m_cycle;')
    A('    auto qs = [&](uint32_t a, const uint32_t *w, uint8_t l) { vuhot::storeFast(vu, c, a, w, l); };')
    A('    (void)qs; (void)op;')
    A('    c.instrs += %du;' % n)
    # MAC ring pushes: no FM* reader inside the block => only the newest write that has landed at block exit (and later ones) can still be seen
    readers = any((not pairs[pc0 + 8 * k]['i']) and ((pairs[pc0 + 8 * k]['lower'] >> 25) & 0x7F) in (0x18, 0x1A, 0x1B) for k in range(n))
    e_exit = issue[-1] + 1
    fm = [k for k in range(n) if fmac_info(pairs[pc0 + 8 * k]['upper']) is not None and fmac_info(pairs[pc0 + 8 * k]['upper'])[4] != 0]
    landed = [k for k in fm if issue[k] + 4 <= e_exit]
    first_keep = max(landed) if landed else None
    keep = set(fm) if (readers or first_keep is None) else set(k for k in fm if k >= first_keep)
    prev_end = 0
    prev_branch = False
    for i in range(n):
        pc = pc0 + 8 * i
        p = pairs[pc]
        d = issue[i] - prev_end
        if d > 0 and cb[i]:
            A('    op.advanceTo(vu, S + %du);' % issue[i])
        elif d > 0:
            A('    vu.m_cycle = S + %du; st.cycles = vu.m_cycle;' % issue[i])
        elif cb[i]:
            A('    op.commit(vu);')
        A('    { // pair %d @ %04X' % (i, pc))
        for line in pair_body(i, pc, p, n, i == n - 1, prev_branch, i in keep):
            A(line)
        A('    }')
        if ca[i] or p['L']['pipe'] == 7:
            A('    op.advance1(vu);')
        else:
            A('    ++vu.m_cycle; st.cycles = vu.m_cycle;')
        if p['e']:
            A('    st.ebit = true; // PERF-IP: E bit; the program ends after the next (delay-slot) pair')
        prev_end = issue[i] + 1
        prev_branch = p['L']['pipe'] == 6
    A('    c.nextHash = 0x%016xull; c.hashValid = true;' % rec['exitsig'])
    if n >= 2 and pairs[pc0 + 8 * (n - 2)]['e']:
        A('    c.programEnded = true;')
        A('    return 1;')
    else:
        A('    return 0;')
    A('}')
    A('')
    return o


HEAD = '''// GENERATED by tools/vu1gen/gen_vu1_hot.py -- do not edit.
// Hot VU1 blocks with static timing (see gen_vu1_hot.py). Exactness is checked by PS2X_VU1_VERIFY=3 and PS2X_VU_BLK_CHECK=1.
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#define private public
#include "runtime/ps2_vu1.h"
#undef private
#include "../vu1_native_api.h"
#include "../vu1_hot_ops.h"

'''


def main():
    usage_path, blk_path = sys.argv[1], sys.argv[2]
    g.configure(usage_path)
    out = OUT.replace('vu1_hot_blocks', g.UC['name'] + '_hot_blocks')
    pre = 'vuH_' if g.UC['unit'] == 1 else 'vu0H_'
    pairs = g.load_pairs(usage_path)
    recs = parse_blk(blk_path)
    wanted = []
    if g.UC['unit'] == 0:
        wanted = [(r['pc'], r['sig']) for r in recs]  # PERF-IM: the VU0 image has only a handful of recorded blocks: take them all
    for line in (open('tools/vu1gen/hot_blocks.txt') if g.UC['unit'] == 1 else []):
        line = line.split('#')[0].strip()
        if line:
            a, b = line.split()
            wanted.append((int(a, 16), int(b, 16)))
    byk = {(r['pc'], r['sig']): r for r in recs}
    chosen = []
    for k in wanted:
        r = byk.get(k)
        if r is None:
            print('WARNING: block %04X %016x not in %s' % (k[0], k[1], blk_path))
            continue
        if r['xg']:
            continue
        # sanity: the block must not contain halt/E bits and must be inside the image
        ok = True
        for i in range(r['n']):
            p = pairs.get(r['pc'] + 8 * i)
            if p is None or p['d'] or p['t'] or p['L']['rsv'] or p['U']['rsv']:
                ok = False
            elif p['e'] and i != r['n'] - 2:  # PERF-IP: an E bit is only allowed on the pair before the block's last (delay-slot) pair
                ok = False
        if not ok:
            print('skip %04X (E/D/T bit or reserved op)' % r['pc'])
            continue
        chosen.append(r)
    lines = [HEAD]
    for idx, r in enumerate(chosen):
        lines.extend(emit_block(pre + '%d' % idx, r, pairs))
        lines.append('')
    lines.append('VuHotFn %sHotLookup(uint32_t pc, uint64_t h)' % g.UC['name'])
    lines.append('{')
    lines.append('    switch (pc)')
    lines.append('    {')
    bypc = {}
    for idx, r in enumerate(chosen):
        bypc.setdefault(r['pc'], []).append((r['sig'], idx))
    for pc in sorted(bypc):
        lines.append('    case 0x%04X:' % pc)
        for sig, idx in bypc[pc]:
            lines.append('        if (h == 0x%016xull) return %s%d;' % (sig, pre, idx))
        lines.append('        break;')
    lines.append('    default: break;')
    lines.append('    }')
    lines.append('    return nullptr;')
    lines.append('}')
    lines.append('')
    starts = sorted(bypc)
    lines.append('const bool k%sHotStart[%d] = {' % (g.UC['Name'], g.UC['slots']))
    row = []
    sset = set(starts)
    for i in range(g.UC['slots']):
        row.append('1' if i * 8 in sset else '0')
        if len(row) == 32:
            lines.append('    ' + ','.join(row) + ',')
            row = []
    lines.append('};')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')
    print('hot blocks: %d (of %d wanted) -> %s' % (len(chosen), len(wanted), out))


main()
