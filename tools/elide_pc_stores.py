#!/usr/bin/env python3
"""elide_pc_stores.py - delete provably-unneeded `ctx->pc = 0x...u;` lines.

Every guest instruction in recomp_source/*.cpp is emitted as
    // 0x3b45ec: 0x240e0002  addiu $t6, $zero, 0x2
    ctx->pc = 0x3b45ecu;
    SET_GPR_S32(...);
The pc store is only needed before statements that can observe ctx->pc.
We remove it when the following statement is pure register arithmetic.

Rule (strict; when in doubt KEEP):
  * Candidate: line matching ^\\s*ctx->pc = 0x[0-9a-fA-F]+u;\\s*$ that is
    directly preceded by a `// 0x` instruction comment (so the function's
    first pc store after the entry switch is never touched).
  * Following statement: the next non-empty, non-comment lines up to (not
    including) the next `// 0x` comment, `ctx->pc =` line, label line
    (`name:`), or a line consisting only of `{`/`}`. More than one line -> KEEP.
  * That single line must start with SET_GPR_S32/U32/U64/S64/ZE32( and end
    with `);`, and every identifier in it must be whitelisted (GPR accessors,
    ADD32/SUB32, ctx, intN_t/uintN_t). Numbers (incl. 0x..u, ..ULL suffixes)
    are literals. Any other identifier (READ32, runtime, HI, LO, calls...) -> KEEP.
  * If the previous instruction's mnemonic starts with 'b' or 'j' (branch or
    jump), this is a delay slot -> KEEP.

Usage: elide_pc_stores.py [--dry-run] <dir>
Without --dry-run files are rewritten in place (line endings preserved).
"""
import os
import re
import sys
from collections import Counter

PC_RE = re.compile(r'^\s*ctx->pc = 0x[0-9a-fA-F]+u;\s*$')
INSN_RE = re.compile(r'^\s*// 0x[0-9a-fA-F]+:\s+0x[0-9a-fA-F]+\s+(\S+)')
LABEL_RE = re.compile(r'^\s*[A-Za-z_][A-Za-z0-9_]*:\s*$')
START_RE = re.compile(r'^\s*SET_GPR_(S32|U32|U64|S64|ZE32)\(')
NUM_RE = re.compile(r'0[xX][0-9a-fA-F]+[uUlL]*|[0-9]+(?:\.[0-9]*)?[uUlLfF]*')
ID_RE = re.compile(r'[A-Za-z_][A-Za-z0-9_]*')
# numbers first (so 0x3b45ecu / 4294966464ULL are one token), then identifiers
TOK_RE = re.compile(r'0[xX][0-9a-fA-F]+[A-Za-z]*|[0-9][0-9A-Za-z_.]*|[A-Za-z_][A-Za-z0-9_]*')
WHITE = set("""SET_GPR_S32 SET_GPR_U32 SET_GPR_U64 SET_GPR_S64 SET_GPR_ZE32
GPR_U32 GPR_S32 GPR_U64 GPR_S64 ADD32 SUB32 ctx int8_t uint8_t int16_t uint16_t
int32_t uint32_t int64_t uint64_t SLL32 SRL32 SRA32 SLT32 SLTU32
FAST_READ8 FAST_READ16 FAST_READ32 FAST_READ64 FAST_READ128
FAST_WRITE8 FAST_WRITE16 FAST_WRITE32 FAST_WRITE64 FAST_WRITE128""".split())
MEM_RE = re.compile(r'^(READ|WRITE)(8|16|32|64|128)$')
PCLIT_RE = re.compile(r'^\s*ctx->pc = (0x[0-9a-fA-F]+u);\s*$')


def is_boundary(s):
    t = s.strip()
    return (t.startswith('// 0x') or t.startswith('ctx->pc =') or t in ('{', '}')
            or bool(LABEL_RE.match(s)))


