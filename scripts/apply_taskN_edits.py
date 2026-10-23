#!/usr/bin/env python3
import sys

# 1. Edit ps2_memory.cpp
with open("PS2Recomp/ps2xRuntime/src/lib/ps2_memory.cpp", "r", encoding="utf-8") as f:
    mem_src = f.read().replace("\r\n", "\n")

mem_target = """    const uint8_t *imageData = nullptr;
    if (!resolveContiguous(imageDataAddr, imageBytes, imageData))
        return false;

    m_dmaStartCount.fetch_add(1, std::memory_order_relaxed);
    m_seenGifCopy = true;
    m_gifCopyCount.fetch_add(1, std::memory_order_relaxed);
    gs.uploadImageNative(setupRegs[0], setupRegs[1], setupRegs[2], setupRegs[3], imageData, imageBytes);"""

mem_repl = """    const uint8_t *imageData = nullptr;
    if (!resolveContiguous(imageDataAddr, imageBytes, imageData))
        return false;

    static uint32_t s_uploadChainSeq = 0;
    ++s_uploadChainSeq;
    uint32_t dbp = static_cast<uint32_t>(setupRegs[0] & 0x3FFFull);
    uint32_t dpsm = static_cast<uint32_t>((setupRegs[0] >> 24u) & 0x3Full);
    uint32_t rrw = static_cast<uint32_t>(setupRegs[2] & 0xFFFull);
    uint32_t rrh = static_cast<uint32_t>((setupRegs[2] >> 32u) & 0xFFFull);
    std::fprintf(stderr, "[GIF:DMA_SRC] seq=%u guestAddr=0x%08X bytes=%u tagId=%u tagAddr=0x%08X dbp=%u dpsm=0x%02X (%ux%u)\\n",
                 s_uploadChainSeq, imageDataAddr, imageBytes, payloadTag.id, payloadTagAddr, dbp, dpsm, rrw, rrh);
    if (imageData && imageBytes >= 16)
    {
        std::fprintf(stderr, "[GIF:DMA_SRC_DATA] first16=[%u,%u,%u,%u,%u,%u,%u,%u, %u,%u,%u,%u,%u,%u,%u,%u]\\n",
                     imageData[0], imageData[1], imageData[2], imageData[3],
                     imageData[4], imageData[5], imageData[6], imageData[7],
                     imageData[8], imageData[9], imageData[10], imageData[11],
                     imageData[12], imageData[13], imageData[14], imageData[15]);
    }
    std::fflush(stderr);

    m_dmaStartCount.fetch_add(1, std::memory_order_relaxed);
    m_seenGifCopy = true;
    m_gifCopyCount.fetch_add(1, std::memory_order_relaxed);
    gs.uploadImageNative(setupRegs[0], setupRegs[1], setupRegs[2], setupRegs[3], imageData, imageBytes);"""

assert mem_target in mem_src, "ps2_memory.cpp target not found!"
mem_src = mem_src.replace(mem_target, mem_repl)
with open("PS2Recomp/ps2xRuntime/src/lib/ps2_memory.cpp", "w", encoding="utf-8", newline="\r\n") as f:
    f.write(mem_src)
print("Updated ps2_memory.cpp successfully.")

# 2. Edit gs_cpu_backend.cpp
with open("PS2Recomp/ps2xRuntime/src/lib/gs/gs_cpu_backend.cpp", "r", encoding="utf-8") as f:
    gs_src = f.read().replace("\r\n", "\n")

gs_target1 = "static void writeUncompressedPng(uint32_t w, uint32_t h, const uint8_t *rgba, const char *filename)"
gs_repl1 = "void writeUncompressedPng(uint32_t w, uint32_t h, const uint8_t *rgba, const char *filename)"
assert gs_target1 in gs_src, "gs_cpu_backend.cpp target 1 not found!"
gs_src = gs_src.replace(gs_target1, gs_repl1)

gs_target2 = """        const uint32_t primitiveIndex = s_debugPrimitiveCount.fetch_add(1u, std::memory_order_relaxed);
        if (primitiveIndex == 64u)
        {
            extern void ps2xSafeLog(const char *fmt, ...);
            ps2xSafeLog("[log] cap reached for tag gs:prim at idx 64\\n");
            std::fflush(stderr);
        }
        gsRecordPrimitiveFbp(ctx.frame.fbp);
        if (primitiveIndex < 64u)"""

gs_repl2 = """        const uint32_t primitiveIndex = s_debugPrimitiveCount.fetch_add(1u, std::memory_order_relaxed);
        if (primitiveIndex == 512u)
        {
            extern void ps2xSafeLog(const char *fmt, ...);
            ps2xSafeLog("[log] cap reached for tag gs:prim at idx 512\\n");
            std::fflush(stderr);
        }
        gsRecordPrimitiveFbp(ctx.frame.fbp);
        if (primitiveIndex < 512u)"""

assert gs_target2 in gs_src, "gs_cpu_backend.cpp target 2 not found!"
gs_src = gs_src.replace(gs_target2, gs_repl2)

