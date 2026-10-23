import os
import sys

def patch_rpc():
    path = "PS2Recomp/ps2xRuntime/src/lib/Kernel/Syscalls/RPC.cpp"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    global_decl = """#include <atomic>
#include <mutex>
#include <cstring>
#include <string>

std::atomic<uint32_t> g_diagSg2Fno0Calls{0};
std::atomic<uint32_t> g_diagDbcBufferWrites{0};
std::atomic<uint32_t> g_diagCid1Requests{0};
std::atomic<uint64_t> g_diagCid1BytesServed{0};
static std::mutex s_diagCid1PathMutex;
static char s_diagLastCid1Path[256] = "";

void diagGetLastCid1Path(char *out, size_t maxLen)
{
    if (!out || maxLen == 0) return;
    std::lock_guard<std::mutex> lock(s_diagCid1PathMutex);
    std::strncpy(out, s_diagLastCid1Path, maxLen - 1);
    out[maxLen - 1] = '\\0';
}

void diagSetLastCid1Path(const std::string &path)
{
    std::lock_guard<std::mutex> lock(s_diagCid1PathMutex);
    std::strncpy(s_diagLastCid1Path, path.c_str(), sizeof(s_diagLastCid1Path) - 1);
    s_diagLastCid1Path[sizeof(s_diagLastCid1Path) - 1] = '\\0';
}
"""

    t_ns = "namespace ps2_syscalls"
    if t_ns in content:
        content = content.replace(t_ns, global_decl + "\n" + t_ns, 1)
    else:
        assert t_ns.replace("\n", "\r\n") in content
        content = content.replace(t_ns.replace("\n", "\r\n"), (global_decl + "\n" + t_ns).replace("\n", "\r\n"), 1)

    # In dbcUpdatePadBuffers:
    t_dbc = "dbcWritePacket(rdram, s_dbcWorkAddr, pad, s_dbcSeq);\n            }\n        }"
    r_dbc = "dbcWritePacket(rdram, s_dbcWorkAddr, pad, s_dbcSeq);\n            }\n            g_diagDbcBufferWrites.fetch_add(1, std::memory_order_relaxed);\n        }"
    if t_dbc in content:
        content = content.replace(t_dbc, r_dbc)
    else:
        assert t_dbc.replace("\n", "\r\n") in content
        content = content.replace(t_dbc.replace("\n", "\r\n"), r_dbc.replace("\n", "\r\n"))

    # In SG2_AUDIO:
    t_sg2 = "dbcUpdatePadBuffers(call.rdram, call.runtime);\n                    return 0;"
    r_sg2 = "dbcUpdatePadBuffers(call.rdram, call.runtime);\n                    g_diagSg2Fno0Calls.fetch_add(1, std::memory_order_relaxed);\n                    return 0;"
    if t_sg2 in content:
        content = content.replace(t_sg2, r_sg2)
    else:
        assert t_sg2.replace("\n", "\r\n") in content
        content = content.replace(t_sg2.replace("\n", "\r\n"), r_sg2.replace("\n", "\r\n"))

    # In handleCid1Request:
    t_cid1 = "uint32_t ringTail = destExtra + alignedCmdSize;"
    r_cid1 = "uint32_t ringTail = destExtra + alignedCmdSize;\n            g_diagCid1Requests.fetch_add(1, std::memory_order_relaxed);"
    if t_cid1 in content:
        content = content.replace(t_cid1, r_cid1)
    else:
        assert t_cid1.replace("\n", "\r\n") in content
        content = content.replace(t_cid1.replace("\n", "\r\n"), r_cid1.replace("\n", "\r\n"))

    # In Open:
    t_open = "std::string path(pathPtr);"
    r_open = "std::string path(pathPtr);\n                    diagSetLastCid1Path(path);"
    if t_open in content:
        content = content.replace(t_open, r_open, 1)
    else:
        assert t_open.replace("\n", "\r\n") in content
        content = content.replace(t_open.replace("\n", "\r\n"), r_open.replace("\n", "\r\n"), 1)

    # In ReadFd:
    t_readfd = "slot.offset += toRead;\n                        reply.result = static_cast<uint32_t>(toRead);"
    r_readfd = "slot.offset += toRead;\n                        g_diagCid1BytesServed.fetch_add(toRead, std::memory_order_relaxed);\n                        diagSetLastCid1Path(slot.entry.fullPath);\n                        reply.result = static_cast<uint32_t>(toRead);"
    if t_readfd in content:
        content = content.replace(t_readfd, r_readfd)
    else:
        assert t_readfd.replace("\n", "\r\n") in content
        content = content.replace(t_readfd.replace("\n", "\r\n"), r_readfd.replace("\n", "\r\n"))

    # In ReadPath:
    t_readpath = "ps2x::vfi::VfiArchive::instance().readFileData(*entry, fileOffset, toRead, rdram + eeDst);\n                        }\n                        reply.result = static_cast<uint32_t>(toRead);"
    r_readpath = "ps2x::vfi::VfiArchive::instance().readFileData(*entry, fileOffset, toRead, rdram + eeDst);\n                        }\n                        g_diagCid1BytesServed.fetch_add(toRead, std::memory_order_relaxed);\n                        diagSetLastCid1Path(path);\n                        reply.result = static_cast<uint32_t>(toRead);"
    if t_readpath in content:
        content = content.replace(t_readpath, r_readpath)
    else:
        assert t_readpath.replace("\n", "\r\n") in content
        content = content.replace(t_readpath.replace("\n", "\r\n"), r_readpath.replace("\n", "\r\n"))

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("RPC.cpp patched successfully")

