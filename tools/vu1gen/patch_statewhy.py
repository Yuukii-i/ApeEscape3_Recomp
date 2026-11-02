"""One-shot patch (PROBE-STATE): split the 'state' slow-pair cause into branchPending / ebit / haltAfterDelaySlot / budget, printed in the replay summary."""
base = "C:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/vu/"


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


BS = chr(92)
edit(base + "generated/vu1_native_dispatch.cpp", [
    ("uint64_t s_cause[6] = {};", "uint64_t s_cause[10] = {}; // [6..9] state split: branchPending, ebit, haltAfterDelaySlot, budget"),
    ("        else\n            ++s_cause[2];\n        c.hashValid = false;",
     "        else\n        {\n            ++s_cause[2];\n            if (vu.m_state.branchPending) ++s_cause[6];\n            else if (vu.m_state.ebit) ++s_cause[7];\n            else if (vu.m_state.haltAfterDelaySlot) ++s_cause[8];\n            else ++s_cause[9];\n        }\n        c.hashValid = false;"),
])
edit(base + "ps2_vu1_core.cpp", [
    ('                    static const char *const nm[3] = {"noStart", "miss", "declined"};',
     '                    std::fprintf(out, "state split: branchPending=%llu ebit=%llu halt=%llu budget=%llu' + BS + 'n", (unsigned long long)ca[6], (unsigned long long)ca[7], (unsigned long long)ca[8], (unsigned long long)ca[9]);\n'
     '                    static const char *const nm[3] = {"noStart", "miss", "declined"};'),
])
print("ok")
