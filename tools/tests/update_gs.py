path = 'PS2Recomp/ps2xRuntime/src/lib/gs/gs_cpu_backend.cpp'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. In LoadClutUnlocked: remove loadCsm1Suffix and firstEntry, load all entries into (destinationBase + entry)
old_load = """    const bool loadCsm1Suffix = tex0.csm == 0u && thirtyTwoBit && !fourBit;
    const uint32_t firstEntry = loadCsm1Suffix ? destinationBase : 0u;

    for (uint32_t entry = firstEntry; entry < entryCount; ++entry)"""

new_load = """    for (uint32_t entry = 0u; entry < entryCount; ++entry)"""

if old_load in content:
    content = content.replace(old_load, new_load)
elif old_load.replace('\n', '\r\n') in content:
    content = content.replace(old_load.replace('\n', '\r\n'), new_load.replace('\n', '\r\n'))
else:
    print('Failed to find old_load')

old_dest = """        const uint32_t destination = (loadCsm1Suffix ? entry : destinationBase + entry) & (sixteenBit ? 0x1FFu : 0x0FFu);"""
new_dest = """        const uint32_t destination = (destinationBase + entry) & (sixteenBit ? 0x1FFu : 0x0FFu);"""

if old_dest in content:
    content = content.replace(old_dest, new_dest)
elif old_dest.replace('\n', '\r\n') in content:
    content = content.replace(old_dest.replace('\n', '\r\n'), new_dest.replace('\n', '\r\n'))
else:
    print('Failed to find old_dest')

# 2. In DrawPrimitive: ensure CLUT is loaded for indexed primitives
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

# 3. In LookupCLUT: clean up indexing to match LoadClutUnlocked destination
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

# 4. In WriteVramUnlocked: invalidate texture cache on write
old_write = """void GSCpuBackend::WriteVramUnlocked(uint32_t psm, uint32_t base, uint32_t bw, uint32_t x, uint32_t y, uint32_t value)
{
    if (!m_vram)
        return;
    m_writeVramFuncs[psm & 0x3Fu](m_vram, base, bw, x, y, value);
}"""

new_write = """void GSCpuBackend::WriteVramUnlocked(uint32_t psm, uint32_t base, uint32_t bw, uint32_t x, uint32_t y, uint32_t value)
{
    if (!m_vram)
        return;
    m_texturePageCache.Invalidate();
    m_writeVramFuncs[psm & 0x3Fu](m_vram, base, bw, x, y, value);
}"""

if old_write in content:
    content = content.replace(old_write, new_write)
elif old_write.replace('\n', '\r\n') in content:
    content = content.replace(old_write.replace('\n', '\r\n'), new_write.replace('\n', '\r\n'))
else:
    print('Failed to find old_write')

# 5. In UploadImage: invalidate texture cache on upload
old_upload = """void GSCpuBackend::UploadImage(const uint8_t *data, uint32_t sizeBytes)
{
    std::lock_guard<std::mutex> lock(m_mutex);
    if (!data || sizeBytes == 0u || !m_vram || m_transferState.direction != 0u)
        return;"""

new_upload = """void GSCpuBackend::UploadImage(const uint8_t *data, uint32_t sizeBytes)
{
    std::lock_guard<std::mutex> lock(m_mutex);
    if (!data || sizeBytes == 0u || !m_vram || m_transferState.direction != 0u)
        return;
    m_texturePageCache.Invalidate();"""

if old_upload in content:
    content = content.replace(old_upload, new_upload)
elif old_upload.replace('\n', '\r\n') in content:
    content = content.replace(old_upload.replace('\n', '\r\n'), new_upload.replace('\n', '\r\n'))
else:
    print('Failed to find old_upload')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('gs_cpu_backend.cpp updated successfully')
