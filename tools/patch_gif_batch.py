"""One-shot patch (PERF-GB): the VIF1 worker hands GIF packets to the async GS queue once per job instead of once per packet."""
base = "C:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/"


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
    # state + flush, placed after gsAsync()/gsAsyncEnabled() so the helpers see GsAsyncState
    ("void gsAsyncWorker()\n{",
     '''// PERF-GB: while the calling thread is in batch mode (the VIF1 worker, around one job) async GIF packets are collected thread-locally and handed to the queue
// under ONE lock at the end of the job (was a lock + possible notify + pool lock per XGKICK). Order is unchanged: single producer, FIFO queue.
thread_local bool t_gsBatch = false;
thread_local std::vector<std::vector<uint8_t>> t_gsPending;
thread_local size_t t_gsPendingBytes = 0;
std::atomic<bool> s_gsAsyncStarted{false};

void gsFlushPending()
{
    if (t_gsPending.empty())
        return;
    GsAsyncState &st = gsAsync();
    std::unique_lock<std::mutex> lock(st.m);
    for (auto &d : t_gsPending)
    {
        const uint64_t kfT1 = __rdtsc(); // PROBE-KF
        ++st.idleWaiters;
        st.cvIdle.wait(lock, [&] { return st.queuedBytes < kGsAsyncMaxBytes; }); // backpressure
        --st.idleWaiters;
        g_waitTicks[3].fetch_add(__rdtsc() - kfT1, std::memory_order_relaxed);
        st.queuedBytes += d.size();
        ++st.enqueuedPkts;
        st.q.push_back(std::move(d));
    }
    if (st.workerWaiting)
        st.cvWork.notify_one();
    t_gsPending.clear();
    t_gsPendingBytes = 0;
}

void gsAsyncWorker()
{'''),
    # fence / ticket waits on a batching thread must flush its own packets first
    ("extern \"C\" void ps2_gs_async_fence()\n{\n    if (!gsAsyncEnabled())\n        return;\n",
     "extern \"C\" void ps2_gs_async_fence()\n{\n    if (!gsAsyncEnabled())\n        return;\n    gsFlushPending(); // PERF-GB\n"),
    ("extern \"C\" void ps2_gs_async_wait_ticket(uint64_t ticket)\n{\n    if (!ticket)\n        return;\n",
     "extern \"C\" void ps2_gs_async_wait_ticket(uint64_t ticket)\n{\n    if (!ticket)\n        return;\n    gsFlushPending(); // PERF-GB\n"),
    # API
    ("// PERF-JF: ticket = number of packets handed to the async worker so far",
     '''// PERF-GB: batch mode for the calling thread (VIF1 worker, around one job); turning it off flushes.
extern "C" void ps2_gs_async_batch(bool on)
{
    if (!gsAsyncEnabled())
        return;
    if (!on)
        gsFlushPending();
    t_gsBatch = on;
}

// PERF-JF: ticket = number of packets handed to the async worker so far'''),
    # drain: batch branch
    ("    if (gsAsyncEnabled())\n    {\n        GsAsyncState &st = gsAsync();\n        std::unique_lock<std::mutex> lock(st.m);\n        if (!st.started)",
     '''    if (gsAsyncEnabled() && t_gsBatch && s_gsAsyncStarted.load(std::memory_order_acquire)) // PERF-GB
    {
        for (size_t i = 0; i < m_queue.size(); ++i)
        {
            auto &pkt = m_queue[i];
            if (pkt.data.empty())
                continue;
            t_gsPendingBytes += pkt.data.size();
            t_gsPending.push_back(std::move(pkt.data));
        }
        m_queue.clear();
        if (t_gsPendingBytes >= (1u << 20))
            gsFlushPending();
        return;
    }

    if (gsAsyncEnabled())
    {
        GsAsyncState &st = gsAsync();
        std::unique_lock<std::mutex> lock(st.m);
        if (!st.started)'''),
    ("            st.fn = m_processFn;\n            std::thread(gsAsyncWorker).detach();\n",
     "            st.fn = m_processFn;\n            std::thread(gsAsyncWorker).detach();\n            s_gsAsyncStarted.store(true, std::memory_order_release); // PERF-GB\n"),
])
edit(base + "ps2_memory.cpp", [
    ("static void vif1Worker()\n{",
     'extern "C" void ps2_gs_async_batch(bool on); // PERF-GB: gs/ps2_gif_arbiter.cpp\nstatic void vif1Worker()\n{'),
    ("        s_vif1Process(job.data.data(), static_cast<uint32_t>(job.data.size()));\n",
     "        ps2_gs_async_batch(true); // PERF-GB\n        s_vif1Process(job.data.data(), static_cast<uint32_t>(job.data.size()));\n        ps2_gs_async_batch(false); // PERF-GB: hand the job's GIF packets to the GS queue under one lock\n"),
])
print("ok")
