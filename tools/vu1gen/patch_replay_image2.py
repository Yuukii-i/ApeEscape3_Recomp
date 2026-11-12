"""One-shot patch (PERF-VAR): PS2X_VU1_REPLAY_IMAGE re-installs the wanted image before every replayed run (the EE thread keeps running and may upload other microcode)."""
p = "C:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/vu/ps2_vu1_core.cpp"
t = open(p, encoding="utf-8", newline="").read()
crlf = "\r\n" in t
if crlf:
    t = t.replace("\r\n", "\n")


def rep(a, b):
    global t
    assert t.count(a) == 1, (t.count(a), a[:80])
    t = t.replace(a, b)


rep('''        if (const char *ri = std::getenv("PS2X_VU1_REPLAY_IMAGE")) // PERF-VAR: replay another microcode image of the corpus (the live code is overwritten, the process exits afterwards)
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
''', '''        const char *const rpImageEnv = std::getenv("PS2X_VU1_REPLAY_IMAGE"); // PERF-VAR: replay another microcode image of the corpus: it is re-installed in the live code before every run
        const uint64_t rpWant = rpImageEnv ? std::strtoull(rpImageEnv, nullptr, 16) : 0ull;
        std::unordered_map<uint64_t, uint64_t> rpGenHash;
        if (rpImageEnv)
            for (const auto &kv : codeOff)
                rpGenHash[kv.first] = rpImageHash(kv.second);
''')
rep('''                    const auto it = codeOff.find(gen);
                    if (it == codeOff.end() ||''', '''                    const auto it = codeOff.find(gen);
                    if (rpImageEnv && it != codeOff.end() && rpGenHash[gen] == rpWant)
                    {
                        std::memcpy(const_cast<uint8_t *>(vuCode), file.data() + it->second, codeSize);
                        rebuildDecodedCodeCache(vuCode, codeSize, memory, memory->getVU1CodeGeneration());
                    }
                    if (it == codeOff.end() ||''')
if crlf:
    t = t.replace("\n", "\r\n")
open(p, "w", encoding="utf-8", newline="").write(t)
print("ok")