def process(lines, stats, idents):
    remove = set()
    rewrites = {}
    prev_mn = None
    n = len(lines)
    for i, ln in enumerate(lines):
        m = INSN_RE.match(ln)
        if m:
            prev_mn_cur = m.group(1).lower()
        if PC_RE.match(ln):
            stats['cand'] += 1
            # find directly-preceding line being an instruction comment
            j = i - 1
            if j < 0 or not INSN_RE.match(lines[j]):
                stats['first'] += 1
                continue
            mn = INSN_RE.match(lines[j]).group(1).lower()
            # previous instruction mnemonic: scan back before lines[j]
            k = j - 1
            pm = None
            while k >= 0:
                mm = INSN_RE.match(lines[k])
                if mm:
                    pm = mm.group(1).lower()
                    break
                k -= 1
            if pm is not None and (pm[0] in 'bj'):
                stats['delay'] += 1
                continue
            body = []
            k = i + 1
            while k < n:
                s = lines[k]
                if is_boundary(s):
                    break
                t = s.strip()
                if t and not t.startswith('//'):
                    body.append(t)
                k += 1
            if len(body) != 1:
                stats['multi'] += 1
                continue
            b = body[0]
            if not ((START_RE.match(b) and b.endswith(');'))
                    or (b.startswith('WRITE') and b.endswith(';'))):
                stats['notset'] += 1
                continue
            toks = TOK_RE.findall(b)
            ids = [x for x in toks if x[0].isalpha() or x[0] == '_']
            mem = [x for x in ids if MEM_RE.match(x)]
            if mem:
                # memory rewrite rule
                pcm = PCLIT_RE.match(ln)
                bad = [x for x in ids if x not in WHITE and not MEM_RE.match(x)]
                is_read = bool(START_RE.match(b)) and b.endswith(');')
                is_write = b.startswith('WRITE') and b.endswith(';')
                name = mem[0]
                ok = (len(mem) == 1 and not bad and pcm
                      and re.search(r'\b%s\(' % name, b)
                      and ((is_read and name.startswith('READ'))
                           or (is_write and name.startswith('WRITE'))))
                if not ok:
                    stats['ident'] += 1
                    idents[(bad or mem)[0]] += 1
                    continue
                remove.add(i)
                # rewrite the body line (the single non-comment line after the pc store)
                for kk in range(i + 1, n):
                    if lines[kk].strip() == b:
                        rewrites[kk] = re.sub(r'\b%s\(' % name,
                                              '%sP(%s, ' % (name, pcm.group(1)),
                                              lines[kk], count=1)
                        break
                stats['memrw'] += 1
                stats['mem_' + name] += 1
                continue
            bad = [x for x in ids if x not in WHITE]
            if bad:
                stats['ident'] += 1
                idents[bad[0]] += 1
                continue
            remove.add(i)
            stats['removable'] += 1
    return remove, rewrites


def main():
    args = sys.argv[1:]
    dry = '--dry-run' in args
    args = [a for a in args if a != '--dry-run']
    if len(args) != 1:
        print(__doc__)
        return 2
    stats = Counter()
    idents = Counter()
    for fn in sorted(os.listdir(args[0])):
        if not fn.endswith('.cpp'):
            continue
        path = os.path.join(args[0], fn)
        with open(path, 'rb') as f:
            data = f.read()
        text = data.decode('utf-8', errors='surrogateescape')
        lines = text.splitlines(keepends=True)
        stats['files'] += 1
        # strip endings for matching, but keep originals for output
        bare = [l.rstrip('\r\n') for l in lines]
        rm, rw = process(bare, stats, idents)
        if (rm or rw) and not dry:
            def _fix(i, l):
                if i in rw:
                    eol = l[len(l.rstrip('\r\n')):]
                    return rw[i] + eol
                return l
            out = ''.join(_fix(i, l) for i, l in enumerate(lines) if i not in rm)
            with open(path, 'wb') as f:
                f.write(out.encode('utf-8', errors='surrogateescape'))
    print('mode: %s' % ('dry-run' if dry else 'WRITE'))
    print('files scanned: %d' % stats['files'])
    print('candidate pc stores: %d' % stats['cand'])
    print('removable (pure): %d' % stats['removable'])
    print('removable (memory rewrite to P): %d  [%s]' % (stats['memrw'], ', '.join(
        '%s=%d' % (k[4:], v) for k, v in sorted(stats.items()) if k.startswith('mem_'))))
    print('kept: multi-line %d, not SET_GPR %d, identifier %d, delay slot %d, first store %d'
          % (stats['multi'], stats['notset'], stats['ident'], stats['delay'], stats['first']))
    print('top identifiers: ' + ', '.join('%s=%d' % kv for kv in idents.most_common(20)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