def patch_memory_card():
    path = "PS2Recomp/ps2xRuntime/src/lib/Kernel/Stubs/MemoryCard.cpp"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    decl = """#include <atomic>
std::atomic<uint32_t> g_diagMcCalls{0};
"""
    t_pos = "namespace ps2_stubs"
    if t_pos in content:
        content = content.replace(t_pos, decl + "\n" + t_pos, 1)
    else:
        assert t_pos.replace("\n", "\r\n") in content
        content = content.replace(t_pos.replace("\n", "\r\n"), (decl + "\n" + t_pos).replace("\n", "\r\n"), 1)

    # sceMcGetDir count and PS2X_MC_GETDIR:
    t_getdir = "void sceMcGetDir(uint8_t *rdram, R5900Context *ctx, PS2Runtime *runtime)\n    {"
    r_getdir = "void sceMcGetDir(uint8_t *rdram, R5900Context *ctx, PS2Runtime *runtime)\n    {\n        g_diagMcCalls.fetch_add(1, std::memory_order_relaxed);"
    if t_getdir in content:
        content = content.replace(t_getdir, r_getdir)
    else:
        assert t_getdir.replace("\n", "\r\n") in content
        content = content.replace(t_getdir.replace("\n", "\r\n"), r_getdir.replace("\n", "\r\n"))

    t_res = "setMcCommandResultLocked(kMcCmdGetDir, result);"
    r_res = """if (result == kMcResultNoEntry)
            {
                const char *mcEnv = std::getenv("PS2X_MC_GETDIR");
                const char *modeStr = "noentry";
                if (mcEnv && std::strcmp(mcEnv, "zero") == 0)
                {
                    result = 0;
                    modeStr = "zero";
                }
                else if (mcEnv && std::strcmp(mcEnv, "nodev") == 0)
                {
                    result = kMcResultNoFormat;
                    modeStr = "nodev";
                }
                RUNTIME_LOG("[MC] GetDir non-existent dir returned " << result << " (mode=" << modeStr << ")");
            }
            setMcCommandResultLocked(kMcCmdGetDir, result);"""
    if t_res in content:
        content = content.replace(t_res, r_res)
    else:
        assert t_res.replace("\n", "\r\n") in content
        content = content.replace(t_res.replace("\n", "\r\n"), r_res.replace("\n", "\r\n"))

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("MemoryCard.cpp patched successfully")

def patch_gs():
    path = "PS2Recomp/ps2xRuntime/src/lib/gs/gs_cpu_backend.cpp"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # External linkage outside anonymous namespace
    decl = """#include <atomic>
#include <vector>
#include <utility>

static std::atomic<uint32_t> s_diagPrimsPerFbp[512]{};
void gsRecordPrimitiveFbp(uint32_t fbp)
{
    if (fbp < 512u)
    {
        s_diagPrimsPerFbp[fbp].fetch_add(1u, std::memory_order_relaxed);
    }
}

void gsGetAndResetPrimsPerFbp(std::vector<std::pair<uint32_t, uint32_t>> &out)
{
    out.clear();
    for (uint32_t i = 0; i < 512u; ++i)
    {
        uint32_t count = s_diagPrimsPerFbp[i].exchange(0u, std::memory_order_relaxed);
        if (count > 0u)
        {
            out.emplace_back(i, count);
        }
    }
}
"""
    t_pos = "GSCpuBackend::GSCpuBackend()"
    if t_pos in content:
        content = content.replace(t_pos, decl + "\n" + t_pos, 1)
    else:
        assert t_pos.replace("\n", "\r\n") in content
        content = content.replace(t_pos.replace("\n", "\r\n"), (decl + "\n" + t_pos).replace("\n", "\r\n"), 1)

    # In DrawPrimitive: record FBP and cap
    t_prim = "const uint32_t primitiveIndex = s_debugPrimitiveCount.fetch_add(1u, std::memory_order_relaxed);"
    r_prim = """const uint32_t primitiveIndex = s_debugPrimitiveCount.fetch_add(1u, std::memory_order_relaxed);
        if (primitiveIndex == 64u)
        {
            extern void ps2xSafeLog(const char *fmt, ...);
            ps2xSafeLog("[log] cap reached for tag gs:prim at idx 64\\n");
            std::fflush(stderr);
        }
        gsRecordPrimitiveFbp(ctx.frame.fbp);"""
    if t_prim in content:
        content = content.replace(t_prim, r_prim)
    else:
        assert t_prim.replace("\n", "\r\n") in content
        content = content.replace(t_prim.replace("\n", "\r\n"), r_prim.replace("\n", "\r\n"))

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("gs_cpu_backend.cpp patched successfully")

