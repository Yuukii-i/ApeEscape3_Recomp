import sys

path = 'PS2Recomp/ps2xRuntime/src/lib/Kernel/Syscalls/RPC.cpp'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target1 = '''        static uint32_t s_dbcSeq = 1u;
        static uint32_t s_dbcPort0BufA = 0x00784D40u;
        static uint32_t s_dbcPort0BufB = 0x00784DC0u;
        static uint32_t s_dbcWorkAddr = 0x00757D40u;'''

repl1 = '''        static uint32_t s_dbcSeq = 1u;
        static uint32_t s_dbcPort0BufA = 0x00784D40u;
        static uint32_t s_dbcPort0BufB = 0x00784DC0u;
        static uint32_t s_dbcPort1BufA = 0x00784E80u;
        static uint32_t s_dbcPort1BufB = 0x00784F00u;
        static uint32_t s_dbcWorkAddr = 0x00757D40u;'''

target2 = '''        static void dbcUpdatePadBuffers(uint8_t *rdram, PS2Runtime *runtime)
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
            g_diagDbcBufferWrites.fetch_add(1, std::memory_order_relaxed);
        }'''

repl2 = '''        static void dbcUpdatePadBuffers(uint8_t *rdram, PS2Runtime *runtime)
        {
            if (!rdram) return;
            ps2_stubs::PadInputState pad0 = ps2_stubs::getCurrentPadInput(0, runtime);

            s_dbcSeq++;
            uint32_t activeBuf0 = (s_dbcSeq & 1) ? s_dbcPort0BufB : s_dbcPort0BufA;
            uint32_t olderBuf0  = (s_dbcSeq & 1) ? s_dbcPort0BufA : s_dbcPort0BufB;

            if (olderBuf0)  dbcWritePacket(rdram, olderBuf0, pad0, s_dbcSeq - 1);
            if (activeBuf0) dbcWritePacket(rdram, activeBuf0, pad0, s_dbcSeq);

            if (s_dbcPort1BufA && s_dbcPort1BufB) {
                ps2_stubs::PadInputState pad1 = ps2_stubs::getCurrentPadInput(1, runtime);
                uint32_t activeBuf1 = (s_dbcSeq & 1) ? s_dbcPort1BufB : s_dbcPort1BufA;
                uint32_t olderBuf1  = (s_dbcSeq & 1) ? s_dbcPort1BufA : s_dbcPort1BufB;
                dbcWritePacket(rdram, olderBuf1, pad1, s_dbcSeq - 1);
                dbcWritePacket(rdram, activeBuf1, pad1, s_dbcSeq);
            }

            if (s_dbcWorkAddr) {
                dbcWritePacket(rdram, s_dbcWorkAddr, pad0, s_dbcSeq);
            }
            g_diagDbcBufferWrites.fetch_add(1, std::memory_order_relaxed);
        }'''

target3 = '''                    if (call.rpcNum == 0x80001301u) // DBC port double-buffer registration
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
                    }'''

repl3 = '''                    if (call.rpcNum == 0x80001301u) // DBC port double-buffer registration
                    {
                        if (call.sendBuf && call.sendSize >= 0x30)
                        {
                            if (const uint8_t *src = getConstMemPtr(call.rdram, call.sendBuf))
                            {
                                uint32_t port = 0;
                                std::memcpy(&port, src + 8, 4);
                                uint32_t bufA = 0, bufB = 0;
                                std::memcpy(&bufA, src + 0x28, 4);
                                std::memcpy(&bufB, src + 0x2C, 4);
                                if (port == 0)
                                {
                                    if (bufA) s_dbcPort0BufA = bufA;
                                    if (bufB) s_dbcPort0BufB = bufB;
                                }
                                else
                                {
                                    if (bufA) s_dbcPort1BufA = bufA;
                                    if (bufB) s_dbcPort1BufB = bufB;
                                }
                                ps2xSafeLog("[rpc:dbc] Registered port %u buffers: A=0x%08x B=0x%08x\\n", port, bufA, bufB);
                                fflush(stderr);
                            }
                        }
                        dbcUpdatePadBuffers(call.rdram, call.runtime);
                        return 0;
                    }'''

assert target1 in content, 'target1 not found'
content = content.replace(target1, repl1, 1)
assert target2 in content, 'target2 not found'
content = content.replace(target2, repl2, 1)
assert target3 in content, 'target3 not found'
content = content.replace(target3, repl3, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Successfully updated RPC.cpp')
