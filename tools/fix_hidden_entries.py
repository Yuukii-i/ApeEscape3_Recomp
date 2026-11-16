"""C334: real functions that the recompiler's splitter hid inside another generated range.
A vtable / function-pointer table in the ELF data points at them, but they have no entry in the generated function
table and no `case` in the containing function's `switch (ctx->pc)`. The runtime then runs them in the small fallback
interpreter (no MMI / lq / sq), which silently returns wrong results (e.g. 0x5d04d8 returned 0 -> call through null).

For every unregistered code address that is referenced from the ELF data area and is preceded by an unconditional
j/jr (+ delay slot) or starts with an `addiu sp,sp,-N` prologue, this script
  1. adds `label_<pc>:` before that instruction's block if the function has no such label,
  2. adds `case 0x<pc>u: goto label_<pc>;` to the entry switch,
  3. registers the pc in register_functions.cpp.
Idempotent. Patches recomp_source in place. Usage: python tools/fix_hidden_entries.py [--dry] [--from-logs] [--logs-only] [--split-returns] [--addrs <path>]"""  # FIX-CR4
import bisect, pathlib, re, struct, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "recomp_source"
ELF = ROOT / "SCUS_975.01"
DRY = "--dry" in sys.argv
LOGS_ONLY = "--logs-only" in sys.argv  # FIX-CR1
FROM_LOGS = "--from-logs" in sys.argv or LOGS_ONLY  # FIX-CR1
SPLIT_RETURNS = "--split-returns" in sys.argv  # FIX-CR2
ADDRS_PATH = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--addrs=")), None)  # FIX-CR4
if ADDRS_PATH is None and "--addrs" in sys.argv:  # FIX-CR4
    ADDRS_PATH = sys.argv[sys.argv.index("--addrs") + 1]  # FIX-CR4
TAG = "// C334"

elf = ELF.read_bytes()
e_phoff = struct.unpack_from("<I", elf, 28)[0]
e_phentsize, e_phnum = struct.unpack_from("<HH", elf, 42)
segs = []
for i in range(e_phnum):
    p_type, p_off, p_vaddr, _pa, p_filesz, _ms, p_flags, _al = struct.unpack_from("<IIIIIIII", elf, e_phoff + i * e_phentsize)
    if p_type == 1 and p_filesz > 0:
        segs.append((p_vaddr, p_off, p_filesz))
seg_vaddr, seg_off, seg_size = segs[0]


def word(a):
    return struct.unpack_from("<I", elf, seg_off + (a - seg_vaddr))[0]


# generated function ranges
funcs = []
for f in SRC.glob("sub_*.cpp"):
    m = re.match(r"sub_([0-9A-F]+)_0x", f.name)
    start = int(m.group(1), 16)
    with open(f, encoding="utf-8", errors="replace") as fh:
        head = fh.read(2000)
    mm = re.search(r"// Address: 0x([0-9a-f]+) - 0x([0-9a-f]+)", head)
    end = int(mm.group(2), 16) if mm else start + 4
    funcs.append((start, end, f))
funcs.sort()
starts = [x[0] for x in funcs]


def containing(a):
    i = bisect.bisect_right(starts, a) - 1
    if i >= 0 and funcs[i][0] <= a < funcs[i][1]:
        return funcs[i]
    return None


code_lo, code_hi = 0x100000, max(e for _s, e, _f in funcs)

reg_path = SRC / "register_functions.cpp"
reg_text = reg_path.read_text(encoding="utf-8", errors="replace")
registered = set(int(x, 16) for x in re.findall(r"g_ps2RecompiledFunctionTable\[\d+\] = \w+; // 0x([0-9a-f]+)", reg_text))
slot_count = int(re.search(r"g_ps2RecompiledFunctionTableSlotCount = (\d+)u", reg_text).group(1))


def uncond(ins):
    op = ins >> 26
    rs = (ins >> 21) & 0x1F  # FIX-CR1
    rt = (ins >> 16) & 0x1F  # FIX-CR1
    return (  # FIX-CR1
        op == 2
        or (op == 0 and (ins & 0x3F) == 8)
        or (op == 4 and rs == 0 and rt == 0)  # FIX-CR1
        or (op == 1 and rs == 0 and rt == 1)  # FIX-CR1
    )


cands = {}
data_start = code_hi + ((4 - code_hi % 4) % 4)
for o in range(data_start - seg_vaddr, seg_size - 3, 4):
    w = struct.unpack_from("<I", elf, seg_off + o)[0]
    if code_lo <= w < code_hi and (w & 3) == 0:
        cands.setdefault(w, []).append(seg_vaddr + o)

log_cands = set()  # FIX-CR1
if FROM_LOGS:  # FIX-CR1
    for err_path in sorted((ROOT / "logs").glob("*.err")):  # FIX-CR1
        with open(err_path, encoding="utf-8", errors="replace") as fh:  # FIX-CR1
            for line in fh:  # FIX-CR1
                if line.startswith("[guest-fallback-interp] entry"):  # FIX-CR1
                    m = re.search(r"targetPc=0x([0-9a-f]+)", line, re.I)  # FIX-CR1
                    if m:  # FIX-CR1
                        log_cands.add(int(m.group(1), 16))  # FIX-CR1

