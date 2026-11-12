"""PERF-LEAN: trim per-pair bookkeeping inside VU hot blocks (exactness-preserving, idempotent).
Hot blocks have static timing, so inside a block nothing reads the readiness scoreboards, st.cycles, the branch-backup
registers (except a branch pair reading the pair before it) or st.pc (except store hooks / execLower). Only the state at
block exit matters, so:
  - m_vfReady/m_viReady/m_accReady stores: only the last write per register is kept, emitted once before the exit
  - st.cycles: one store at block exit
  - m_viBranchBackup*: kept only on the last pair and on a pair directly before a branch reader
  - st.pc = <pair>: kept only on pairs that store (qs / sq / isw / sqi / xgkick) or call execLower
Usage: python tools/vu1gen/patch_lean_hot.py"""
import pathlib
import re

GEN = pathlib.Path(__file__).resolve().parent.parent.parent / "PS2Recomp/ps2xRuntime/src/lib/vu/generated"
TAG = "PERF-LEAN"
RDY = re.compile(r"^\s*vu\.m_(vfReady\[\d+\]\[\d+\]|viReady\[\d+\]|accReady\[\d+\]) = vu\.m_cycle \+ (\d+)u;\s*$")
PAIR = re.compile(r"^    \{ // pair (\d+) @ ([0-9A-F]+)$")
SETC = re.compile(r"(?:setCycleXg\(vu, op, S|advanceTo\(vu, S) \+ (\d+)u\)")


def patch_block(lines):
    """lines: the text lines of one block function. Returns the new lines."""
    # locate pairs
    pairs = []  # (start, end) line indexes of '    { // pair' .. '    }'
    i = 0
    while i < len(lines):
        if PAIR.match(lines[i]):
            j = i + 1
            while lines[j] != "    }":
                j += 1
            pairs.append((i, j))
            i = j
        i += 1
    if not pairs:
        return lines
    ready = {}
    cur = 0
    out = []
    pos = 0
    for k, (a, b) in enumerate(pairs):
        # lines between pairs: cycle model + passthrough
        for ln in lines[pos:a]:
            m = SETC.search(ln)
            if m:
                cur = int(m.group(1))
            out.append(ln)
        body = lines[a:b + 1]
        nxt_txt = "\n".join(lines[pairs[k + 1][0]:pairs[k + 1][1] + 1]) if k + 1 < len(pairs) else ""
        is_last = k == len(pairs) - 1
        keep_backup = is_last or ("readBranchVi" in nxt_txt) or ("execLower" in nxt_txt) or ("branchPending" in nxt_txt)
        txt = "\n".join(body)
        needs_pc = (", qs)" in txt) or ("execLower" in txt) or ("xgkick" in txt.lower()) or ("oldUp" in txt)
        nb = []
        for idx, ln in enumerate(body):
            m = RDY.match(ln)
            if m:
                ready[m.group(1)] = cur + int(m.group(2))
                continue
            if not keep_backup and ("m_viBranchBackup" in ln):
                continue
            if idx == 1 and ln.strip().startswith("st.pc = 0x") and not needs_pc:
                continue
            nb.append(ln)
        out.extend(nb)
        pos = b + 1
        # after the pair: advance model
        tail = lines[pos] if pos < len(lines) else ""
        cur += 1
    out.extend(lines[pos:])
    # st.cycles: drop the per-pair store, one at exit
    res = []
    for ln in out:
        ln = ln.replace("++vu.m_cycle; st.cycles = vu.m_cycle; if (vu.m_xgkick.active)", "++vu.m_cycle; if (vu.m_xgkick.active)")
        res.append(ln)
    # insert exit stores before 'c.nextHash'
    final = []
    for ln in res:
        if ln.lstrip().startswith("c.nextHash = "):
            final.append("    st.cycles = vu.m_cycle; // " + TAG)
            for key in sorted(ready):
                final.append("    vu.m_%s = S + %du; // %s" % (key, ready[key], TAG))
        final.append(ln)
    return final


for fn in ("vu1_hot_blocks.cpp", "vu0_hot_blocks.cpp"):
    p = GEN / fn
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8", errors="surrogateescape")
    if TAG in t:
        print(fn, "already patched")
        continue
    lines = t.split("\n")
    out = []
    i = 0
    nblk = 0
    while i < len(lines):
        if re.match(r"^static int vu0?H_\d+\(", lines[i]):
            j = i
            while lines[j] != "}":
                j += 1
            out.extend(patch_block(lines[i:j + 1]))
            nblk += 1
            i = j + 1
            continue
        out.append(lines[i])
        i += 1
    p.write_text("\n".join(out), encoding="utf-8", errors="surrogateescape")
    print(fn, "patched blocks:", nblk, "lines", len(lines), "->", len(out))