def patch_pad():
    path = "PS2Recomp/ps2xRuntime/src/lib/Kernel/Stubs/Pad.cpp"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Global extern ps2xSafeLog above namespace
    decl = "extern void ps2xSafeLog(const char *fmt, ...);\n"
    t_ns = "namespace ps2_stubs"
    if t_ns in content:
        content = content.replace(t_ns, decl + t_ns, 1)
    else:
        assert t_ns.replace("\n", "\r\n") in content
        content = content.replace(t_ns.replace("\n", "\r\n"), (decl + t_ns).replace("\n", "\r\n"), 1)

    # Cap report on pad read
    t_padcap = "if (g_padReadLogCount < 48)"
    r_padcap = """if (g_padReadLogCount == 48)
            {
                static bool s_padCapReported = false;
                if (!s_padCapReported)
                {
                    s_padCapReported = true;
                    ::ps2xSafeLog("[log] cap reached for tag pad:read at idx 48\\n");
                    std::fflush(stderr);
                }
            }
            if (g_padReadLogCount < 48)"""
    if t_padcap in content:
        content = content.replace(t_padcap, r_padcap)
    else:
        assert t_padcap.replace("\n", "\r\n") in content
        content = content.replace(t_padcap.replace("\n", "\r\n"), r_padcap.replace("\n", "\r\n"))

    # In getCurrentPadInput:
    t_getpad = "applyGamepadState(state);\n                applyKeyboardState(state, true);\n            }\n        }\n        return state;"
    r_getpad = """applyGamepadState(state);\n                applyKeyboardState(state, true);\n            }\n        }

        // PS2X_INJECT_PAD support
        struct PadInjection {
            std::string button;
            uint16_t mask = 0;
            uint64_t startMs = 0;
            uint64_t durMs = 0;
            bool active = false;
        };
        static std::vector<PadInjection> s_injections;
        static bool s_injParsed = false;
        static auto s_bootTime = std::chrono::steady_clock::now();

        if (!s_injParsed)
        {
            s_injParsed = true;
            const char *env = std::getenv("PS2X_INJECT_PAD");
            if (env && env[0] != '\\0')
            {
                std::string str(env);
                size_t pos = 0;
                while (pos < str.size())
                {
                    size_t comma = str.find(',', pos);
                    std::string item = str.substr(pos, (comma == std::string::npos) ? std::string::npos : (comma - pos));
                    pos = (comma == std::string::npos) ? str.size() : (comma + 1);

                    size_t c1 = item.find(':');
                    size_t c2 = (c1 != std::string::npos) ? item.find(':', c1 + 1) : std::string::npos;
                    if (c1 != std::string::npos && c2 != std::string::npos)
                    {
                        PadInjection inj;
                        inj.button = item.substr(0, c1);
                        try {
                            inj.startMs = std::stoull(item.substr(c1 + 1, c2 - c1 - 1));
                            inj.durMs = std::stoull(item.substr(c2 + 1));
                        } catch (...) { continue; }

                        if (inj.button == "START") inj.mask = kPadBtnStart;
                        else if (inj.button == "CROSS") inj.mask = kPadBtnCross;
                        else if (inj.button == "CIRCLE") inj.mask = kPadBtnCircle;
                        else if (inj.button == "UP") inj.mask = kPadBtnUp;
                        else if (inj.button == "DOWN") inj.mask = kPadBtnDown;
                        else if (inj.button == "LEFT") inj.mask = kPadBtnLeft;
                        else if (inj.button == "RIGHT") inj.mask = kPadBtnRight;

                        if (inj.mask != 0)
                        {
                            s_injections.push_back(inj);
                        }
                    }
                }
            }
        }

        const uint64_t nowMs = std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - s_bootTime).count();
        for (auto &inj : s_injections)
        {
            bool shouldBeActive = (nowMs >= inj.startMs && nowMs < (inj.startMs + inj.durMs));
            if (shouldBeActive != inj.active)
            {
                inj.active = shouldBeActive;
                ::ps2xSafeLog("[pad] inject %s %s\\n", inj.button.c_str(), shouldBeActive ? "down" : "up");
                std::fflush(stderr);
            }
            if (inj.active)
            {
                state.buttons &= ~inj.mask;
            }
        }

        return state;"""
    if t_getpad in content:
        content = content.replace(t_getpad, r_getpad)
    else:
        assert t_getpad.replace("\n", "\r\n") in content
        content = content.replace(t_getpad.replace("\n", "\r\n"), r_getpad.replace("\n", "\r\n"))

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Pad.cpp patched successfully")

