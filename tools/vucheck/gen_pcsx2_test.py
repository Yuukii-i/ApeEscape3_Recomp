#!/usr/bin/env python3
"""VC1 part A: generate a PCSX2-side conformance test for VU0 macro (COP2) ops.

Tables taken from PS2Recomp/ps2xRecomp/include/ps2recomp/instructions.h
(VU0MacroSpecial1Functions / VU0MacroSpecial2Functions) and the field split in
PS2Recomp/ps2xRecomp/src/lib/r5900_decoder.cpp (special2 = ((raw>>6)&0x1F)<<2 | raw&3,
funct = 0x3C | (v & 3) for v>=0x00 in special2; fsf = bits 22..21, ftf = bits 24..23 for div/sqrt/rsqrt).

Outputs (in this dir): ops.txt inputs.bin inputs.txt pcsx2_test.bin layout.txt
"""
import os, random, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = 0x01E00000          # guest load address (user to confirm it is free)
SENT = BASE + 0x800        # sentinel quad (0xDEADBEEF x4)
DONE = BASE + 0x810        # done marker word
INPUTS = BASE + 0x1000
STUBS = BASE + 0x2000
RESULTS = BASE + 0x10000   # NOT part of the blob (reserved RAM)
CASE_SZ = 80
REC_SZ = 64
NCASES = 32


def fb(x):
    return struct.unpack('<I', struct.pack('<f', x))[0]


# ---------------------------------------------------------------- tables
S1 = {}
names1 = []
for base, n in (("ADD", 0), ("SUB", 4), ("MADD", 8), ("MSUB", 12), ("MAX", 16), ("MINI", 20), ("MUL", 24)):
    for i, c in enumerate("xyzw"):
        S1[n + i] = "V%s%s" % (base, c)
S1.update({0x1C: "VMULq", 0x1D: "VMAXi", 0x1E: "VMULi", 0x1F: "VMINIi",
           0x20: "VADDq", 0x21: "VMADDq", 0x22: "VADDi", 0x23: "VMADDi",
           0x24: "VSUBq", 0x25: "VMSUBq", 0x26: "VSUBi", 0x27: "VMSUBi",
           0x28: "VADD", 0x29: "VMADD", 0x2A: "VMUL", 0x2B: "VMAX",
           0x2C: "VSUB", 0x2D: "VMSUB", 0x2E: "VOPMSUB", 0x2F: "VMINI"})

S2 = {}
for base, n in (("ADDA", 0), ("SUBA", 4), ("MADDA", 8), ("MSUBA", 12)):
    for i, c in enumerate("xyzw"):
        S2[n + i] = "V%s%s" % (base, c)
for i, c in enumerate(("0", "4", "12", "15")):
    S2[0x10 + i] = "VITOF" + c
    S2[0x14 + i] = "VFTOI" + c
for i, c in enumerate("xyzw"):
    S2[0x18 + i] = "VMULA" + c
S2.update({0x1C: "VMULAq", 0x1D: "VABS", 0x1E: "VMULAi", 0x1F: "VCLIPw",
           0x20: "VADDAq", 0x21: "VMADDAq", 0x22: "VADDAi", 0x23: "VMADDAi",
           0x24: "VSUBAq", 0x25: "VMSUBAq", 0x26: "VSUBAi", 0x27: "VMSUBAi",
           0x28: "VADDA", 0x29: "VMADDA", 0x2A: "VMULA", 0x2C: "VSUBA",
           0x2D: "VMSUBA", 0x2E: "VOPMULA", 0x2F: "VNOP",
           0x30: "VMOVE", 0x31: "VMR32", 0x38: "VDIV", 0x39: "VSQRT",
           0x3A: "VRSQRT", 0x3B: "VWAITQ"})

CO = 0x4A000000


def enc1(f, dest, ft, fs, fd):
    return CO | (dest << 21) | (ft << 16) | (fs << 11) | (fd << 6) | f


def enc2(v, dest, ft, fs):
    return CO | (dest << 21) | (ft << 16) | (fs << 11) | ((v >> 2) << 6) | (0x3C | (v & 3))


def decode(w):
    """Reverse: return (name, dest, ft, fs, fd_or_sel)"""
    f = w & 0x3F
    dest = (w >> 21) & 0xF
    ft = (w >> 16) & 0x1F
    fs = (w >> 11) & 0x1F
    fd = (w >> 6) & 0x1F
    if f >= 0x3C:
        v = (fd << 2) | (w & 3)
        return S2.get(v, "?s2_%02x" % v), dest, ft, fs, fd
    return S1.get(f, "?s1_%02x" % f), dest, ft, fs, fd


