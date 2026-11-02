"""One-shot patch (PERF-SL): bounded lag for the per-frame sceGsSyncPath. With PS2X_SYNCPATH_ASYNC=1 the frame-sync call (return address 0x0051E290) waits until the
VIF1 worker has finished everything enqueued before the PREVIOUS frame sync (lag = PS2X_SYNCPATH_LAG frames, default 1) instead of not waiting at all."""
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


edit(base + "ps2_memory.cpp", [
    ("        std::atomic<bool> pending{false}; // queue non-empty or worker busy\n    };",
     "        std::atomic<bool> pending{false}; // queue non-empty or worker busy\n"
     "        uint64_t enqueuedJobs = 0, doneJobs = 0; // PERF-SL: job sequence numbers (guarded by m)\n"
     "        uint32_t lagWaiters = 0;                 // PERF-SL: EE threads waiting in ps2_vif1_sync_lag\n    };"),
    ("    st.queuedBytes += data.size();\n    job.data = std::move(data);\n    st.q.push_back(std::move(job));\n",
     "    st.queuedBytes += data.size();\n    job.data = std::move(data);\n    st.q.push_back(std::move(job));\n    ++st.enqueuedJobs; // PERF-SL\n"),
    ("            st.busy = false;\n            if (st.q.empty())\n            {\n                st.pending.store(false, std::memory_order_release);\n                st.cvIdle.notify_all();\n            }\n",
     "            st.busy = false;\n            ++st.doneJobs; // PERF-SL\n            if (st.q.empty())\n            {\n                st.pending.store(false, std::memory_order_release);\n                st.cvIdle.notify_all();\n            }\n"
     "            else if (st.lagWaiters != 0u)\n                st.cvIdle.notify_all();\n"),
    ('extern "C" bool ps2_vif1_on_worker() { return t_onVif1Worker; }\n',
     '''extern "C" bool ps2_vif1_on_worker() { return t_onVif1Worker; }
// PERF-SL: called by the per-frame sceGsSyncPath: remember how many jobs exist now and wait until the worker has finished the jobs that existed `lag` calls ago.
// lag=1: at most one frame of VU1/GIF work is in flight while the EE builds the next one (steady cadence, bounded input latency).
extern "C" void ps2_vif1_sync_lag(uint32_t lag)
{
    if (!vif1AsyncEnabled() || t_onVif1Worker)
        return;
    Vif1AsyncState &st = vifAsync();
    static std::deque<uint64_t> s_tickets; // EE thread only
    std::unique_lock<std::mutex> lock(st.m);
    s_tickets.push_back(st.enqueuedJobs);
    if (s_tickets.size() > lag)
    {
        const uint64_t want = s_tickets.front();
        s_tickets.pop_front();
        if (st.doneJobs < want)
        {
            const uint64_t fT0 = __rdtsc();
            ++st.lagWaiters;
            st.cvIdle.wait(lock, [&] { return st.doneJobs >= want; });
            --st.lagWaiters;
            g_waitTicks[0].fetch_add(__rdtsc() - fT0, std::memory_order_relaxed);
            g_waitTicks[5].fetch_add(1, std::memory_order_relaxed);
        }
    }
}
'''),
])
edit(base + "Kernel/Stubs/GS.cpp", [
    ("            if (s_syncPathAsync)\n            {\n                setReturnS32(ctx, 0);\n                return;\n            }\n",
     '''            if (s_syncPathAsync)
            {
                // PERF-SL: only the per-frame sync (called from the frame-swap routine, return address 0x0051E290) is overlapped, with a bounded lag; every other caller waits fully
                static const uint32_t s_lag = []() { const char *e = std::getenv("PS2X_SYNCPATH_LAG"); const unsigned long n = e ? std::strtoul(e, nullptr, 10) : 1ul; return static_cast<uint32_t>(n ? n : 1ul); }();
                if (getRegU32(ctx, 31) == 0x0051E290u)
                {
                    ps2_vif1_sync_lag(s_lag);
                    setReturnS32(ctx, 0);
                    return;
                }
            }
'''),
    ("    void sceGsSyncPath(uint8_t *rdram, R5900Context *ctx, PS2Runtime *runtime)\n    {",
     '    extern "C" void ps2_vif1_sync_lag(uint32_t lag); // PERF-SL: ps2_memory.cpp\n\n    void sceGsSyncPath(uint8_t *rdram, R5900Context *ctx, PS2Runtime *runtime)\n    {'),
])
print("ok")
