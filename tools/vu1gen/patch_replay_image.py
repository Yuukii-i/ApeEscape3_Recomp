"""One-shot patch (PERF-VAR): PS2X_VU1_REPLAY_IMAGE=<hex image hash> replays the corpus runs of that microcode image; the replay summary lists the images."""
p = "C:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/vu/ps2_vu1_core.cpp"
BS = chr(92)
t = open(p, encoding="utf-8", newline="").read()
crlf = "\r\n" in t
if crlf:
    t = t.replace("\r\n", "\n")
a = "        bool imageLoaded = false;\n        for (const auto &kv : codeOff)\n"
assert t.count(a) == 1
b = '''        const auto rpImageHash = [&](size_t off)
        {
            uint64_t h = 1469598103934665603ull;
            for (uint32_t i = 0; i < codeSize; ++i)
                h = (h ^ file[off + i]) * 1099511628211ull;
            return h;
        };
        if (const char *ri = std::getenv("PS2X_VU1_REPLAY_IMAGE")) // PERF-VAR: replay another microcode image of the corpus (the live code is overwritten, the process exits afterwards)
        {
            const uint64_t want = std::strtoull(ri, nullptr, 16);
            for (const auto &kv : codeOff)
                if (rpImageHash(kv.second) == want)
                {
                    std::memcpy(const_cast<uint8_t *>(vuCode), file.data() + kv.second, codeSize);
                    rebuildDecodedCodeCache(vuCode, codeSize, memory, kv.first);
                    break;
                }
        }
''' + a
t = t.replace(a, b)
a2 = '            std::fprintf(out, "records=%zu codeImages=%zu stateSize file=%u now=%zu' + BS + 'n", runsIdx.size(), codeOff.size(), stSize, sizeof(VU1State));' + "\n"
assert t.count(a2) == 1, t.count(a2)
b2 = a2 + '            for (const auto &kv : codeOff)\n                std::fprintf(out, "image gen=%llu hash=%016llx' + BS + 'n", (unsigned long long)kv.first, (unsigned long long)rpImageHash(kv.second));\n'
t = t.replace(a2, b2)
if crlf:
    t = t.replace("\n", "\r\n")
open(p, "w", encoding="utf-8", newline="").write(t)
print("ok")