DESTS = ((0xF, "xyzw"), (0x1, "w"), (0xC, "xy"))
ops = []  # (name, word, needs_wait)

# special1: all arithmetic 0x00..0x2F, vf3 = fd, vf1 = fs, vf2 = ft (q/i variants ft=0)
for f in range(0x30):
    nm = S1[f]
    qi = nm.endswith("q") or nm.endswith("i")
    ft = 0 if qi else 2
    if nm == "VOPMSUB":
        ops.append(("VOPMSUB.xyz", enc1(f, 0xE, 2, 1, 3), False))
        continue
    for d, ds in DESTS:
        ops.append(("%s.%s" % (nm, ds), enc1(f, d, ft, 1, 3), False))

# special2 ACC ops + conversions
for v in range(0x30):
    if v not in S2:
        continue
    nm = S2[v]
    if nm in ("VNOP", "VCLIPw", "VOPMULA"):
        continue
    qi = nm.endswith("q") or nm.endswith("i")
    if nm in ("VITOF0", "VITOF4", "VITOF12", "VITOF15", "VFTOI0", "VFTOI4",
              "VFTOI12", "VFTOI15", "VABS", "VMOVE", "VMR32"):
        ft, fs = 3, 1          # ft is the destination register
    else:
        ft, fs = (0 if qi else 2), 1
    for d, ds in DESTS:
        ops.append(("%s.%s" % (nm, ds), enc2(v, d, ft, fs), False))
# VMOVE/VMR32 live at 0x30/0x31 (loop above covers range(0x30) so add explicitly)
for v in (0x30, 0x31):
    for d, ds in DESTS:
        ops.append(("%s.%s" % (S2[v], ds), enc2(v, d, 3, 1), False))
ops.append(("VOPMULA.xyz", enc2(0x2E, 0xE, 2, 1), False))
ops.append(("VCLIPw.xyz", enc2(0x1F, 0xF, 2, 1), False))
# div / sqrt / rsqrt (+VWAITQ); fsf bits 22..21, ftf bits 24..23
for (fsf, ftf) in ((0, 0), (1, 3), (3, 2), (2, 1)):
    sel = "fs%s_ft%s" % ("xyzw"[fsf], "xyzw"[ftf])
    ops.append(("VDIV.%s" % sel, enc2(0x38, (ftf << 2) | fsf, 2, 1), True))
for ftf in range(4):
    ops.append(("VSQRT.ft%s" % "xyzw"[ftf], enc2(0x39, ftf << 2, 2, 0), True))
for (fsf, ftf) in ((0, 0), (1, 3), (3, 2), (2, 1)):
    sel = "fs%s_ft%s" % ("xyzw"[fsf], "xyzw"[ftf])
    ops.append(("VRSQRT.%s" % sel, enc2(0x3A, (ftf << 2) | fsf, 2, 1), True))

# dest-position fix: the dest field bits 24..21 are x=0x8,y=0x4,z=0x2,w=0x1 (already the case above)
# BUT div/sqrt use (ftf<<2|fsf) as the 4-bit field: ftf = bits 24..23 = field>>2, fsf = bits 22..21 = field&3. ok.

assert len(ops) >= 150, len(ops)
NOPS = len(ops)

with open(os.path.join(HERE, "ops.txt"), "w") as fh:
    for nm, w, _ in ops:
        fh.write("%s 0x%08X\n" % (nm, w))

# ---------------------------------------------------------------- inputs
rng = random.Random(0xA3E5)


def q4(*v):
    return [x if isinstance(x, int) else fb(x) for x in v]


def rnd_norm():
    e = rng.randint(-20, 20)
    m = rng.uniform(1.0, 2.0)
    return fb((-1 if rng.random() < 0.5 else 1) * m * (2.0 ** e))


def rnd_vec():
    return [rnd_norm() for _ in range(4)]


