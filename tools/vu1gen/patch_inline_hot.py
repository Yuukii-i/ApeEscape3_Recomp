"""PERF-INL: inline the generic lower/upper ops that VU1 hot blocks still reach through function pointers (idempotent).
Exact re-statements of VU1Interpreter::execLower / execUpper for B, BAL, JR, JALR, IBLTZ/IBGTZ/IBLEZ/IBGEZ, ISUBIU, DIV, SQRT, RSQRT, WAITQ and CLIP
(the op.execLower wrapper only adds flgSyncReader for opcodes 0x10..0x1C, none of which is inlined here). Also drops two kinds of dead per-pair stores:
  - vu.m_currentUpperInstruction = ... (only read inside the interpreter's own execUpper helpers, which set it themselves)
  - the vf0/vi0 canonicalisation, when every statement of the pair is known not to write register 0
Run after patch_lean_hot.py / patch_loop_hot.py. Usage: python tools/vu1gen/patch_inline_hot.py"""
import pathlib
import re
import sys

GEN = pathlib.Path(__file__).resolve().parent.parent.parent / "PS2Recomp/ps2xRuntime/src/lib/vu/generated"
TAG = "PERF-INL"
UNIT = 0 if "--vu0" in sys.argv else 1  # --vu0: patch generated/vu0_hot_blocks.cpp (EE-thread VU0 microprograms) instead of the VU1 file
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
PFX = "vu0H_" if UNIT == 0 else "vuH_"
IMAGE = "d985722524327b89" if UNIT == 0 else "86503d3905e35276"
PCMASK = 0x0FFF if UNIT == 0 else 0x3FFF

LOWER = re.compile(r"^(\s*)op\.execLower\(vu, 0x([0-9a-f]+)u, c\.vuData, c\.dataSize, \*c\.gs, c\.memory, 0x([0-9a-f]+)u\);\s*$")
UPPER = re.compile(r"^(\s*)op\.execUpper\(vu, 0x([0-9a-f]+)u\);\s*$")
PAIR = re.compile(r"^\s*\{ // pair (\d+) @ ([0-9A-F]+)$")
RESET = "st.vf[0][0] = 0.0f; st.vf[0][1] = 0.0f; st.vf[0][2] = 0.0f; st.vf[0][3] = 1.0f; st.vi[0] = 0;"


def imm11(w):
    v = w & 0x7FF
    return v - 0x800 if v & 0x400 else v


def branch(pc, w, cond=None):
    tgt = (pc + 8 + imm11(w) * 8) & PCMASK
    body = "{ st.branchPending = true; st.branchTarget = 0x%04Xu; st.branchDelay = 1; }" % tgt
    return body if cond is None else "if (%s) %s" % (cond, body)


