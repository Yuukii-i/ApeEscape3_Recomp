with open('PS2Recomp/ps2xRuntime/src/lib/ps2_memory.cpp', 'rb') as f:
    content = f.read()

target = b'''                        if (transferTagData)
                            appendVifTagData(currentTagAddr);

                        if (hasPayload)
                            appendData(dataAddr, tagQwc);
                        if (irq && tieEnabled)'''

replacement = b'''                        if (transferTagData)
                            appendVifTagData(currentTagAddr);

                        if (hasPayload)
                            appendData(dataAddr, tagQwc);

                        if (channelBase == 0x10009000u && (tagQwc == 512 || tagQwc == 64 || (tagQwc > 0 && tagsProcessed <= 6)))
                        {
                            uint32_t w2 = 0, w3 = 0;
                            if (physTag + 16 <= tagMax) {
                                std::memcpy(&w2, tp + 8, 4);
                                std::memcpy(&w3, tp + 12, 4);
                            }
                            uint8_t sample[16] = {};
                            if (hasPayload) {
                                uint32_t dp = 0;
                                try { dp = translateAddress(dataAddr); } catch(...) {}
                                const uint8_t *db = isScratchpad(dataAddr) ? m_scratchpad : m_rdram;
                                const uint32_t dm = isScratchpad(dataAddr) ? PS2_SCRATCHPAD_SIZE : PS2_RAM_SIZE;
                                if (dp + 16 <= dm) std::memcpy(sample, db + dp, 16);
                            }
                            static int s_tagLogCount = 0;
                            if (s_tagLogCount++ < 50) {
                                std::fprintf(stderr, "[DMA:VIF1_TAG] tagAddr=0x%08X id=%u qwc=%u dataAddr=0x%08X w2=0x%08X w3=0x%08X TTE=%d payload0..7=[%u,%u,%u,%u,%u,%u,%u,%u]\\n",
                                             currentTagAddr, id, tagQwc, dataAddr, w2, w3, transferTagData ? 1 : 0,
                                             sample[0], sample[1], sample[2], sample[3], sample[4], sample[5], sample[6], sample[7]);
                                std::fflush(stderr);
                            }
                        }
                        if (irq && tieEnabled)'''

if b'\r\n' in content:
    target = target.replace(b'\n', b'\r\n')
    replacement = replacement.replace(b'\n', b'\r\n')

assert target in content, 'Target not found in content!'
new_content = content.replace(target, replacement, 1)
with open('PS2Recomp/ps2xRuntime/src/lib/ps2_memory.cpp', 'wb') as f:
    f.write(new_content)
print('Successfully updated ps2_memory.cpp!')