cases = []  # (vf1, vf2)
cases.append((q4(1.5, -2.25, 3.75, 0.1), q4(0.5, 4.0, -1.25, 7.0)))                          # 0 normal
cases.append((q4(0x00000000, 0x80000000, 0x00000000, 0x80000000), q4(0, 0, 0x80000000, 0x80000000)))  # 1 +-0
cases.append((q4(0x1, 0x007fffff, 0x80000001, 0x1), q4(0x007fffff, 0x80000001, 0x1, 0x00800000)))      # 2 denormals
cases.append((q4(0x7f800000, 0xff800000, 0x7fffffff, 0xffffffff), q4(0x3f800000, 0x7f800000, 0x7fc00000, 0xff800000)))  # 3 exp255
cases.append((q4(0x7fc00000, 0x7f800000, 0xff800000, 0x7fffffff), q4(0x7fffffff, 0x7f800000, 0x3f800000, 0xffffffff)))  # 4
cases.append((q4(0x7f7fffff, 0xff7fffff, 0x7f7fffff, 0x00800000), q4(0x7f7fffff, 0x7f7fffff, 2.0, 1.0)))  # 5 max normal / overflow
cases.append((q4(0x00800000, 0x80800000, 0x00800000, 0x00800001), q4(0.5, 0.5, 0x80800000, 0x00800000)))  # 6 tiny / underflow
cases.append((q4(1.0, -1.0, 2.5, 1e10), q4(-1.0, 1.0, -2.5, -1e10)))                           # 7 cancellation
cases.append((q4(0x3f800001, 0x3f800000, 0xbf800001, 0x40000001), q4(0xbf800000, 0xbf800001, 0x3f800001, 0xc0000000)))  # 8 1ulp cancel
cases.append((q4(1e10, 1.0, 1e-10, 3.0), q4(1.0, 1e10, 1.0, 1e-10)))                            # 9 exp gaps
cases.append((q4(16777216.0, 1.0, 1e30, 1e-30), q4(1.0, 16777216.0, 1.0, 1e30)))                # 10 gaps >=24
cases.append((q4(3e9, -3e9, 2147483648.0, -2147483648.0), q4(2147483520.0, -2147483904.0, 1e10, -1e10)))  # 11 ftoi big
cases.append((q4(1e-9, 0.5, 1.5, 2.5), q4(-0.5, -1.5, -2.5, 0x3efffffe)))                       # 12 ftoi ties
cases.append((q4(4096.0, 16.0, 524288.0, 65536.0), q4(0.0625, 1.0 / 4096, 32768.0, 1048576.0)))  # 13 ftoi scaled
cases.append((q4(1.0, -1.0, 1.0, 5.0), q4(0.0, 0.0, 0.0, 1.0)))                                 # 14 clip |x|==w
cases.append((q4(0x3f800001, 0xbf800001, 0.5, 0.0), q4(0.0, 0.0, 0.0, 1.0)))                    # 15 clip 1ulp above
cases.append((q4(-1.0, 2.0, -3.0, 0.0), q4(0.0, 0.0, 0.0, -1.0)))                              # 16 clip negative w
cases.append((q4(0x3f7fffff, 0xbf7fffff, 2.0, 1.0), q4(0.0, 0.0, 0.0, 1.0)))                   # 17 clip 1ulp below
cases.append((q4(0, 1, 0xffffffff, 0x7fffffff), q4(0x80000000, 0x40000000, 2, 3)))              # 18 itof ints
cases.append((q4(0x80000000, 0x40000000, 0x00ffffff, 0x01000000), q4(0xffffff00, 0x100, 16, 255)))  # 19 itof ints 2
cases.append((q4(1.0, -1.0, 0.0, 2.0), q4(0.0, 0x80000000, 0.0, 4.0)))                          # 20 div by zero / 0/0
cases.append((q4(4.0, 9.0, 2.0, 1e30), q4(-4.0, 9.0, 1e-30, 1e30)))                            # 21 sqrt of negative etc
cases.append((q4(0x7f7fffff, 0x00800000, 1.0, 3.0), q4(0x00800000, 0x7f7fffff, 3.0, 1.0)))      # 22 div ovf/underflow
cases.append((q4(0x80000000, 0x00000000, 0x80800000, 0x7f7fffff), q4(0x80000000, 0x80800000, 0x00000000, 0xff7fffff)))  # 23
while len(cases) < NCASES:
    cases.append((rnd_vec(), rnd_vec()))

special_vals = [3.0, -0.5, 1e10, 0x7f7fffff, 0x1, 0x80000000, 0x7f800000, 1.0,
                0x7fffffff, 0x00800000, -2.0, 0x007fffff]


def sv(i):
    v = special_vals[i % len(special_vals)]
    return v if isinstance(v, int) else fb(v)


acc_special = {2: (q4(0x1, 0x007fffff, 0x80000001, 0x00800000), q4(1.0, 1.0, 1.0, 1.0)),
               3: (q4(0x7fc00000, 0x7f800000, 1.0, 2.0), q4(1.0, 1.0, 1.0, 1.0)),
               5: (q4(0x7f7fffff, 0x7f7fffff, 0xff7fffff, 1.0), q4(2.0, 2.0, 2.0, 1.0)),
               7: (q4(1.0, -1.0, 2.5, 1e10), q4(1.0, 1.0, 1.0, 1.0)),
               9: (q4(1e10, 1.0, 1e-10, 3.0), q4(1.0, 1.0, 1.0, 1.0)),
               6: (q4(0x00800000, 0x80800000, 1e-30, 0x00800000), q4(0.5, 0.5, 1e-10, 0.5))}

