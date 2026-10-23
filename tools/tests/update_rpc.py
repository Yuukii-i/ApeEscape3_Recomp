import os

path = 'PS2Recomp/ps2xRuntime/src/lib/Kernel/Syscalls/RPC.cpp'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add Pad.h include
if '../Stubs/Pad.h' not in content:
    content = content.replace('#include "../Stubs/SIF.h"', '#include "../Stubs/SIF.h"\n#include "../Stubs/Pad.h"')

# Locate DBC section
target_old = """                    if (call.rpcNum == 0x80001304u) // sceDbcSetWorkAddr
                    {
                        uint32_t workAddr = 0;
                        if (call.sendBuf && call.sendSize >= 8)
                        {
                            if (const uint8_t *src = getConstMemPtr(call.rdram, call.sendBuf))
                            {
                                std::memcpy(&workAddr, src + 4, 4);
                            }
                        }
                        ps2xSafeLog( "[rpc:dbc] sceDbcSetWorkAddr workAddr=0x%08x\\n", workAddr);
                        fflush(stderr);

                        auto writeIdleDbcBuffer = [](uint8_t *rdram, uint32_t addr) {
                            if (!rdram || addr == 0 || addr >= 0x02000000u) return;
                            uint8_t *dst = getMemPtr(rdram, addr);
                            if (!dst) return;
                            std::memset(dst, 0, 128);
                            dst[0x00] = 0x01; // status: DBC_STAT_CONNECTED
                            dst[0x01] = 0x00;
                            dst[0x02] = 0x20; // packet len: 32 bytes
                            dst[0x03] = 0x00;
                            dst[0x04] = 0x01; // valid / connected word
                            // DualShock 2 idle packet at +0x1C:
                            dst[0x1C + 0x00] = 0x00; // terminal/status
                            dst[0x1C + 0x01] = 0x73; // pad type: DS2
                            dst[0x1C + 0x02] = 0xFF; // buttons low byte (all released)
                            dst[0x1C + 0x03] = 0xFF; // buttons high byte (all released)
                            dst[0x1C + 0x04] = 0xFF; // buttons low byte (if at offset 4)
                            dst[0x1C + 0x05] = 0xFF; // buttons high byte (if at offset 5)
                            dst[0x1C + 0x06] = 0x80; // stick R-X
                            dst[0x1C + 0x07] = 0x80; // stick R-Y
                            dst[0x1C + 0x08] = 0x80; // stick L-X
                            dst[0x1C + 0x09] = 0x80; // stick L-Y
                            dst[0x1C + 0x0A] = 0x80;
                            dst[0x1C + 0x0B] = 0x80;
                            dst[0x1C + 0x0C] = 0x80;
                            dst[0x1C + 0x0D] = 0x80;
                            // sequence counter at +0x7C:
                            uint32_t seq = 1;
                            std::memcpy(dst + 0x7C, &seq, 4);
                        };

                        if (workAddr != 0) {
                            writeIdleDbcBuffer(call.rdram, workAddr);
                        }
                        // Also initialize Port 0 double buffers (0x00784D40 and 0x00784DC0):
                        writeIdleDbcBuffer(call.rdram, 0x00784D40u);
                        writeIdleDbcBuffer(call.rdram, 0x00784DC0u);
                        return 0;
                    }
                    if (call.rpcNum == 0x80001301u) // DBC port double-buffer registration
                    {
                        auto writeIdleDbcBuffer = [](uint8_t *rdram, uint32_t addr) {
                            if (!rdram || addr == 0 || addr >= 0x02000000u) return;
                            uint8_t *dst = getMemPtr(rdram, addr);
                            if (!dst) return;
                            std::memset(dst, 0, 128);
                            dst[0x00] = 0x01; // status: DBC_STAT_CONNECTED
                            dst[0x01] = 0x00;
                            dst[0x02] = 0x20; // packet len: 32 bytes
                            dst[0x03] = 0x00;
                            dst[0x04] = 0x01; // valid / connected word
                            dst[0x1C + 0x00] = 0x00;
                            dst[0x1C + 0x01] = 0x73;
                            dst[0x1C + 0x02] = 0xFF;
                            dst[0x1C + 0x03] = 0xFF;
                            dst[0x1C + 0x04] = 0xFF;
                            dst[0x1C + 0x05] = 0xFF;
                            dst[0x1C + 0x06] = 0x80;
                            dst[0x1C + 0x07] = 0x80;
                            dst[0x1C + 0x08] = 0x80;
                            dst[0x1C + 0x09] = 0x80;
                            dst[0x1C + 0x0A] = 0x80;
                            dst[0x1C + 0x0B] = 0x80;
                            dst[0x1C + 0x0C] = 0x80;
                            dst[0x1C + 0x0D] = 0x80;
                            uint32_t seq = 1;
                            std::memcpy(dst + 0x7C, &seq, 4);
                        };

                        if (call.sendBuf && call.sendSize >= 0x30)
                        {
                            if (const uint8_t *src = getConstMemPtr(call.rdram, call.sendBuf))
                            {
                                uint32_t bufA = 0, bufB = 0;
                                std::memcpy(&bufA, src + 0x28, 4);
                                std::memcpy(&bufB, src + 0x2C, 4);
                                if (bufA) writeIdleDbcBuffer(call.rdram, bufA);
                                if (bufB) writeIdleDbcBuffer(call.rdram, bufB);
                            }
                        }
                        return 0;
                    }"""