def inline_lower(pc, w):
    op7 = (w >> 25) & 0x7F
    vis, vit = (w >> 11) & 0x1F, (w >> 16) & 0x1F
    if op7 == 0x20:
        return [branch(pc, w)]
    if op7 == 0x21:
        out = ["if (%d != 0) st.vi[%d] = static_cast<int32_t>(0x%xu);" % (vit, vit, (pc + 16) // 8)] if vit else []
        return out + [branch(pc, w)]
    if op7 in (0x24, 0x25):
        out = ["const uint32_t jt = (static_cast<uint32_t>(static_cast<uint16_t>(vuhot::readBranchVi(vu, %d))) * 8u) & 0x%Xu;" % (vis, PCMASK)]
        if op7 == 0x25 and vit:
            out.append("st.vi[%d] = static_cast<int32_t>(0x%xu);" % (vit, (pc + 16) // 8))
        out.append("st.branchPending = true; st.branchTarget = jt; st.branchDelay = 1;")
        return ["{"] + ["    " + s for s in out] + ["}"]
    if op7 in (0x2C, 0x2D, 0x2E, 0x2F):
        rel = {0x2C: "< 0", 0x2D: "> 0", 0x2E: "<= 0", 0x2F: ">= 0"}[op7]
        return [branch(pc, w, "static_cast<int16_t>(vuhot::readBranchVi(vu, %d)) %s" % (vis, rel))]
    if op7 == 0x09:
        imm = (w & 0x7FF) | ((w >> 10) & 0x7800)
        return ["if (%d != 0) st.vi[%d] = static_cast<int16_t>(st.vi[%d] - %d);" % (vit, vit, vis, imm)] if vit else ["// ISUBIU to vi0"]
    if op7 == 0x40 and (w & 0x3F) >= 0x3C:
        f2 = (w & 3) | ((w >> 4) & 0x7C)
        fsf, ftf = (w >> 21) & 3, (w >> 23) & 3
        if f2 == 0x38:
            return ["vuhot::divQ(vu, c, %d, %d, %d, %d);" % (vis, fsf, vit, ftf)]
        if f2 == 0x39:
            return ["vuhot::sqrtQ(vu, c, %d, %d);" % (vit, ftf)]
        if f2 == 0x3A:
            return ["vuhot::rsqrtQ(vu, c, %d, %d, %d, %d);" % (vis, fsf, vit, ftf)]
        if f2 == 0x3B:
            return ["// WAITQ"]
    return None


# does this statement write vf0 / vi0?  True = yes, False = no, None = unknown (keep the canonicalisation)
RE_FMAC = re.compile(r"vuhot::fmac<\d+, \d+, \d+, (true|false), (\d+), (?:true|false)>\(vu, \d+u, \d+, \d+, (\d+)\);")
RE_MAXMINI = re.compile(r"vuhot::maxmini<(?:true|false), \d+, \d+, (\d+)>\(st, \d+, \d+, (\d+)\);")
RE_FTOI = re.compile(r"vuhot::ftoi<-?\d+, (\d+)>\(st, \d+, (\d+)\);")
RE_MOVE = re.compile(r"vuhot::(?:move|mr32)\(st, (\d+), (\d+), (\d+)\);")
RE_LQ = re.compile(r"vuhot::lq\(st, c\.vuData, c\.dataSize, (\d+), (\d+), (\d+), -?\d+\);")
RE_LQI = re.compile(r"vuhot::lqi\(st, c\.vuData, c\.dataSize, (\d+), (\d+), (\d+)\);")
RE_SQI = re.compile(r"vuhot::sqi\(st, c\.dataSize, \d+, \d+, (\d+), qs\);")
RE_SQ = re.compile(r"vuhot::(?:sq|isw)\(st, c\.dataSize, \d+, \d+, \d+, -?\d+, qs\);")
RE_ILW = re.compile(r"vuhot::ilw\(st, c\.vuData, c\.dataSize, \d+, \d+, \d+, -?\d+\);")
RE_VI = re.compile(r"st\.vi\[(\d+)\] = ")
SAFE_PREFIX = ("const int32_t oldVi", "vu.m_", "st.pc", "if (st.branchPending)", "{ st.branch", "if (static_cast<int16_t>", "if (", "}", "{", "else",
               "// ", "++", "--", "c.", "const uint32_t jt", "st.branchPending", "st.q", "vuhot::divQ", "vuhot::sqrtQ", "vuhot::rsqrtQ", "vuhot::clip",
               "const uint32_t currentDi", "st.status")


def writes_zero(s):
    s = s.strip()
    if not s:
        return False
    if s.startswith("st.vf[0][0] = 0.0f"):
        return False
    m = RE_FMAC.match(s)
    if m:
        return m.group(1) == "false" and int(m.group(2)) != 0 and int(m.group(3)) == 0
    m = RE_MAXMINI.match(s)
    if m:
        return int(m.group(1)) != 0 and int(m.group(2)) == 0
    m = RE_FTOI.match(s)
    if m:
        return int(m.group(1)) != 0 and int(m.group(2)) == 0
    m = RE_MOVE.match(s)
    if m:
        return int(m.group(1)) != 0 and int(m.group(2)) == 0
    m = RE_LQ.match(s)
    if m:
        return int(m.group(1)) != 0 and int(m.group(2)) == 0
    m = RE_LQI.match(s)
    if m:
        return (int(m.group(1)) != 0 and int(m.group(2)) == 0) or int(m.group(3)) == 0
    m = RE_SQI.match(s)
    if m:
        return int(m.group(1)) == 0
    if RE_SQ.match(s) or RE_ILW.match(s):
        return False
    m = RE_VI.match(s)
    if m:
        return int(m.group(1)) == 0
    if s.startswith(SAFE_PREFIX):
        return False
    return None


def process_pair(lines):
    """lines: one '{ // pair' ... '}' group. Returns (new lines, counters)."""
    cnt = dict(lower=0, upper=0, cui=0, reset=0)
    pc = int(PAIR.match(lines[0]).group(2), 16)
    out = []
    for ln in lines:
        m = LOWER.match(ln)
        if m:
            rep = inline_lower(pc, int(m.group(2), 16))
            if rep is not None:
                ind = m.group(1)
                out.extend(ind + r + (" // " + TAG if k == 0 else "") for k, r in enumerate(rep))
                cnt["lower"] += 1
                continue
        m = UPPER.match(ln)
        if m:
            u = int(m.group(2), 16)
            if (u & 0x3F) >= 0x3C and ((u & 3) | ((u >> 4) & 0x7C)) == 0x1F:
                out.append("%svuhot::clip(vu, %d, %d); // %s" % (m.group(1), (u >> 11) & 0x1F, (u >> 16) & 0x1F, TAG))
                cnt["upper"] += 1
                continue
        if re.match(r"^\s*vu\.m_currentUpperInstruction = 0x[0-9a-f]+u;", ln):
            cnt["cui"] += 1
            continue
        out.append(ln)
    # vf0 / vi0 canonicalisation
    wz = [writes_zero(s) for s in out[1:]]
    if all(w is False for w in wz) and any(s.strip() == RESET for s in out):
        out = [s for s in out if s.strip() != RESET]
        cnt["reset"] += 1
    return out, cnt


p = GEN / ("vu%d_hot_blocks.cpp" % UNIT)
t = p.read_text(encoding="utf-8", errors="surrogateescape")
if TAG in t:
    print("already patched")
    raise SystemExit
lines = t.split("\n")
res = []
tot = dict(lower=0, upper=0, cui=0, reset=0, pairs=0)
i = 0
while i < len(lines):
    if PAIR.match(lines[i]):
        # the pair's closing brace: track brace depth (the branch-resolution block inside a pair also closes with "    }")
        depth = 0
        j = i
        while True:
            depth += lines[j].count("{") - lines[j].count("}")
            if depth == 0:
                break
            j += 1
        grp, cnt = process_pair(lines[i:j + 1])
        res.extend(grp)
        for k in cnt:
            tot[k] += cnt[k]
        tot["pairs"] += 1
        i = j + 1
        continue
    res.append(lines[i])
    i += 1
out = "\n".join(res)
out = out.replace("static int %s0(" % PFX, "// " + TAG + ": inline lower/upper ops, dead stores dropped (tools/vu1gen/patch_inline_hot.py)\nstatic int %s0(" % PFX, 1)
p.write_text(out, encoding="utf-8", errors="surrogateescape")
print("pairs", tot["pairs"], "lower ops inlined", tot["lower"], "clips inlined", tot["upper"], "currentUpper stores dropped", tot["cui"], "vf0 resets dropped", tot["reset"])