blob_in = bytearray()
txt = ["# inputs: case | vf1 | vf2 | vf6 | vf7 | I | Q  (hex bit patterns, lanes x y z w)"]
for i, (a, b) in enumerate(cases):
    if i in acc_special:
        v6, v7 = acc_special[i]
    else:
        v6, v7 = rnd_vec(), rnd_vec()
    I = sv(i)
    Q = sv(i + 5)
    rec = struct.pack('<16I', *(a + b + v6 + v7)) + struct.pack('<4I', I, Q, 0, 0)
    assert len(rec) == CASE_SZ
    blob_in += rec
    h = lambda v: " ".join("%08x" % x for x in v)
    txt.append("%02d | %s | %s | %s | %s | I=%08x | Q=%08x" % (i, h(a), h(b), h(v6), h(v7), I, Q))
open(os.path.join(HERE, "inputs.bin"), "wb").write(blob_in)
open(os.path.join(HERE, "inputs.txt"), "w").write("\n".join(txt) + "\n")

# ---------------------------------------------------------------- MIPS
R = dict(zero=0, t0=8, t1=9, s0=16, s1=17, s2=18, s3=19, s4=20, s5=21, ra=31)


def lui(rt, imm): return (0x0F << 26) | (rt << 16) | (imm & 0xFFFF)
def ori(rt, rs, imm): return (0x0D << 26) | (rs << 21) | (rt << 16) | (imm & 0xFFFF)
def addiu(rt, rs, imm): return (0x09 << 26) | (rs << 21) | (rt << 16) | (imm & 0xFFFF)
def lw(rt, off, rs): return (0x23 << 26) | (rs << 21) | (rt << 16) | (off & 0xFFFF)
def sw(rt, off, rs): return (0x2B << 26) | (rs << 21) | (rt << 16) | (off & 0xFFFF)
def lqc2(vt, off, rs): return (0x36 << 26) | (rs << 21) | (vt << 16) | (off & 0xFFFF)
def sqc2(vt, off, rs): return (0x3E << 26) | (rs << 21) | (vt << 16) | (off & 0xFFFF)
def ctc2(rt, vi): return (0x12 << 26) | (6 << 21) | (rt << 16) | (vi << 11)
def cfc2(rt, vi): return (0x12 << 26) | (2 << 21) | (rt << 16) | (vi << 11)
def jalr(rs, rd=31): return (rs << 21) | (rd << 11) | 0x09
def jr(rs): return (rs << 21) | 0x08
def bne(rs, rt, off): return (0x05 << 26) | (rs << 21) | (rt << 16) | (off & 0xFFFF)
def beq(rs, rt, off): return (0x04 << 26) | (rs << 21) | (rt << 16) | (off & 0xFFFF)


NOP = 0
DI = 0x42000039
VWAITQ = 0x4A0003BF
VMULA_6_7 = enc2(0x2A, 0xF, 7, 6)                     # VMULA.xyzw ACC = vf6 * vf7
VMADDx_5 = enc1(0x08, 0xF, 0, 0, 5)                   # vmaddx.xyzw vf5, vf0, vf0x : vf5 = ACC + vf0*vf0.x


def li(r, v): return [lui(r, v >> 16), ori(r, r, v & 0xFFFF)]