target_new = """                    if (call.rpcNum == 0x80001304u) // sceDbcSetWorkAddr
                    {
                        uint32_t workAddr = 0;
                        if (call.sendBuf && call.sendSize >= 8)
                        {
                            if (const uint8_t *src = getConstMemPtr(call.rdram, call.sendBuf))
                            {
                                std::memcpy(&workAddr, src + 4, 4);
                            }
                        }
                        ps2xSafeLog( "[rpc:dbc] sceDbcSetWorkAddr workAddr=0x%08x\\n", workAddr);
                        fflush(stderr);

                        if (workAddr != 0) {
                            s_dbcWorkAddr = workAddr;
                        }
                        dbcUpdatePadBuffers(call.rdram, call.runtime);
                        return 0;
                    }
                    if (call.rpcNum == 0x80001301u) // DBC port double-buffer registration
                    {
                        if (call.sendBuf && call.sendSize >= 0x30)
                        {
                            if (const uint8_t *src = getConstMemPtr(call.rdram, call.sendBuf))
                            {
                                uint32_t bufA = 0, bufB = 0;
                                std::memcpy(&bufA, src + 0x28, 4);
                                std::memcpy(&bufB, src + 0x2C, 4);
                                if (bufA) s_dbcPort0BufA = bufA;
                                if (bufB) s_dbcPort0BufB = bufB;
                            }
                        }
                        dbcUpdatePadBuffers(call.rdram, call.runtime);
                        return 0;
                    }"""