def patch_runtime():
    path = "PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Include DiagSampler.h
    t_inc = '#include "ps2_runtime.h"'
    r_inc = '#include "ps2_runtime.h"\n#include "diag/DiagSampler.h"\nstd::atomic<uint32_t> g_diagMscalCount{0};\nstd::atomic<uint32_t> g_diagGifPacketCount{0};'
    if t_inc in content:
        content = content.replace(t_inc, r_inc)
    else:
        assert t_inc.replace("\n", "\r\n") in content
        content = content.replace(t_inc.replace("\n", "\r\n"), r_inc.replace("\n", "\r\n"))

    # Count GIF packet in m_gifArbiter
    t_gif = 'm_gifArbiter.setProcessPacketFn([this](const uint8_t *data, uint32_t size)\n                                    { m_gs.processGIFPacket(data, size); });'
    r_gif = 'm_gifArbiter.setProcessPacketFn([this](const uint8_t *data, uint32_t size)\n                                    { g_diagGifPacketCount.fetch_add(1, std::memory_order_relaxed); m_gs.processGIFPacket(data, size); });'
    if t_gif in content:
        content = content.replace(t_gif, r_gif)
    else:
        assert t_gif.replace("\n", "\r\n") in content
        content = content.replace(t_gif.replace("\n", "\r\n"), r_gif.replace("\n", "\r\n"))

    # Count MSCAL in m_vu1MscalCallback
    t_mscal = 'm_memory.setVu1MscalCallback([this](uint32_t startPC, uint32_t top, uint32_t itop)\n                                 {'
    r_mscal = 'm_memory.setVu1MscalCallback([this](uint32_t startPC, uint32_t top, uint32_t itop)\n                                 {\n                                     g_diagMscalCount.fetch_add(1, std::memory_order_relaxed);'
    if t_mscal in content:
        content = content.replace(t_mscal, r_mscal)
    else:
        assert t_mscal.replace("\n", "\r\n") in content
        content = content.replace(t_mscal.replace("\n", "\r\n"), r_mscal.replace("\n", "\r\n"))

    # In updateDisplayTexture: cap message and sampler hook
    t_upload = '++s_uploadDebugCount;\n    });\n    s_lastDisplayFbp = displayFbp;'
    r_upload = """++s_uploadDebugCount;
        if (s_uploadDebugCount == 128u)
        {
            ps2xSafeLog("[log] cap reached for tag frame:upload at idx 128\\n");
            std::fflush(stderr);
        }
    });
    s_lastDisplayFbp = displayFbp;"""
    if t_upload in content:
        content = content.replace(t_upload, r_upload)
    else:
        assert t_upload.replace("\n", "\r\n") in content
        content = content.replace(t_upload.replace("\n", "\r\n"), r_upload.replace("\n", "\r\n"))

    t_sampler_hook = "s_hasUploadedFrame = true;\n\n    static uint64_t s_lastDumpTick"
    r_sampler_hook = "s_hasUploadedFrame = true;\n    ps2_diag::DiagSampler::onFrame(rt, currentTick, s_uploadBuffer, displayFbp, sourceFbp, width, height);\n\n    static uint64_t s_lastDumpTick"
    if t_sampler_hook in content:
        content = content.replace(t_sampler_hook, r_sampler_hook)
    else:
        assert t_sampler_hook.replace("\n", "\r\n") in content
        content = content.replace(t_sampler_hook.replace("\n", "\r\n"), r_sampler_hook.replace("\n", "\r\n"))

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("ps2_runtime.cpp patched successfully")

if __name__ == "__main__":
    patch_rpc()
    patch_memory_card()
    patch_gs()
    patch_pad()
    patch_runtime()