code = []
code.append(DI)
code += li(R['s0'], STUBS)
code += li(R['s1'], RESULTS)
code += li(R['s2'], NOPS)
code += li(R['s5'], SENT)
outer = len(code)
code += li(R['s3'], INPUTS)
code.append(addiu(R['s4'], R['zero'], NCASES))
inner = len(code)
code += [lqc2(1, 0, R['s3']), lqc2(2, 16, R['s3']), lqc2(6, 32, R['s3']), lqc2(7, 48, R['s3']),
         lw(R['t0'], 64, R['s3']), ctc2(R['t0'], 21),    # I  = vi21
         lw(R['t0'], 68, R['s3']), ctc2(R['t0'], 22),    # Q  = vi22
         lqc2(3, 0, R['s5']),                            # vf3 sentinel
         VMULA_6_7,                                      # seed ACC
         ctc2(R['zero'], 16), ctc2(R['zero'], 17), ctc2(R['zero'], 18),  # clear status/mac/clip
         jalr(R['s0']), NOP,
         sqc2(3, 0, R['s1']),
         cfc2(R['t0'], 16), sw(R['t0'], 32, R['s1']),
         cfc2(R['t0'], 17), sw(R['t0'], 36, R['s1']),
         cfc2(R['t0'], 18), sw(R['t0'], 40, R['s1']),
         cfc2(R['t0'], 22), sw(R['t0'], 44, R['s1']),
         cfc2(R['t0'], 21), sw(R['t0'], 48, R['s1']),
         VMADDx_5, sqc2(5, 16, R['s1']),
         sw(R['zero'], 52, R['s1']), sw(R['zero'], 56, R['s1']), sw(R['zero'], 60, R['s1']),
         addiu(R['s1'], R['s1'], REC_SZ), addiu(R['s3'], R['s3'], CASE_SZ), addiu(R['s4'], R['s4'], -1)]
code.append(bne(R['s4'], R['zero'], inner - (len(code) + 1)))
code.append(NOP)
code += [addiu(R['s0'], R['s0'], 16), addiu(R['s2'], R['s2'], -1)]
code.append(bne(R['s2'], R['zero'], outer - (len(code) + 1)))
code.append(NOP)
code += li(R['t0'], DONE) + li(R['t1'], 0x600DF00D) + [sw(R['t1'], 0, R['t0'])]
done_pc = BASE + 4 * len(code)
code.append(beq(0, 0, -1))   # infinite loop at done_pc
code.append(NOP)
assert 4 * len(code) < 0x800

blob_end = STUBS - BASE + 16 * NOPS
blob = bytearray(blob_end)
for i, w in enumerate(code):
    struct.pack_into('<I', blob, 4 * i, w)
struct.pack_into('<4I', blob, SENT - BASE, *([0xDEADBEEF] * 4))
blob[INPUTS - BASE:INPUTS - BASE + len(blob_in)] = blob_in
for i, (nm, w, wait) in enumerate(ops):
    off = STUBS - BASE + 16 * i
    struct.pack_into('<4I', blob, off, w, VWAITQ if wait else NOP, jr(R['ra']), NOP)
open(os.path.join(HERE, "pcsx2_test.bin"), "wb").write(blob)

lay = ["blob_load_address   0x%08X (size 0x%X)" % (BASE, len(blob)),
       "harness_entry       0x%08X" % BASE,
       "done_pc             0x%08X (infinite loop; bp here)" % done_pc,
       "done_marker         0x%08X (== 0x600DF00D when finished)" % DONE,
       "sentinel_quad       0x%08X" % SENT,
       "input_table         0x%08X (%d cases x %d bytes)" % (INPUTS, NCASES, CASE_SZ),
       "op_stub_table       0x%08X (%d ops x 16 bytes: op; vwaitq|nop; jr ra; nop)" % (STUBS, NOPS),
       "result_table        0x%08X (%d ops x %d cases x %d bytes = 0x%X; NOT in blob)" % (RESULTS, NOPS, NCASES, REC_SZ, NOPS * NCASES * REC_SZ),
       "result_end          0x%08X" % (RESULTS + NOPS * NCASES * REC_SZ),
       "record_layout       vf3[0x00] acc[0x10] status[0x20] mac[0x24] clip[0x28] Q[0x2C] I[0x30] pad[0x34..0x3F]",
       "result_index        (op_index*%d + case)*%d from result_table; op order = ops.txt line order" % (NCASES, REC_SZ),
       "num_ops             %d" % NOPS, "num_cases           %d" % NCASES]
open(os.path.join(HERE, "layout.txt"), "w").write("\n".join(lay) + "\n")

# ---------------------------------------------------------------- sanity
print("ops=%d blob=0x%X done_pc=0x%08X result_end=0x%08X" % (NOPS, len(blob), done_pc, RESULTS + NOPS * NCASES * REC_SZ))
step = max(1, NOPS // 10)
for i in range(0, NOPS, step)[:10]:
    nm, w, _ = ops[i]
    dn, dest, ft, fs, fd = decode(w)
    print("%-16s 0x%08X -> %-10s dest=%x ft=%d fs=%d fd/sel=%d" % (nm, w, dn, dest, ft, fs, fd))
# every op must round-trip to its own base name
bad = 0
for nm, w, _ in ops:
    dn = decode(w)[0]
    if not nm.startswith(dn):
        bad += 1
        print("MISMATCH", nm, hex(w), dn)
print("roundtrip mismatches:", bad)
sys.exit(1 if bad else 0)
