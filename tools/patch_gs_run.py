"""One-shot patch (PERF-GR): GS draw runs.
Header: GSRasterBackend::SubmitRun (state once + many prims, default loops Submit), GS keeps a cached draw state (rebuilt only after a state register write)
and queues prims into a run that is submitted in one backend call; everything else that touches the backend (or the deferred display copy) flushes the run first.
Vulkan wrapper overrides SubmitRun: one lock for the whole run, one GSPrimitiveBatch whose state is filled once."""
import re

base = "C:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/"


def load(path):
    t = open(path, encoding="utf-8", newline="").read()
    crlf = "\r\n" in t
    return t.replace("\r\n", "\n"), crlf


def save(path, t, crlf):
    if crlf:
        t = t.replace("\n", "\r\n")
    open(path, "w", encoding="utf-8", newline="").write(t)


def rep1(t, a, b):
    assert t.count(a) == 1, (t.count(a), a[:100])
    return t.replace(a, b)


# ---- gs_backend.h
p = base + "include/runtime/gs/gs_backend.h"
t, crlf = load(p)
t = rep1(t, "#include <cstdint>\n#include <vector>\n", "#include <array>\n#include <cstddef>\n#include <cstdint>\n#include <vector>\n")
t = rep1(t, "class GSRasterBackend\n{", """// PERF-GR: one primitive of a draw run (the run shares one GSDrawState)
struct GSRunPrim
{
    std::array<GSVertex, 3> vertices{};
    uint8_t vertexCount = 0;
};

class GSRasterBackend
{""")
t = rep1(t, "    virtual void LoadClut(", """    // PERF-GR: consecutive prims with identical draw state; same effect as calling Submit once per prim
    virtual void SubmitRun(const GSDrawState &state, const GSRunPrim *prims, size_t count)
    {
        GSPrimitiveBatch b;
        b.state = state;
        for (size_t i = 0; i < count; ++i)
        {
            b.vertices = prims[i].vertices;
            b.vertexCount = prims[i].vertexCount;
            Submit(b);
        }
    }
    virtual void LoadClut(""")
save(p, t, crlf)

# ---- gs_frontend.h
p = base + "include/runtime/gs/gs_frontend.h"
t, crlf = load(p)
t = rep1(t, "    GSPrimitiveBatch buildDrawBatch(int vertexCount) const;\n",
         """    GSPrimitiveBatch buildDrawBatch(int vertexCount) const;
    // PERF-GR: draw runs
    void refreshDrawBatch(int vertexCount);
    void queueDraw(const GSPrimitiveBatch &batch);
    void flushPendingDraws() const;
    void flushDeferredOrdered();
""")
t = rep1(t, "    GSContext &activeContext();\n",
         """    GSContext &activeContext();

    // PERF-GR
    GSPrimitiveBatch m_drawBatch{};
    bool m_stateDirty = true;
    uint64_t m_stateSerial = 1;
    mutable GSDrawState m_runState{};
    mutable uint64_t m_runSerial = 0;
    mutable std::vector<GSRunPrim> m_runPrims;
""")
save(p, t, crlf)

# ---- gs_frontend.cpp
p = base + "src/lib/gs/gs_frontend.cpp"
t, crlf = load(p)

# ordered deferred flush everywhere inside GS members, except the snapshot path that runs outside m_stateMutex
t = t.replace("flushDeferredDisplayCopy(m_backend.get());", "flushDeferredOrdered();")
t = rep1(t, "    if (!m_backend)\n        return;\n    flushDeferredOrdered();",
         "    if (!m_backend)\n        return;\n    flushDeferredDisplayCopy(m_backend.get()); // outside m_stateMutex: no pending run here");

# the other backend touch points flush the run first
for fn in ["LoadClut", "BeginTransfer", "TextureFlush", "UploadImage", "ClearFramebuffer", "ConsumeLocalToHostBytes", "ReadVram", "WriteVram"]:
    t = t.replace("m_backend->%s(" % fn, "(flushPendingDraws(), m_backend.get())->%s(" % fn)
t = rep1(t, "            m_backend->Flush();\n            m_backend->Sync(GSSyncReason::Finish);",
         "            (flushPendingDraws(), m_backend.get())->Flush();\n            m_backend->Sync(GSSyncReason::Finish);")