helpers = """        static uint32_t s_dbcSeq = 1u;
        static uint32_t s_dbcPort0BufA = 0x00784D40u;
        static uint32_t s_dbcPort0BufB = 0x00784DC0u;
        static uint32_t s_dbcWorkAddr = 0x00757D40u;

        static void dbcWritePacket(uint8_t *rdram, uint32_t addr, const ps2_stubs::PadInputState &pad, uint32_t seq)
        {
            if (!rdram || addr == 0 || addr >= 0x02000000u) return;
            uint8_t *dst = getMemPtr(rdram, addr);
            if (!dst) return;

            dst[0x00] = 0x01; // status: DBC_STAT_CONNECTED
            dst[0x01] = 0x00;
            dst[0x02] = 0x20; // packet len: 32 bytes
            dst[0x03] = 0x00;
            dst[0x04] = 0x01; // valid / connected word

            std::memset(dst + 0x1C, 0, 32);
            dst[0x1C + 0x00] = 0x00; // terminal/status
            dst[0x1C + 0x01] = 0x73; // pad type: DS2
            dst[0x1C + 0x02] = static_cast<uint8_t>(pad.buttons & 0xFFu);
            dst[0x1C + 0x03] = static_cast<uint8_t>((pad.buttons >> 8u) & 0xFFu);
            dst[0x1C + 0x04] = pad.rx;
            dst[0x1C + 0x05] = pad.ry;
            dst[0x1C + 0x06] = pad.lx;
            dst[0x1C + 0x07] = pad.ly;

            // Pressure values: 0xFF if pressed, 0x00 if not:
            dst[0x1C + 8]  = (pad.buttons & (1 << 5)) ? 0x00 : 0xFF; // Right
            dst[0x1C + 9]  = (pad.buttons & (1 << 7)) ? 0x00 : 0xFF; // Left
            dst[0x1C + 10] = (pad.buttons & (1 << 4)) ? 0x00 : 0xFF; // Up
            dst[0x1C + 11] = (pad.buttons & (1 << 6)) ? 0x00 : 0xFF; // Down
            dst[0x1C + 12] = (pad.buttons & (1 << 12)) ? 0x00 : 0xFF; // Triangle
            dst[0x1C + 13] = (pad.buttons & (1 << 13)) ? 0x00 : 0xFF; // Circle
            dst[0x1C + 14] = (pad.buttons & (1 << 14)) ? 0x00 : 0xFF; // Cross
            dst[0x1C + 15] = (pad.buttons & (1 << 15)) ? 0x00 : 0xFF; // Square
            dst[0x1C + 16] = (pad.buttons & (1 << 10)) ? 0x00 : 0xFF; // L1
            dst[0x1C + 17] = (pad.buttons & (1 << 8)) ? 0x00 : 0xFF; // L2
            dst[0x1C + 18] = (pad.buttons & (1 << 11)) ? 0x00 : 0xFF; // R1
            dst[0x1C + 19] = (pad.buttons & (1 << 9)) ? 0x00 : 0xFF; // R2

            // sequence counter at +0x7C:
            std::memcpy(dst + 0x7C, &seq, sizeof(seq));
        }

        static void dbcUpdatePadBuffers(uint8_t *rdram, PS2Runtime *runtime)
        {
            if (!rdram) return;
            ps2_stubs::PadInputState pad = ps2_stubs::getCurrentPadInput(0, runtime);

            s_dbcSeq++;
            uint32_t activeBuf = (s_dbcSeq & 1) ? s_dbcPort0BufB : s_dbcPort0BufA;
            uint32_t olderBuf  = (s_dbcSeq & 1) ? s_dbcPort0BufA : s_dbcPort0BufB;

            dbcWritePacket(rdram, olderBuf, pad, s_dbcSeq - 1);
            dbcWritePacket(rdram, activeBuf, pad, s_dbcSeq);
            if (s_dbcWorkAddr) {
                dbcWritePacket(rdram, s_dbcWorkAddr, pad, s_dbcSeq);
            }
        }
"""

before_marker = '        static void initRpcHleServices()'
if before_marker in content:
    content = content.replace(before_marker, helpers + '\n' + before_marker)
elif before_marker.replace('\n', '\r\n') in content:
    content = content.replace(before_marker.replace('\n', '\r\n'), helpers.replace('\n', '\r\n') + '\r\n' + before_marker.replace('\n', '\r\n'))
else:
    print('Failed to find before_marker')

if target_old in content:
    content = content.replace(target_old, target_new)
elif target_old.replace('\n', '\r\n') in content:
    content = content.replace(target_old.replace('\n', '\r\n'), target_new.replace('\n', '\r\n'))
else:
    print('Failed to find target_old')

# Add dbcUpdatePadBuffers call in SG2_AUDIO
sg2_old = """                        uint32_t zeroBytes = std::min(call.recvSize, 448u);
                        rpcZeroRdram(call.rdram, call.recvBuf, zeroBytes);
                    }
                    return 0;"""
sg2_new = """                        uint32_t zeroBytes = std::min(call.recvSize, 448u);
                        rpcZeroRdram(call.rdram, call.recvBuf, zeroBytes);
                    }
                    dbcUpdatePadBuffers(call.rdram, call.runtime);
                    return 0;"""

if sg2_old in content:
    content = content.replace(sg2_old, sg2_new)
elif sg2_old.replace('\n', '\r\n') in content:
    content = content.replace(sg2_old.replace('\n', '\r\n'), sg2_new.replace('\n', '\r\n'))
else:
    print('Failed to find sg2_old')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('RPC.cpp updated successfully')
