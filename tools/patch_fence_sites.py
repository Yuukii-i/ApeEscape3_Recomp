"""One-shot patch (PROBE-FS): attribute VIF1 fence waits (EE thread) to call sites: newest distinct guest function, current executing guest function, host return address."""
p = "C:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/ps2_memory.cpp"
BS = chr(92)
t = open(p, encoding="utf-8", newline="").read()
crlf = "\r\n" in t
if crlf:
    t = t.replace("\r\n", "\n")


def rep(a, b):
    global t
    assert t.count(a) == 1, (t.count(a), a[:80])
    t = t.replace(a, b)


rep('extern "C" void ps2_vif1_fence()\n{\n    if (!vif1AsyncEnabled() || t_onVif1Worker)\n        return;\n',
    '''extern "C" uint32_t probe_getNewestDistinctFn(); // PROBE-FS
extern thread_local uint32_t g_currentExecutingFunction;
struct FenceSite { uint32_t fn, cur; uintptr_t ra; uint64_t ticks, n; };
static FenceSite s_fenceSites[24]; // PROBE-FS: EE thread only (the worker returns before the wait)
extern "C" void ps2_vif1_fence()
{
    if (!vif1AsyncEnabled() || t_onVif1Worker)
        return;
''')
rep('''        g_waitTicks[0].fetch_add(__rdtsc() - fT0, std::memory_order_relaxed);
        g_waitTicks[5].fetch_add(1, std::memory_order_relaxed);
    }
    if (g_vif1ApplyVpuStat)''', '''        g_waitTicks[0].fetch_add(__rdtsc() - fT0, std::memory_order_relaxed);
        g_waitTicks[5].fetch_add(1, std::memory_order_relaxed);
        { // PROBE-FS
            const uint32_t fn = probe_getNewestDistinctFn(), cur = g_currentExecutingFunction;
            const uintptr_t ra = reinterpret_cast<uintptr_t>(_ReturnAddress());
            FenceSite *slot = nullptr;
            for (FenceSite &s : s_fenceSites)
                if (s.n && s.fn == fn && s.cur == cur && s.ra == ra) { slot = &s; break; }
            if (!slot)
                for (FenceSite &s : s_fenceSites)
                    if (!s.n) { slot = &s; s.fn = fn; s.cur = cur; s.ra = ra; break; }
            if (slot) { slot->ticks += __rdtsc() - fT0; ++slot->n; }
        }
    }
    if (g_vif1ApplyVpuStat)''')
rep('''            s_t0 = now;
            s_tsc0 = tsc;
''', '''            { // PROBE-FS: the heaviest waiting call sites of this window
                for (int pass = 0; pass < 4; ++pass)
                {
                    FenceSite *best = nullptr;
                    for (FenceSite &s : s_fenceSites)
                        if (s.n && (!best || s.ticks > best->ticks)) best = &s;
                    if (!best) break;
                    ps2xSafeLog("[fsite] newestFn=%08X curFn=%08X ra=%p waits=%llu ms=%.1f''' + BS + '''n", best->fn, best->cur, reinterpret_cast<void *>(best->ra),
                                (unsigned long long)best->n, static_cast<double>(best->ticks) / tpm);
                    best->n = 0; best->ticks = 0;
                }
                for (FenceSite &s : s_fenceSites) { s.n = 0; s.ticks = 0; }
            }
            s_t0 = now;
            s_tsc0 = tsc;
''')
if crlf:
    t = t.replace("\n", "\r\n")
open(p, "w", encoding="utf-8", newline="").write(t)
print("ok")
