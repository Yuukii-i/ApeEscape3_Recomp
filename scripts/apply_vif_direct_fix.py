with open('PS2Recomp/ps2xRuntime/src/lib/ps2_vif1_interpreter.cpp', 'rb') as f:
    content = f.read()

# 1. Remove the pending block from top of while loop
top_target = b'''    while (pos + 4 <= sizeBytes)
    {
        if (m_vif1PendingPath2ImageQwc != 0u)
        {
            const uint32_t availableQw = (sizeBytes - pos) / 16u;
            if (availableQw == 0u)
            {
                break;
            }

            const uint32_t chunkQw = std::min<uint32_t>(m_vif1PendingPath2ImageQwc, availableQw);
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
            std::vector<uint8_t> imagePacket(16u + static_cast<size_t>(chunkQw) * 16u, 0u);
            const uint64_t imageTag =
                static_cast<uint64_t>(chunkQw & 0x7FFFu) |
                ((m_vif1PendingPath2ImageQwc == chunkQw) ? (1ull << 15) : 0ull) |
                (static_cast<uint64_t>(kGifFmtImage) << 58);
            std::memcpy(imagePacket.data(), &imageTag, sizeof(imageTag));
            std::memcpy(imagePacket.data() + 16u, data + pos, static_cast<size_t>(chunkQw) * 16u);
            submitGifPacket(GifPathId::Path2, imagePacket.data(), static_cast<uint32_t>(imagePacket.size()), true, m_vif1PendingPath2DirectHl);

            pos += chunkQw * 16u;
            m_vif1PendingPath2ImageQwc -= chunkQw;
            if (m_vif1PendingPath2ImageQwc == 0u)
            {
                m_vif1PendingPath2DirectHl = false;
            }
            continue;
        }'''

top_replacement = b'''    while (pos + 4 <= sizeBytes)
    {'''

if b'\r\n' in content:
    top_target = top_target.replace(b'\n', b'\r\n')
    top_replacement = top_replacement.replace(b'\n', b'\r\n')

assert top_target in content, 'top_target not found in ps2_vif1_interpreter.cpp!'
content = content.replace(top_target, top_replacement, 1)

# 2. In VIF_DIRECT, handle m_vif1PendingPath2ImageQwc
direct_target = b'''            if (qwCount > 0)
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
                submitGifPacket(GifPathId::Path2, data + pos, qwCount * 16, true, directHl);

                const uint32_t pendingImageQw = pendingGifImageQwc(data + pos, qwCount * 16u);
                if (pendingImageQw != 0u)
                {
                    m_vif1PendingPath2ImageQwc = pendingImageQw;
                    m_vif1PendingPath2DirectHl = directHl;
                }
            }'''

direct_replacement = b'''            if (qwCount > 0)
            {
                const bool directHl = (opcode == VIF_DIRECTHL);
                if (m_vif1PendingPath2ImageQwc != 0u)
                {
                    const uint32_t chunkQw = std::min<uint32_t>(m_vif1PendingPath2ImageQwc, qwCount);
                    std::vector<uint8_t> imagePacket(16u + static_cast<size_t>(chunkQw) * 16u, 0u);
                    const uint64_t imageTag =
                        static_cast<uint64_t>(chunkQw & 0x7FFFu) |
                        ((m_vif1PendingPath2ImageQwc == chunkQw) ? (1ull << 15) : 0ull) |
                        (static_cast<uint64_t>(kGifFmtImage) << 58);
                    std::memcpy(imagePacket.data(), &imageTag, sizeof(imageTag));
                    std::memcpy(imagePacket.data() + 16u, data + pos, static_cast<size_t>(chunkQw) * 16u);
                    submitGifPacket(GifPathId::Path2, imagePacket.data(), static_cast<uint32_t>(imagePacket.size()), true, directHl);
                    m_vif1PendingPath2ImageQwc -= chunkQw;
                    if (m_vif1PendingPath2ImageQwc == 0u)
                    {
                        m_vif1PendingPath2DirectHl = false;
                    }
                }
                else
                {
                    submitGifPacket(GifPathId::Path2, data + pos, qwCount * 16, true, directHl);

                    const uint32_t pendingImageQw = pendingGifImageQwc(data + pos, qwCount * 16u);
                    if (pendingImageQw != 0u)
                    {
                        m_vif1PendingPath2ImageQwc = pendingImageQw;
                        m_vif1PendingPath2DirectHl = directHl;
                    }
                }
            }'''

if b'\r\n' in content:
    direct_target = direct_target.replace(b'\n', b'\r\n')
    direct_replacement = direct_replacement.replace(b'\n', b'\r\n')

assert direct_target in content, 'direct_target not found in ps2_vif1_interpreter.cpp!'
content = content.replace(direct_target, direct_replacement, 1)

with open('PS2Recomp/ps2xRuntime/src/lib/ps2_vif1_interpreter.cpp', 'wb') as f:
    f.write(content)
print('Successfully patched ps2_vif1_interpreter.cpp!')
