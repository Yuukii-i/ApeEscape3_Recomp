# Patch ps2_vif1_interpreter.cpp
with open('PS2Recomp/ps2xRuntime/src/lib/ps2_vif1_interpreter.cpp', 'rb') as f:
    content = f.read()

target1 = b'''            if (qwCount > 0)
            {
                const bool directHl = (opcode == VIF_DIRECTHL);
                submitGifPacket(GifPathId::Path2, data + pos, qwCount * 16, true, directHl);'''

replacement1 = b'''            if (qwCount > 0)
            {
                if (qwCount == 512 || qwCount == 64)
                {
                    static int s_vifSubmitCount = 0;
                    if (s_vifSubmitCount++ < 10)
                    {
                        std::fprintf(stderr, "[VIF1:SUBMIT_DIRECT] qwCount=%u pos=%u sizeBytes=%u first8=[%u,%u,%u,%u,%u,%u,%u,%u]\\n",
                                     qwCount, pos, sizeBytes,
                                     data[pos], data[pos+1], data[pos+2], data[pos+3],
                                     data[pos+4], data[pos+5], data[pos+6], data[pos+7]);
                        std::fflush(stderr);
                    }
                }
                const bool directHl = (opcode == VIF_DIRECTHL);
                submitGifPacket(GifPathId::Path2, data + pos, qwCount * 16, true, directHl);'''

if b'\r\n' in content:
    target1 = target1.replace(b'\n', b'\r\n')
    replacement1 = replacement1.replace(b'\n', b'\r\n')

assert target1 in content, 'Target1 not found in ps2_vif1_interpreter.cpp!'
content = content.replace(target1, replacement1, 1)

target2 = b'''            const uint32_t chunkQw = std::min<uint32_t>(m_vif1PendingPath2ImageQwc, availableQw);
            std::vector<uint8_t> imagePacket(16u + static_cast<size_t>(chunkQw) * 16u, 0u);'''

replacement2 = b'''            const uint32_t chunkQw = std::min<uint32_t>(m_vif1PendingPath2ImageQwc, availableQw);
            if (chunkQw == 512 || chunkQw == 64)
            {
                static int s_vifPendingCount = 0;
                if (s_vifPendingCount++ < 10)
                {
                    std::fprintf(stderr, "[VIF1:SUBMIT_PENDING] chunkQw=%u pos=%u sizeBytes=%u first8=[%u,%u,%u,%u,%u,%u,%u,%u]\\n",
                                 chunkQw, pos, sizeBytes,
                                 data[pos], data[pos+1], data[pos+2], data[pos+3],
                                 data[pos+4], data[pos+5], data[pos+6], data[pos+7]);
                    std::fflush(stderr);
                }
            }
            std::vector<uint8_t> imagePacket(16u + static_cast<size_t>(chunkQw) * 16u, 0u);'''

if b'\r\n' in content:
    target2 = target2.replace(b'\n', b'\r\n')
    replacement2 = replacement2.replace(b'\n', b'\r\n')

assert target2 in content, 'Target2 not found in ps2_vif1_interpreter.cpp!'
content = content.replace(target2, replacement2, 1)

with open('PS2Recomp/ps2xRuntime/src/lib/ps2_vif1_interpreter.cpp', 'wb') as f:
    f.write(content)
print('Successfully updated ps2_vif1_interpreter.cpp!')

# Patch gs_cpu_backend.cpp
with open('PS2Recomp/ps2xRuntime/src/lib/gs/gs_cpu_backend.cpp', 'rb') as f:
    gs_content = f.read()

target_gs = b'''    const uint32_t dbp = m_transfer.bitbltbuf.dbp;
    const uint32_t dbw = std::max<uint32_t>(m_transfer.bitbltbuf.dbw, 1u);'''

replacement_gs = b'''    const uint32_t dbp = m_transfer.bitbltbuf.dbp;
    const uint32_t dbw = std::max<uint32_t>(m_transfer.bitbltbuf.dbw, 1u);
    if (dbp == 10752 || dbp == 10784)
    {
        static int s_upLogCount = 0;
        if (s_upLogCount++ < 10)
        {
            std::fprintf(stderr, "[GS:UPLOAD_IMAGE] dbp=%u dpsm=0x%02X sizeBytes=%u first8=[%u,%u,%u,%u,%u,%u,%u,%u]\\n",
                         dbp, m_transfer.bitbltbuf.dpsm, sizeBytes,
                         data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7]);
            std::fflush(stderr);
        }
    }'''

if b'\r\n' in gs_content:
    target_gs = target_gs.replace(b'\n', b'\r\n')
    replacement_gs = replacement_gs.replace(b'\n', b'\r\n')

assert target_gs in gs_content, 'target_gs not found in gs_cpu_backend.cpp!'
gs_content = gs_content.replace(target_gs, replacement_gs, 1)

with open('PS2Recomp/ps2xRuntime/src/lib/gs/gs_cpu_backend.cpp', 'wb') as f:
    f.write(gs_content)
print('Successfully updated gs_cpu_backend.cpp!')