addr_cands = set()  # FIX-CR4
if ADDRS_PATH is not None:  # FIX-CR4
    with open(ADDRS_PATH, encoding="utf-8", errors="replace") as fh:  # FIX-CR4
        for line in fh:  # FIX-CR4
            line = line.split("#", 1)[0].strip()  # FIX-CR4
            if line:  # FIX-CR4
                addr_cands.add(int(line, 16))  # FIX-CR4

split_cands = set()  # FIX-CR2
if SPLIT_RETURNS:  # FIX-CR2
    for j in range(code_lo, code_hi, 4):  # FIX-CR2
        ins = word(j)  # FIX-CR2
        op = ins >> 26  # FIX-CR2
        if op == 3 or (op == 0 and (ins & 0x3F) == 9):  # FIX-CR2
            ret = j + 8  # FIX-CR2
            c = containing(ret)  # FIX-CR2
            if c and c[0] != ret and containing(j) != c and ret not in registered:  # FIX-CR2
                split_cands.add(ret)  # FIX-CR2
    split_sorted = [(w, containing(w)) for w in sorted(split_cands)]  # FIX-CR2
    print("split-returns candidates:", len(split_sorted))  # FIX-CR2
    for w, (fstart, _fend, _fpath) in split_sorted[:30]:  # FIX-CR2
        print("  0x%x (in 0x%x)" % (w, fstart))  # FIX-CR2
    split_lines = ["0x%x (in 0x%x)" % (w, c[0]) for w, c in split_sorted]  # FIX-CR2
    (ROOT / "tools" / "split_returns.txt").write_text("\n".join(split_lines) + ("\n" if split_lines else ""), encoding="utf-8")  # FIX-CR2

todo = []
base_cands = (log_cands | addr_cands) if (LOGS_ONLY or ADDRS_PATH is not None) else (set(cands) | log_cands)  # FIX-CR4
for w in sorted(base_cands | split_cands):  # FIX-CR2
    if (w & 3) != 0:  # FIX-CR1
        continue  # FIX-CR1
    c = containing(w)
    if not c or c[0] == w or w in registered:
        continue
    if w in log_cands or w in addr_cands or w in split_cands or uncond(word(w - 8)) or ((word(w) >> 16) == 0x27BD and (word(w) & 0x8000)):  # FIX-CR4
        todo.append((w, c))
print("hidden entries to patch:", len(todo))
for w, (fstart, _fend, _fpath) in todo:  # FIX-CR1
    print("  0x%x (in 0x%x)" % (w, fstart))  # FIX-CR1

new_reg = []
patched_files = {}
skipped = []
for w, (fstart, fend, fpath) in todo:
    txt = patched_files.get(fpath)
    if txt is None:
        txt = fpath.read_text(encoding="utf-8", errors="surrogateescape")
    hexw = "%x" % w
    changed = False
    # 1. entry switch case
    if not re.search(r"case 0x%s[uU]?:" % hexw, txt):
        m = re.search(r"    switch \(ctx->pc\) \{\n", txt)
        if m:
            txt = txt[: m.end()] + "        case 0x%su: goto label_%s; %s\n" % (hexw, hexw, TAG) + txt[m.end():]
        else:
            # function without alternate entries: create the switch before the first `ctx->pc = <start>u;`
            first = "    ctx->pc = 0x%xu;\n" % fstart
            k = txt.find("\n" + first)
            if k < 0:
                skipped.append((hexw, fpath.name, "no switch / no start stmt"))
                continue
            sw = "\n    switch (ctx->pc) {\n        case 0x%su: goto label_%s; %s\n        default: break;\n    }\n" % (hexw, hexw, TAG)
            txt = txt[: k + 1] + sw + txt[k + 1:]
        changed = True
    # 2. label
    if not re.search(r"^label_%s:" % hexw, txt, re.M):
        lines = txt.split("\n")
        idx = None
        for i, l in enumerate(lines):
            if l.startswith("    // 0x%s:" % hexw) and "(Delay Slot)" not in l:
                idx = i
                break
        if idx is None:
            skipped.append((hexw, fpath.name, "no instruction line"))
            continue
        lines.insert(idx, "label_%s: %s" % (hexw, TAG))
        txt = "\n".join(lines)
        changed = True
    patched_files[fpath] = txt
    slot = (w - 0x100000) >> 2
    if slot < slot_count:
        new_reg.append("        g_ps2RecompiledFunctionTable[%d] = %s; // 0x%s" % (slot, fpath.stem, hexw))
    if changed or True:
        pass

print("files to write:", len(patched_files), "registrations:", len(new_reg), "skipped:", len(skipped))
for s in skipped[:20]:
    print("  skipped", s)

import os, shutil
BK = os.environ.get("PS2X_BACKUP_DIR")
if not DRY:
    if BK:
        pathlib.Path(BK).mkdir(parents=True, exist_ok=True)
        for fpath in list(patched_files) + [reg_path]:
            dst = pathlib.Path(BK) / fpath.name
            if not dst.exists():
                shutil.copy2(fpath, dst)
    for fpath, txt in patched_files.items():
        fpath.write_text(txt, encoding="utf-8", errors="surrogateescape")
    if new_reg:
        anchor = "    }\n};\nstatic const GeneratedFunctionTableInitializer"
        assert reg_text.count(anchor) == 1
        reg_text = reg_text.replace(anchor, "\n".join(new_reg) + "\n" + anchor)
        reg_path.write_text(reg_text, encoding="utf-8", errors="surrogateescape")
    print("patched")
else:
    print("dry run, nothing written")
