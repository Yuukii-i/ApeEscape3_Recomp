"""One-shot patch (PROBE-GQ2, part 2): globals + accessors, Vulkan wrapper lock-wait / Present-hold timers, [gsq2] print. Run after patch_gsq2_probe.py."""
base = "C:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/"
BS = chr(92)


def edit(path, pairs):
    t = open(path, encoding="utf-8", newline="").read()
    crlf = "\r\n" in t
    if crlf:
        t = t.replace("\r\n", "\n")
    for a, b in pairs:
        assert t.count(a) == 1, (path, t.count(a), a[:90])
        t = t.replace(a, b)
    if crlf:
        t = t.replace("\n", "\r\n")
    open(path, "w", encoding="utf-8", newline="").write(t)


edit(base + "gs/gs_frontend.cpp", [
    ("#include <intrin.h>\n",
     '#include <intrin.h>\n#include <atomic>\nstd::atomic<uint64_t> g_gqBuild{0}, g_gqSubmit{0}, g_gqDraws{0}; // PROBE-GQ2\n'
     'extern "C" void ps2_gs_front_stats(uint64_t *out) { out[0] = g_gqBuild.exchange(0); out[1] = g_gqSubmit.exchange(0); out[2] = g_gqDraws.exchange(0); }\n'),
])
edit(base + "gs/ps2_vk_gs_backend.cpp", [
    ("#include <intrin.h>\n",
     '#include <intrin.h>\nstatic std::atomic<uint64_t> g_gqLockWait{0}, g_gqLockWaits{0}, g_gqPresentHold{0}, g_gqPresents{0}; // PROBE-GQ2\n'
     'extern "C" void ps2_gs_vk_stats(uint64_t *out) { out[0] = g_gqLockWait.exchange(0); out[1] = g_gqLockWaits.exchange(0); out[2] = g_gqPresentHold.exchange(0); out[3] = g_gqPresents.exchange(0); }\n'),
    ("        void Submit(const GSPrimitiveBatch &batch) override\n        {\n            std::lock_guard<std::mutex> lk(m_);\n",
     "        void Submit(const GSPrimitiveBatch &batch) override\n        {\n            const uint64_t gqL0 = __rdtsc(); // PROBE-GQ2\n            std::lock_guard<std::mutex> lk(m_);\n"
     "            g_gqLockWait.fetch_add(__rdtsc() - gqL0, std::memory_order_relaxed);\n            g_gqLockWaits.fetch_add(1, std::memory_order_relaxed);\n"),
    ("        void LoadClut(const GSTex0Reg &tex0, const GSTexClutReg &texclut) override\n        {\n            std::lock_guard<std::mutex> lk(m_);\n",
     "        void LoadClut(const GSTex0Reg &tex0, const GSTexClutReg &texclut) override\n        {\n            const uint64_t gqL0 = __rdtsc(); // PROBE-GQ2\n            std::lock_guard<std::mutex> lk(m_);\n"
     "            g_gqLockWait.fetch_add(__rdtsc() - gqL0, std::memory_order_relaxed);\n            g_gqLockWaits.fetch_add(1, std::memory_order_relaxed);\n"),
    ("        PresentationFrame Present(const GSPresentationRequest &request) override\n        {\n            std::lock_guard<std::mutex> lk(m_);\n",
     "        PresentationFrame Present(const GSPresentationRequest &request) override\n        {\n            std::lock_guard<std::mutex> lk(m_);\n"
     "            struct GqHold // PROBE-GQ2: time the lock is held\n            {\n                uint64_t t0 = __rdtsc();\n"
     "                ~GqHold() { g_gqPresentHold.fetch_add(__rdtsc() - t0, std::memory_order_relaxed); g_gqPresents.fetch_add(1, std::memory_order_relaxed); }\n            } gqHold;\n"),
])
edit(base + "ps2_memory.cpp", [
    ('extern "C" void ps2_gs_async_stats(uint64_t *out); // PROBE-GQ',
     'extern "C" void ps2_gs_async_stats(uint64_t *out); // PROBE-GQ\nextern "C" void ps2_gs_front_stats(uint64_t *out); // PROBE-GQ2\nextern "C" void ps2_gs_vk_stats(uint64_t *out);'),
    ("            { // PROBE-FS: the heaviest waiting call sites of this window",
     '            { // PROBE-GQ2\n                uint64_t f[3], k[4];\n                ps2_gs_front_stats(f);\n                ps2_gs_vk_stats(k);\n'
     '                ps2xSafeLog("[gsq2] draws=%llu build_ms=%.0f submit_ms=%.0f | vk_lock_wait_ms=%.0f (n=%llu) present_hold_ms=%.0f (n=%llu)' + BS + 'n", (unsigned long long)f[2], static_cast<double>(f[0]) / tpm,\n'
     '                            static_cast<double>(f[1]) / tpm, static_cast<double>(k[0]) / tpm, (unsigned long long)k[1], static_cast<double>(k[2]) / tpm, (unsigned long long)k[3]);\n            }\n'
     "            { // PROBE-FS: the heaviest waiting call sites of this window"),
])
print("part 2 ok")
