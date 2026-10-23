# Apply Step 4 fix:
# 1. Restore 0x003703D4 override in ps2_runtime.cpp
# 2. Fix CID1 FD base in RPC.cpp

with open('PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp', 'rb') as f:
    content = f.read()

target1 = b'''    // Remove 0x003703D4 override and add logging for sub_0015993C:'''.replace(b'\n', b'\r\n')
replacement1 = b'''    // 0x003703D4: Early exit check returning non-zero error code -> force return 0
    replaceFunction(0x003703D4u, [](uint8_t *rdram, R5900Context *ctx, PS2Runtime *runtime) {
        ps2xSafeLog("[override] 0x003703D4 called (ra=0x%08x) -> returning 0\\n", getRegU32(ctx, 31));
        setReturnS32(ctx, 0);
        ctx->pc = getRegU32(ctx, 31);
    });

    // Logging for sub_0015993C:'''.replace(b'\n', b'\r\n')

assert target1 in content, "target1 not found in ps2_runtime.cpp!"
content = content.replace(target1, replacement1, 1)

with open('PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp', 'wb') as f:
    f.write(content)
print("Updated ps2_runtime.cpp with 0x003703D4 override")

with open('PS2Recomp/ps2xRuntime/src/lib/Kernel/Syscalls/RPC.cpp', 'rb') as f:
    rpc = f.read()

target_rpc = b'''                    int allocFd = -1;
                    for (int i = 0; i < 16; ++i)
                    {
                        if (!s_vfiDescriptors[i].open)
                        {
                            allocFd = i;
                            break;
                        }
                    }
                    if (allocFd < 0)
                    {
                        ps2xSafeLog( "[CID1:Open] ERROR: out of FDs for '%s'\\n", path.c_str());
                        reply.result = static_cast<uint32_t>(-1);
                    }
                    else
                    {
                        s_vfiDescriptors[allocFd].open = true;
                        s_vfiDescriptors[allocFd].entry = *entry;
                        s_vfiDescriptors[allocFd].offset = 0;
                        reply.result = static_cast<uint32_t>(allocFd);
                        ps2xSafeLog( "[CID1:Open] fd=%d -> '%s' (size=%llu, LSN=%u)\\n",
                                     allocFd, path.c_str(), static_cast<unsigned long long>(entry->fileSize), entry->isoLsn);
                    }
                }
                break;
            }
            case 0x04: // Close
            {
                uint32_t fd = *reinterpret_cast<const uint32_t *>(src + 0x10);
                if (fd < 16 && s_vfiDescriptors[fd].open)
                {
                    s_vfiDescriptors[fd].open = false;
                    reply.result = 0;
                    ps2xSafeLog( "[CID1:Close] fd=%u\\n", fd);
                }
                else
                {
                    ps2xSafeLog( "[CID1:Close] fd=%u INVALID\\n", fd);
                    reply.result = static_cast<uint32_t>(-1);
                }
                break;
            }
            case 0x06: // Read fd
            {
                uint32_t fd = *reinterpret_cast<const uint32_t *>(src + 0x10);
                uint32_t eeDst = *reinterpret_cast<const uint32_t *>(src + 0x14);
                uint32_t reqSize = *reinterpret_cast<const uint32_t *>(src + 0x18);
                if (fd < 16 && s_vfiDescriptors[fd].open)
                {
                    auto &slot = s_vfiDescriptors[fd];'''.replace(b'\n', b'\r\n')

