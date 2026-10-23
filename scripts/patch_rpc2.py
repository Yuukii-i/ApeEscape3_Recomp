import sys

path = 'PS2Recomp/ps2xRuntime/src/lib/Kernel/Syscalls/RPC.cpp'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target1 = '''            if (s_dbcWorkAddr) {
                dbcWritePacket(rdram, s_dbcWorkAddr, pad0, s_dbcSeq);
            }'''

repl1 = '''            if (s_dbcWorkAddr) {
                if (uint8_t *workDst = getMemPtr(rdram, s_dbcWorkAddr)) {
                    uint32_t status0 = 1; // Port 0 connected
                    uint32_t status1 = 1; // Port 1 connected
                    std::memcpy(workDst, &status0, 4);
                    std::memcpy(workDst + 4, &status1, 4);
                }
            }'''

target2 = '''                                ps2xSafeLog("[rpc:dbc] Registered port %u buffers: A=0x%08x B=0x%08x\\n", port, bufA, bufB);
                                fflush(stderr);
                            }
                        }
                        dbcUpdatePadBuffers(call.rdram, call.runtime);
                        return 0;
                    }'''

repl2 = '''                                if (call.recvBuf && call.recvSize >= 0x28)
                                {
                                    if (uint8_t *dst = getMemPtr(call.rdram, call.recvBuf))
                                    {
                                        uint32_t one = 1;
                                        std::memcpy(dst, &one, 4);
                                        std::memcpy(dst + 0x24, &port, 4);
                                    }
                                }
                                ps2xSafeLog("[rpc:dbc] Registered port %u buffers: A=0x%08x B=0x%08x\\n", port, bufA, bufB);
                                fflush(stderr);
                            }
                        }
                        dbcUpdatePadBuffers(call.rdram, call.runtime);
                        return 0;
                    }
                    if (call.rpcNum == 0x80001303u) // DBC check/poll port connection
                    {
                        if (call.recvBuf && call.recvSize >= 8)
                        {
                            if (uint8_t *dst = getMemPtr(call.rdram, call.recvBuf))
                            {
                                uint32_t status = 1; // 1 = connected
                                std::memcpy(dst + 4, &status, 4);
                            }
                        }
                        return 0;
                    }'''

assert target1 in content, 'target1 not found'
content = content.replace(target1, repl1, 1)
assert target2 in content, 'target2 not found'
content = content.replace(target2, repl2, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Successfully patched RPC.cpp with DBC work buffer and 0x80001303 handler')
