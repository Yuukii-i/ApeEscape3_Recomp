path = 'PS2Recomp/ps2xRuntime/src/lib/gs/gs_cpu_backend.cpp'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. In DrawPrimitive: ensure CLUT is loaded for indexed primitives
old_draw = """    switch (state.prim.type)
    {
    case GS_PRIM_SPRITE:"""

new_draw = """    if (state.prim.tme && (isFourBitIndexedPsm(ctx.tex0.psm) || isEightBitIndexedPsm(ctx.tex0.psm)))
    {
        LoadClutUnlocked(ctx.tex0, state.texclut);
    }

    switch (state.prim.type)
    {
    case GS_PRIM_SPRITE:"""

if old_draw in content:
    content = content.replace(old_draw, new_draw)
elif old_draw.replace('\n', '\r\n') in content:
    content = content.replace(old_draw.replace('\n', '\r\n'), new_draw.replace('\n', '\r\n'))
else:
    print('Failed to find old_draw')

# 2. In LookupCLUT: simplified clutIndex
old_lookup = """    uint32_t clutIndex = (clutBase + sourceIndex) & (sixteenBit ? 0x1FFu : 0x0FFu);
    if (!sixteenBit && csm == 0u && isEightBitIndexedPsm(sourcePsm))
    {
        const uint32_t block = std::min((sourceIndex & 0xF0u) + clutBase, 240u);
        clutIndex = block + (sourceIndex & 0x0Fu);
    }"""

new_lookup = """    const uint32_t clutIndex = (clutBase + sourceIndex) & (sixteenBit ? 0x1FFu : 0x0FFu);"""

if old_lookup in content:
    content = content.replace(old_lookup, new_lookup)
elif old_lookup.replace('\n', '\r\n') in content:
    content = content.replace(old_lookup.replace('\n', '\r\n'), new_lookup.replace('\n', '\r\n'))
else:
    print('Failed to find old_lookup')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Step 0 changes applied successfully')
