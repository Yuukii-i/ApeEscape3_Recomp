"""C329: nine generated functions end on a branch/jump whose delay-slot instruction fell into the next function
range and was never emitted (e.g. sub_00352E0C: b 0x352ED8 lost `qmtc2 s1, vf02`, which broke the swing distance test).
Inserts the missing delay-slot instruction. Patches recomp_source in place; idempotent. Usage: python tools/fix_delay_slots.py [--dry]"""
import pathlib, sys

SRC = pathlib.Path(__file__).resolve().parent.parent / "recomp_source"
DRY = "--dry" in sys.argv
TAG = "// C329 (lost delay slot)"

# (file, anchor line(s) that the delay slot must follow, delay-slot code)
SITES = [
    ("sub_001000A0_0x1000a0.cpp", "    ctx->pc = 0x10010Cu;\n    {\n        const uint32_t jumpTarget",
     "SET_GPR_S32(ctx, 29, (int32_t)ADD32(GPR_U32(ctx, 29), 16)); // addiu sp, sp, 0x10"),
    ("sub_0017FEA0_0x17fea0.cpp", "        if (branch_taken_0x17fffc) {\n            ctx->pc = 0x180020u;",
     "SET_GPR_S32(ctx, 15, (int32_t)READ32(ADD32(GPR_U32(ctx, 16), 12))); // lw t7, 0xC(s0) (bnel: only when taken)"),
    ("sub_0031734C_0x31734c.cpp", "    ctx->pc = 0x31736Cu;\n    SET_GPR_U32(ctx, 31, 0x317374u);",
     "WRITE128(ADD32(GPR_U32(ctx, 29), 16), GPR_VEC(ctx, 14)); // sq t6, 0x10(sp)"),
    ("sub_00326194_0x326194.cpp", "    ctx->pc = 0x326268u;\n    SET_GPR_U32(ctx, 31, 0x326270u);",
     "{ uint32_t bits = READ32(GPR_U32(ctx, 15)); std::memcpy(&ctx->f[13], &bits, sizeof(bits)); } // lwc1 f13, 0(t7)"),
    ("sub_003269B0_0x3269b0.cpp", "    ctx->pc = 0x326C68u;\n    SET_GPR_U32(ctx, 31, 0x326C70u);",
     "SET_GPR_U64(ctx, 4, (uint64_t)GPR_U64(ctx, 16) + (uint64_t)GPR_U64(ctx, 0)); // daddu a0, s0, zero"),
    ("sub_003507D0_0x3507d0.cpp", "    ctx->pc = 0x3507FCu;\n    SET_GPR_U32(ctx, 31, 0x350804u);",
     "SET_GPR_S32(ctx, 4, (int32_t)ADD32(GPR_U32(ctx, 4), 12584)); // addiu a0, a0, 0x3128"),
    ("sub_00352E0C_0x352e0c.cpp", "    ctx->pc = 0x353130u;\n    {\n        const bool branch_taken_0x353130",
     "ctx->vu0_vf[2] = _mm_castsi128_ps(GPR_VEC(ctx, 17)); // qmtc2 s1, vf02"),
    ("sub_00360554_0x360554.cpp", "    ctx->pc = 0x3607FCu;\n    {\n        const uint32_t jumpTarget",
     "SET_GPR_S32(ctx, 29, (int32_t)ADD32(GPR_U32(ctx, 29), 48)); // addiu sp, sp, 0x30"),
    ("sub_00372F60_0x372f60.cpp", "    ctx->pc = 0x37302Cu;\n    SET_GPR_U32(ctx, 31, 0x373034u);",
     "SET_GPR_U64(ctx, 5, (uint64_t)GPR_U64(ctx, 29) + (uint64_t)GPR_U64(ctx, 0)); // daddu a1, sp, zero"),
]

done = 0
for name, anchor, code in SITES:
    f = SRC / name
    txt = f.read_text(encoding="utf-8", errors="surrogateescape")
    if TAG in txt:
        print(name, "already patched")
        continue
    if txt.count(anchor) != 1:
        print(name, "ANCHOR COUNT", txt.count(anchor), "- skipped")
        continue
    first, rest = anchor.split("\n", 1)
    # the delay slot goes right after the first anchor line (the `ctx->pc = ...` or `if (taken) {` line)
    new = first + "\n    " + code + " " + TAG + "\n" + rest
    if not DRY:
        f.write_text(txt.replace(anchor, new), encoding="utf-8", errors="surrogateescape")
    print(name, "patched" if not DRY else "would patch")
    done += 1
print("done", done, "dry" if DRY else "")