with open("PS2Recomp/ps2xRuntime/src/lib/gs/gs_cpu_backend.cpp", "w", encoding="utf-8", newline="\r\n") as f:
    f.write(gs_src)
print("Updated gs_cpu_backend.cpp successfully.")

# 3. Edit ps2_runtime.cpp
with open("PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp", "r", encoding="utf-8") as f:
    rt_src = f.read().replace("\r\n", "\n")

rt_target1 = """            ps2xSafeLog("[frame:upload] idx=%u tick=%llu displayFbp=%u sourceFbp=%u size=%ux%u preferred=%u hash=0x%08x\\n",
                        s_uploadDebugCount,
                        (unsigned long long)currentTick,
                        displayFbp,
                        sourceFbp,
                        width,
                        height,
                        usedPreferredDisplaySource ? 1u : 0u,
                        frameHash);"""

rt_repl1 = """            ps2xSafeLog("[frame:upload] idx=%u tick=%llu displayFbp=%u sourceFbp=%u size=%ux%u preferred=%u hash=0x%08x\\n",
                        s_uploadDebugCount,
                        (unsigned long long)currentTick,
                        displayFbp,
                        sourceFbp,
                        width,
                        height,
                        usedPreferredDisplaySource ? 1u : 0u,
                        frameHash);
            if ((currentTick >= 68 && currentTick <= 75) || frameHash == 0xefb69dc5u || s_uploadDebugCount == 69u)
            {
                static bool s_tick70Dumped = false;
                if (!s_tick70Dumped && !s_scratch.empty() && width != 0 && height != 0)
                {
                    s_tick70Dumped = true;
                    extern void writeUncompressedPng(uint32_t w, uint32_t h, const uint8_t *rgba, const char *filename);
                    std::filesystem::create_directories("frames");
                    writeUncompressedPng(width, height, s_scratch.data(), "frames/frame_tick70.png");
                    ps2xSafeLog("[frame:dump] Dumped frame at tick=%llu idx=%u hash=0x%08x to frames/frame_tick70.png\\n",
                                (unsigned long long)currentTick, s_uploadDebugCount, frameHash);
                }
            }"""

assert rt_target1 in rt_src, "ps2_runtime.cpp target 1 not found!"
rt_src = rt_src.replace(rt_target1, rt_repl1)

rt_target2 = """        auto it = s_boundConfigStubs.find(pc);
        if (it != s_boundConfigStubs.end())
        {
            it->second.handler(rdram, ctx, runtime);
            if (it->second.name == "vfprintf" || it->second.name == "_vfprintf_r" ||
                it->second.name == "sprintf" || it->second.name == "_sprintf_r" ||
                it->second.name == "printf" || it->second.name == "_printf_r")
            {
                std::lock_guard<std::mutex> lock(s_logMutex);
                std::fputc('\\n', stderr);
                std::fflush(stderr);
            }
        }"""

rt_repl2 = """        auto it = s_boundConfigStubs.find(pc);
        if (it != s_boundConfigStubs.end())
        {
            static int s_tracePrintf = -1;
            if (s_tracePrintf == -1)
            {
                const char *env = std::getenv("PS2X_TRACE_PRINTF");
                s_tracePrintf = (env && (std::strcmp(env, "1") == 0 || std::strcmp(env, "true") == 0)) ? 1 : 0;
            }

            if (s_tracePrintf == 0 && (it->second.name == "vfprintf" || it->second.name == "_vfprintf_r"))
            {
#ifdef _WIN32
                static int s_nullFd = -1;
                if (s_nullFd == -1) {
                    s_nullFd = _open("NUL", 0x0002 /* _O_RDWR */);
                }
                std::fflush(stderr);
                int saved_stderr = _dup(2);
                if (s_nullFd >= 0) {
                    _dup2(s_nullFd, 2);
                }
                it->second.handler(rdram, ctx, runtime);
                std::fflush(stderr);
                if (saved_stderr >= 0) {
                    _dup2(saved_stderr, 2);
                    _close(saved_stderr);
                }
#else
                it->second.handler(rdram, ctx, runtime);
#endif
            }
            else
            {
                it->second.handler(rdram, ctx, runtime);
                if (s_tracePrintf == 1 &&
                    (it->second.name == "vfprintf" || it->second.name == "_vfprintf_r" ||
                     it->second.name == "sprintf" || it->second.name == "_sprintf_r" ||
                     it->second.name == "printf" || it->second.name == "_printf_r"))
                {
                    std::lock_guard<std::mutex> lock(s_logMutex);
                    std::fputc('\\n', stderr);
                    std::fflush(stderr);
                }
            }
        }"""

assert rt_target2 in rt_src, "ps2_runtime.cpp target 2 not found!"
rt_src = rt_src.replace(rt_target2, rt_repl2)

# Make sure io.h is included for _open, _dup, _dup2 in Windows
if "#include <io.h>" not in rt_src:
    rt_src = "#ifdef _WIN32\n#include <io.h>\n#endif\n" + rt_src

with open("PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp", "w", encoding="utf-8", newline="\r\n") as f:
    f.write(rt_src)
print("Updated ps2_runtime.cpp successfully.")
