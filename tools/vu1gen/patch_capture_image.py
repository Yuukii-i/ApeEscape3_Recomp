"""One-shot patch (PERF-VAR): PS2X_VU1_CORPUS=<file> (capture and replay) and PS2X_VU1_CAPTURE_IMAGE=<hex image hash> (capture only runs of that microcode image)."""
p = "C:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/vu/ps2_vu1_core.cpp"
t = open(p, encoding="utf-8", newline="").read()
crlf = "\r\n" in t
if crlf:
    t = t.replace("\r\n", "\n")


def rep(a, b):
    global t
    assert t.count(a) == 1, (t.count(a), a[:80])
    t = t.replace(a, b)


rep('s_capF = std::fopen("logs/vu1corpus.bin", "wb");', 's_capF = std::fopen(corpusPath(), "wb");')
rep('std::fopen("logs/vu1corpus.bin", "rb")', 'std::fopen(corpusPath(), "rb")')
rep("static bool capOn() {",
    'static const char *corpusPath() { const char *e = std::getenv("PS2X_VU1_CORPUS"); return (e && e[0]) ? e : "logs/vu1corpus.bin"; } // PERF-VAR\n'
    "static bool capOn() {")
rep("s_capKept < capMaxRecords() && vuCode == memory->getVU1Code()) // PROBE-CAPTURE",
    "s_capKept < capMaxRecords() && vuCode == memory->getVU1Code() && capImageOk()) // PROBE-CAPTURE")
rep("static uint32_t capMaxRecords() {",
    'static bool capImageOk() { static const char *e = std::getenv("PS2X_VU1_CAPTURE_IMAGE"); static const uint64_t want = e ? std::strtoull(e, nullptr, 16) : 0ull; return !e || s_hcCurHash == want; } // PERF-VAR\n'
    "static uint32_t capMaxRecords() {")
if crlf:
    t = t.replace("\n", "\r\n")
open(p, "w", encoding="utf-8", newline="").write(t)
print("ok")
