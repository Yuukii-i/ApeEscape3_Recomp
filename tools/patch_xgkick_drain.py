"""One-shot patch (PERF-XD): flushPipelines finishes the last XGKICK transfer in closed form instead of one progressXgkick() call per cycle.
At that point no VU code runs, so VU memory is static: walk the GIF tags, copy the extent with memcpy, add the exact cycle count (the first quadword needs
2-credit cycles, every later one 2) and finish. Anything unusual (reserved format, oversize, unaligned or non power-of-two memory) falls back to the old loop."""
p = "C:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/vu/ps2_vu1_core.cpp"
t = open(p, encoding="utf-8", newline="").read()
crlf = "\r\n" in t
if crlf:
    t = t.replace("\r\n", "\n")
a = '''    while (m_xgkick.active && m_activeVuData && m_activeVuDataSize != 0u)
    {
        ++m_cycle;
        m_state.cycles = m_cycle;
        progressXgkick();
    }
    if (s_vuImmFlags && !s_vfyRef) // PERF-HV'''
assert t.count(a) == 1, t.count(a)
b = '''    static const bool s_xgDrainOn = []() { const char *e = std::getenv("PS2X_VU1_XGDRAIN"); return !(e && e[0] == '0'); }(); // PERF-XD: =0 restores the per-cycle loop
    if (s_xgDrainOn && m_xgkick.active && m_activeVuData && m_activeVuDataSize != 0u && !s_eiCurRunActive)
    {
        // PERF-XD: closed-form drain of the final transfer (see tools/patch_xgkick_drain.py)
        const uint32_t dsz = m_activeVuDataSize;
        bool ok = (dsz & (dsz - 1u)) == 0u && (m_xgkick.sourceAddress & 15u) == 0u && m_xgkick.cycleCredit < 2u;
        const uint32_t cb0 = m_xgkick.copiedBytes;
        uint32_t cb = cb0, tagEnd = m_xgkick.currentTagEnd, total = m_xgkick.totalBytes;
        bool eop = m_xgkick.currentTagEop, finished = false;
        uint32_t credit = m_xgkick.cycleCredit;
        uint64_t cycles = 0;
        const auto take = [&](uint32_t n) // n quadwords copied back to back
        {
            if (n == 0u)
                return;
            cycles += (2u - credit) + 2ull * (n - 1u);
            credit = 0u;
        };
        while (ok && !finished)
        {
            if (tagEnd == 0u)
            {
                if (cb > XgkickPipeline::kBufferSize - 16u) { ok = false; break; }
                const uint32_t qoff = cb;
                take(1u);
                cb += 16u;
                uint64_t tagLo = 0;
                std::memcpy(&tagLo, m_activeVuData + ((m_xgkick.sourceAddress + qoff) & (dsz - 1u)), sizeof(tagLo));
                const uint32_t nloop = static_cast<uint32_t>(tagLo & 0x7FFFu);
                const uint32_t format = static_cast<uint32_t>((tagLo >> 58) & 0x3u);
                uint32_t nreg = static_cast<uint32_t>((tagLo >> 60) & 0xFu);
                if (nreg == 0u)
                    nreg = 16u;
                uint64_t tagBytes = 16u;
                if (format == 0u)
                    tagBytes += static_cast<uint64_t>(nloop) * nreg * 16u;
                else if (format == 1u)
                    tagBytes += ((static_cast<uint64_t>(nloop) * nreg + 1u) & ~1ull) * 8u;
                else if (format == 2u)
                    tagBytes += static_cast<uint64_t>(nloop) * 16u;
                else { ok = false; break; }
                if (tagBytes > XgkickPipeline::kBufferSize - qoff || (tagBytes & 15u) != 0u) { ok = false; break; }
                tagEnd = qoff + static_cast<uint32_t>(tagBytes);
                eop = ((tagLo >> 15) & 1u) != 0u;
                if (eop)
                    total = tagEnd;
            }
            if (cb < tagEnd)
            {
                take((tagEnd - cb) / 16u);
                cb = tagEnd;
            }
            if (eop)
                finished = true;
            else
            {
                tagEnd = 0u;
                eop = false;
            }
        }
        if (ok && finished)
        {
            uint32_t done = cb0;
            while (done < cb)
            {
                const uint32_t s = (m_xgkick.sourceAddress + done) & (dsz - 1u);
                const uint32_t n = std::min<uint32_t>(cb - done, dsz - s);
                std::memcpy(m_xgkick.packet.data() + done, m_activeVuData + s, n);
                done += n;
            }
            m_cycle += cycles;
            m_state.cycles = m_cycle;
            m_xgkick.copiedBytes = cb;
            m_xgkick.currentTagEnd = tagEnd;
            m_xgkick.currentTagEop = eop;
            m_xgkick.totalBytes = total;
            m_xgkick.cycleCredit = credit;
            finishXgkick();
        }
    }
    while (m_xgkick.active && m_activeVuData && m_activeVuDataSize != 0u)
    {
        ++m_cycle;
        m_state.cycles = m_cycle;
        progressXgkick();
    }
    if (s_vuImmFlags && !s_vfyRef) // PERF-HV'''
t = t.replace(a, b)
if crlf:
    t = t.replace("\n", "\r\n")
open(p, "w", encoding="utf-8", newline="").write(t)
print("ok")
