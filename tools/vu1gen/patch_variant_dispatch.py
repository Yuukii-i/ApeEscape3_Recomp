"""One-shot patch (PERF-VAR): native executors/hot blocks/kernels for microcode images that differ from the main image in a few pairs.
Applied 2026-11-01; kept for the record, do not rerun."""
base = "C:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/vu/"
NL = chr(92) + "n"  # the two characters backslash-n inside C string literals


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


BLOCK = '''// PERF-VAR: other microcode images (same program family, a few dozen pairs differ) reuse the main image's executors, hot blocks and kernels wherever
// their pair + usage record is identical (tools/vu1gen/variant_masks.py); every other pc falls back to the exact interpreter (return 2).
#include "vu1_variants.inc"
namespace
{
const uint8_t *s_same = nullptr;     // null = main image (everything allowed)
bool s_hotOk[2048];                  // hot block starting at this pair is usable (all pairs of its span are identical)
bool s_kOk[3] = {true, true, true};  // kernels: vertex (2440..25B8), copy (0C80..0CB8), full/loop (1FE0..243F)
bool varRange(uint32_t lo, uint32_t hiIncl)
{
    for (uint32_t pc = lo; pc <= hiIncl; pc += 8u)
        if (!s_same[pc >> 3])
            return false;
    return true;
}
} // namespace
void vu1NativeSelectImage(uint64_t hash)
{
    s_same = nullptr;
    for (uint32_t i = 0; i < kVu1VariantCount; ++i)
        if (kVu1Variants[i].hash == hash)
            s_same = kVu1Variants[i].same;
    s_kOk[0] = s_kOk[1] = s_kOk[2] = true;
    if (!s_same)
        return;
    for (uint32_t i = 0; i < 2048u; ++i)
    {
        bool ok = true;
        if (kVu1HotStart[i])
        {
            const uint32_t n = (kVu1HotSpan[i] ? kVu1HotSpan[i] : 1u) + 1u; // +1 pair of margin
            for (uint32_t k = 0; k < n && ok; ++k)
                ok = (i + k) < 2048u && s_same[i + k];
        }
        s_hotOk[i] = ok;
    }
    s_kOk[0] = varRange(0x2440u, 0x25B8u);
    s_kOk[1] = varRange(0x0C80u, 0x0CB8u);
    s_kOk[2] = varRange(0x1FE0u, 0x2438u);
    std::printf("[probe] vu1 variant image %016llx: same pairs %u, hot starts usable %u, kernels vertex=%d copy=%d full=%d@@NL",
                (unsigned long long)hash, (unsigned)std::count(s_same, s_same + 2048, uint8_t(1)),
                (unsigned)std::count(s_hotOk, s_hotOk + 2048, true), (int)s_kOk[0], (int)s_kOk[1], (int)s_kOk[2]);
}
bool vu1NativeSupportsImage(uint64_t hash)
{
    if (hash == kVu1NativeMainHash)
        return true;
    for (uint32_t i = 0; i < kVu1VariantCount; ++i)
        if (kVu1Variants[i].hash == hash)
            return true;
    return false;
}

int vu1NativeRun(VU1Interpreter &vu, VuNativeCtx &c)
{'''.replace("@@NL", NL)

edit(base + "generated/vu1_native_dispatch.cpp", [
    ("int vu1NativeRun(VU1Interpreter &vu, VuNativeCtx &c)\n{", BLOCK),
    ("if (kVu1HotStart[pc >> 3] && (s_xgHot || !vu.m_xgkick.active) &&",
     "if (kVu1HotStart[pc >> 3] && (!s_same || s_hotOk[pc >> 3]) && (s_xgHot || !vu.m_xgkick.active) &&"),
    ("if (s_lbOn && pc == 0x2440u && c.nextHash == kHashVertEntry &&", "if (s_lbOn && s_kOk[0] && pc == 0x2440u && c.nextHash == kHashVertEntry &&"),
    ("if (s_lbOn && pc == 0x0C80u && c.nextHash == kHashCopyEntry &&", "if (s_lbOn && s_kOk[1] && pc == 0x0C80u && c.nextHash == kHashCopyEntry &&"),
    ("if (s_lbOn && pc == 0x1FE0u && c.nextHash == kLbEntryHash &&", "if (s_lbOn && s_kOk[2] && pc == 0x1FE0u && c.nextHash == kLbEntryHash &&"),
    ("if (s_lbOn && pc == 0x20F8u && c.nextHash == kLbLoopHash &&", "if (s_lbOn && s_kOk[2] && pc == 0x20F8u && c.nextHash == kLbLoopHash &&"),
    ("        const StepFn fn = kStep[pc >> 3];\n        if (!fn)\n            return 2;",
     "        const StepFn fn = kStep[pc >> 3];\n        if (!fn || (s_same && !s_same[pc >> 3]))\n            return 2;"),
])
edit(base + "ps2_vu1_core.cpp", [
    ("        if (m_unit == Unit::VU1)\n            s_hcCurHash = h;\n",
     "        if (m_unit == Unit::VU1)\n        {\n            s_hcCurHash = h;\n            vu1NativeSelectImage(h); // PERF-VAR\n        }\n"),
    ("static uint64_t s_hcCurHash = 0; // PROBE-HC",
     "void vu1NativeSelectImage(uint64_t hash); // PERF-VAR: generated/vu1_native_dispatch.cpp\nbool vu1NativeSupportsImage(uint64_t hash);\nstatic uint64_t s_hcCurHash = 0; // PROBE-HC"),
    ("(s_hcCurHash == kVu1NativeMainHash && codeSize == 0x4000u)", "(vu1NativeSupportsImage(s_hcCurHash) && codeSize == 0x4000u)"),
])
print("ok")