replacement_rpc = b'''                    constexpr int kCid1FdBase = 3;
                    int allocSlot = -1;
                    for (int i = 0; i < 16; ++i)
                    {
                        if (!s_vfiDescriptors[i].open)
                        {
                            allocSlot = i;
                            break;
                        }
                    }
                    if (allocSlot < 0)
                    {
                        ps2xSafeLog( "[CID1:Open] ERROR: out of FDs for '%s'\\n", path.c_str());
                        reply.result = static_cast<uint32_t>(-1);
                    }
                    else
                    {
                        s_vfiDescriptors[allocSlot].open = true;
                        s_vfiDescriptors[allocSlot].entry = *entry;
                        s_vfiDescriptors[allocSlot].offset = 0;
                        int allocFd = allocSlot + kCid1FdBase;
                        reply.result = static_cast<uint32_t>(allocFd);
                        ps2xSafeLog( "[CID1:Open] fd=%d (slot=%d) -> '%s' (size=%llu, LSN=%u)\\n",
                                     allocFd, allocSlot, path.c_str(), static_cast<unsigned long long>(entry->fileSize), entry->isoLsn);
                    }
                }
                break;
            }
            case 0x04: // Close
            {
                constexpr int kCid1FdBase = 3;
                uint32_t fd = *reinterpret_cast<const uint32_t *>(src + 0x10);
                int fdSlot = static_cast<int>(fd) - kCid1FdBase;
                if (fdSlot >= 0 && fdSlot < 16 && s_vfiDescriptors[fdSlot].open)
                {
                    s_vfiDescriptors[fdSlot].open = false;
                    reply.result = 0;
                    ps2xSafeLog( "[CID1:Close] fd=%u (slot=%d)\\n", fd, fdSlot);
                }
                else
                {
                    ps2xSafeLog( "[CID1:Close] fd=%u (slot=%d) INVALID\\n", fd, fdSlot);
                    reply.result = static_cast<uint32_t>(-1);
                }
                break;
            }
            case 0x06: // Read fd
            {
                constexpr int kCid1FdBase = 3;
                uint32_t fd = *reinterpret_cast<const uint32_t *>(src + 0x10);
                uint32_t eeDst = *reinterpret_cast<const uint32_t *>(src + 0x14);
                uint32_t reqSize = *reinterpret_cast<const uint32_t *>(src + 0x18);
                int fdSlot = static_cast<int>(fd) - kCid1FdBase;
                if (fdSlot >= 0 && fdSlot < 16 && s_vfiDescriptors[fdSlot].open)
                {
                    auto &slot = s_vfiDescriptors[fdSlot];'''.replace(b'\n', b'\r\n')

target_seek = b'''            case 0x07: // Seek
            {
                uint32_t fd = *reinterpret_cast<const uint32_t *>(src + 0x10);
                int32_t seekOffset = *reinterpret_cast<const int32_t *>(src + 0x14);
                uint32_t whence = *reinterpret_cast<const uint32_t *>(src + 0x18);
                if (fd < 16 && s_vfiDescriptors[fd].open)
                {
                    auto &slot = s_vfiDescriptors[fd];'''.replace(b'\n', b'\r\n')

replacement_seek = b'''            case 0x07: // Seek
            {
                constexpr int kCid1FdBase = 3;
                uint32_t fd = *reinterpret_cast<const uint32_t *>(src + 0x10);
                int32_t seekOffset = *reinterpret_cast<const int32_t *>(src + 0x14);
                uint32_t whence = *reinterpret_cast<const uint32_t *>(src + 0x18);
                int fdSlot = static_cast<int>(fd) - kCid1FdBase;
                if (fdSlot >= 0 && fdSlot < 16 && s_vfiDescriptors[fdSlot].open)
                {
                    auto &slot = s_vfiDescriptors[fdSlot];'''.replace(b'\n', b'\r\n')

assert target_rpc in rpc, "target_rpc not found in RPC.cpp!"
rpc = rpc.replace(target_rpc, replacement_rpc, 1)

assert target_seek in rpc, "target_seek not found in RPC.cpp!"
rpc = rpc.replace(target_seek, replacement_seek, 1)

with open('PS2Recomp/ps2xRuntime/src/lib/Kernel/Syscalls/RPC.cpp', 'wb') as f:
    f.write(rpc)
print("Updated RPC.cpp with CID1 FD offset")
