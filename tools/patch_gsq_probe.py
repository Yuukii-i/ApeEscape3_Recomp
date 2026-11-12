"""One-shot patch (PROBE-GQ): GS async worker busy/idle ticks, peak queued bytes, producer block count, printed as [gsq] next to the [wait] line."""
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


edit(base + "gs/ps2_gif_arbiter.cpp", [
    ("std::atomic<bool> s_gsAsyncStarted{false};",
     "std::atomic<bool> s_gsAsyncStarted{false};\n"
     "std::atomic<uint64_t> g_gsqBusy{0}, g_gsqIdle{0}, g_gsqBlocked{0}, g_gsqPeak{0}, g_gsqPkts{0}; // PROBE-GQ"),
    ("        st.workerWaiting = true;\n        st.cvWork.wait(lock, [&] { return !st.q.empty(); });\n        st.workerWaiting = false;\n",
     "        st.workerWaiting = true;\n        const uint64_t gqI0 = __rdtsc(); // PROBE-GQ\n        st.cvWork.wait(lock, [&] { return !st.q.empty(); });\n"
     "        g_gsqIdle.fetch_add(__rdtsc() - gqI0, std::memory_order_relaxed);\n        st.workerWaiting = false;\n"),
    ("        const size_t pktSize = pkt.size();\n        st.fn(pkt.data(), static_cast<uint32_t>(pktSize));\n",
     "        const size_t pktSize = pkt.size();\n        const uint64_t gqB0 = __rdtsc(); // PROBE-GQ\n        st.fn(pkt.data(), static_cast<uint32_t>(pktSize));\n"
     "        g_gsqBusy.fetch_add(__rdtsc() - gqB0, std::memory_order_relaxed);\n        g_gsqPkts.fetch_add(1, std::memory_order_relaxed);\n"),
    ("        st.queuedBytes += d.size();\n        ++st.enqueuedPkts;\n        st.q.push_back(std::move(d));\n    }\n    if (st.workerWaiting)",
     "        st.queuedBytes += d.size();\n        if (st.queuedBytes > g_gsqPeak.load(std::memory_order_relaxed)) g_gsqPeak.store(st.queuedBytes, std::memory_order_relaxed); // PROBE-GQ\n"
     "        ++st.enqueuedPkts;\n        st.q.push_back(std::move(d));\n    }\n    if (st.workerWaiting)"),
    ("        --st.idleWaiters;\n        g_waitTicks[3].fetch_add(__rdtsc() - kfT1, std::memory_order_relaxed);\n        st.queuedBytes += d.size();",
     "        --st.idleWaiters;\n        if (__rdtsc() - kfT1 > 20000ull) g_gsqBlocked.fetch_add(1, std::memory_order_relaxed); // PROBE-GQ: blocked for more than ~5 us\n"
     "        g_waitTicks[3].fetch_add(__rdtsc() - kfT1, std::memory_order_relaxed);\n        st.queuedBytes += d.size();"),
    ("// PERF-GB: batch mode for the calling thread",
     'extern "C" void ps2_gs_async_stats(uint64_t *out) // PROBE-GQ: busy, idle ticks, blocked count, peak bytes, packets (all reset on read)\n'
     "{\n    out[0] = g_gsqBusy.exchange(0);\n    out[1] = g_gsqIdle.exchange(0);\n    out[2] = g_gsqBlocked.exchange(0);\n    out[3] = g_gsqPeak.exchange(0);\n    out[4] = g_gsqPkts.exchange(0);\n}\n\n"
     "// PERF-GB: batch mode for the calling thread"),
])
edit(base + "ps2_memory.cpp", [
    ('extern "C" uint32_t probe_getNewestDistinctFn(); // PROBE-FS',
     'extern "C" void ps2_gs_async_stats(uint64_t *out); // PROBE-GQ\nextern "C" uint32_t probe_getNewestDistinctFn(); // PROBE-FS'),
    ("            { // PROBE-FS: the heaviest waiting call sites of this window",
     '            { // PROBE-GQ\n                uint64_t g[5];\n                ps2_gs_async_stats(g);\n'
     '                ps2xSafeLog("[gsq] gs_busy_ms=%.0f gs_idle_ms=%.0f producer_blocks=%llu peak_queue_kb=%.0f packets=%llu' + BS + 'n", static_cast<double>(g[0]) / tpm, static_cast<double>(g[1]) / tpm,\n'
     '                            (unsigned long long)g[2], static_cast<double>(g[3]) / 1024.0, (unsigned long long)g[4]);\n            }\n'
     "            { // PROBE-FS: the heaviest waiting call sites of this window"),
])
print("ok")