t = rep1(t, "    if (m_backend)\n    {\n        m_backend->Flush();\n        m_backend->Sync(GSSyncReason::Reset);\n        m_backend->Reset();",
         "    if (m_backend)\n    {\n        (flushPendingDraws(), m_backend.get())->Flush();\n        m_backend->Sync(GSSyncReason::Reset);\n        m_backend->Reset();\n        m_stateDirty = true;")
t = rep1(t, "    if (m_backend)\n    {\n        m_backend->Flush();\n        m_backend->Sync(GSSyncReason::Reset);\n\n        // The external",
         "    if (m_backend)\n    {\n        (flushPendingDraws(), m_backend.get())->Flush();\n        m_backend->Sync(GSSyncReason::Reset);\n\n        // The external")
t = rep1(t, "    m_backend = std::move(backend);\n    m_backend->Initialize(m_localMemoryStorage, m_localMemorySize);\n",
         "    m_backend = std::move(backend);\n    m_stateDirty = true;\n    m_backend->Initialize(m_localMemoryStorage, m_localMemorySize);\n")

t = rep1(t, "    std::memset(m_ctx, 0, sizeof(m_ctx));\n    m_prim = {};", "    std::memset(m_ctx, 0, sizeof(m_ctx));\n    m_stateDirty = true; // PERF-GR\n    m_prim = {};")

# any packet / register entry point leaves no pending prims behind (the presenter flushes the backend from another thread)
t = rep1(t, "    std::unique_lock<std::recursive_mutex> lock(m_stateMutex);\n\n    if (probeActive) {\n        auto tLockAcquired",
         "    std::unique_lock<std::recursive_mutex> lock(m_stateMutex);\n    struct RunFlush { const GS *g; ~RunFlush() { g->flushPendingDraws(); } } runFlush{this}; // PERF-GR\n\n    if (probeActive) {\n        auto tLockAcquired")
t = rep1(t, "    std::lock_guard<std::recursive_mutex> lock(m_stateMutex);\n    writeRegisterUnlocked(regAddr, value);\n}",
         "    std::lock_guard<std::recursive_mutex> lock(m_stateMutex);\n    struct RunFlush { const GS *g; ~RunFlush() { g->flushPendingDraws(); } } runFlush{this}; // PERF-GR\n    writeRegisterUnlocked(regAddr, value);\n}")

# state dirty tracking: every register write except per-vertex data
t = rep1(t, "    switch (regAddr)\n    {\n    case GS_REG_PRIM:\n    {\n        m_primRegister = decodePrimRegister(value);",
         """    switch (regAddr) // PERF-GR: anything but per-vertex data can change the draw state
    {
    case GS_REG_RGBAQ: case GS_REG_ST: case GS_REG_UV: case GS_REG_XYZF2: case GS_REG_XYZ2:
    case GS_REG_XYZF3: case GS_REG_XYZ3: case GS_REG_FOG:
        break;
    default:
        m_stateDirty = true;
        break;
    }

    switch (regAddr)
    {
    case GS_REG_PRIM:
    {
        m_primRegister = decodePrimRegister(value);""")

# vertexKick: cached batch + queued submit
t = rep1(t, "        GSPrimitiveBatch batch = buildDrawBatch(needed);\n        updatePreferredDisplaySourceForDraw(batch);",
         "        refreshDrawBatch(needed); // PERF-GR\n        GSPrimitiveBatch &batch = m_drawBatch;\n        updatePreferredDisplaySourceForDraw(batch);")
t = rep1(t, "            const uint64_t gqS0 = __rdtsc(); // PROBE-GQ2\n            m_backend->Submit(batch);\n            g_gqSubmit.fetch_add(__rdtsc() - gqS0, std::memory_order_relaxed);\n            g_gqDraws.fetch_add(1, std::memory_order_relaxed);\n",
         "            queueDraw(batch); // PERF-GR\n")

