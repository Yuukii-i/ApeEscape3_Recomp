"""One-shot patch (PROBE-GQ2): vertexKick total / buildDrawBatch / Submit ticks, wrapper lock wait ticks, Present hold ticks -> [gsq2] line."""
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
    ("    if (drawing && m_backend)\n    {\n        GSPrimitiveBatch batch = buildDrawBatch(needed);\n        updatePreferredDisplaySourceForDraw(batch);\n",
     "    if (drawing && m_backend)\n    {\n        const uint64_t gqT0 = __rdtsc(); // PROBE-GQ2\n        GSPrimitiveBatch batch = buildDrawBatch(needed);\n        updatePreferredDisplaySourceForDraw(batch);\n"
     "        g_gqBuild.fetch_add(__rdtsc() - gqT0, std::memory_order_relaxed);\n"),
    ("            m_backend->Submit(batch);\n        }\n\n        recordDrawDebugEventUnlocked(needed);",
     "            const uint64_t gqS0 = __rdtsc(); // PROBE-GQ2\n            m_backend->Submit(batch);\n            g_gqSubmit.fetch_add(__rdtsc() - gqS0, std::memory_order_relaxed);\n            g_gqDraws.fetch_add(1, std::memory_order_relaxed);\n        }\n\n        recordDrawDebugEventUnlocked(needed);"),
])
print("frontend ok")