t = rep1(t, "GSPrimitiveBatch GS::buildDrawBatch(int vertexCount) const\n{", """// PERF-GR: the draw state is rebuilt only after a state register write; per prim only the vertices change
void GS::refreshDrawBatch(int vertexCount)
{
    GSPrimitiveBatch &batch = m_drawBatch;
    if (m_stateDirty)
    {
        m_stateDirty = false;
        ++m_stateSerial;
        GSDrawState &s = batch.state;
        s.context = m_ctx[m_prim.ctxt ? 1 : 0];
        s.prim = m_prim;
        s.texa = m_texa;
        s.texclut = m_texclut;
        s.pabe = m_pabe;
        s.scanmsk = m_scanmsk;
        s.dimx = m_dimx;
        s.dthe = m_dthe;
        s.colclamp = m_colclamp;
        s.fogR = m_fogR;
        s.fogG = m_fogG;
        s.fogB = m_fogB;
        s.textureWidth = static_cast<uint16_t>(1u << std::min<uint32_t>(s.context.tex0.tw, 10u));
        s.textureHeight = static_cast<uint16_t>(1u << std::min<uint32_t>(s.context.tex0.th, 10u));
        const uint64_t tex1 = s.context.tex1;
        const uint8_t mmag = static_cast<uint8_t>((tex1 >> 5u) & 0x1u);
        const uint8_t mmin = static_cast<uint8_t>((tex1 >> 6u) & 0x7u);
        s.linearFilter = mmag != 0u || mmin == 1u || (mmin & 0x4u) != 0u;
    }
    batch.vertexCount = static_cast<uint8_t>(std::min(vertexCount, 3));
    for (int i = 0; i < 3; ++i)
        batch.vertices[static_cast<size_t>(i)] = (i < batch.vertexCount) ? m_vtxQueue[i] : GSVertex{};
}

void GS::queueDraw(const GSPrimitiveBatch &batch)
{
    if (!m_runPrims.empty() && m_runSerial != m_stateSerial)
        flushPendingDraws();
    if (m_runPrims.empty())
    {
        m_runState = batch.state;
        m_runSerial = m_stateSerial;
        if (m_runPrims.capacity() < 512u)
            m_runPrims.reserve(512u);
    }
    GSRunPrim rp;
    rp.vertices = batch.vertices;
    rp.vertexCount = batch.vertexCount;
    m_runPrims.push_back(rp);
    if (m_runPrims.size() >= 512u)
        flushPendingDraws();
}

void GS::flushPendingDraws() const
{
    if (m_runPrims.empty())
        return;
    if (m_backend)
    {
        const uint64_t gqS0 = __rdtsc(); // PROBE-GQ2
        m_backend->SubmitRun(m_runState, m_runPrims.data(), m_runPrims.size());
        g_gqSubmit.fetch_add(__rdtsc() - gqS0, std::memory_order_relaxed);
        g_gqDraws.fetch_add(m_runPrims.size(), std::memory_order_relaxed);
    }
    m_runPrims.clear();
}

void GS::flushDeferredOrdered()
{
    flushPendingDraws();
    flushDeferredDisplayCopy(m_backend.get());
}

GSPrimitiveBatch GS::buildDrawBatch(int vertexCount) const
{""")
save(p, t, crlf)

# ---- Vulkan wrapper: one lock per run
p = base + "src/lib/gs/ps2_vk_gs_backend.cpp"
t, crlf = load(p)
t = rep1(t, "        void LoadClut(const GSTex0Reg &tex0, const GSTexClutReg &texclut) override\n        {\n            const uint64_t gqL0",
         """        void SubmitRun(const GSDrawState &state, const GSRunPrim *prims, size_t count) override // PERF-GR
        {
            const uint64_t gqL0 = __rdtsc(); // PROBE-GQ2
            std::lock_guard<std::mutex> lk(m_);
            g_gqLockWait.fetch_add(__rdtsc() - gqL0, std::memory_order_relaxed);
            g_gqLockWaits.fetch_add(1, std::memory_order_relaxed);
            GSPrimitiveBatch batch;
            batch.state = state;
            for (size_t i = 0; i < count; ++i)
            {
                batch.vertices = prims[i].vertices;
                batch.vertexCount = prims[i].vertexCount;
                if (ref_)
                    ref_->Submit(batch);
                if (!vkReady_ || batch.vertexCount == 0u)
                {
                    cpuDraw(batch);
                    continue;
                }
                const int reason = gpuDraw(batch);
                if (reason > 0)
                {
                    ++fallback_[std::min(reason, 15)];
                    cpuDraw(batch);
                }
            }
        }

        void LoadClut(const GSTex0Reg &tex0, const GSTexClutReg &texclut) override
        {
            const uint64_t gqL0""")
save(p, t, crlf)
print("ok")
