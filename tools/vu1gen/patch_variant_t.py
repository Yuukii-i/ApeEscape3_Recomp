"""One-shot patch (PERF-VAR): image-specific executors and hot blocks for the pcs where image 4020410124328442 differs from main.
Applied 2026-11-01; kept for the record, do not rerun."""
base = "C:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/"


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


edit(base + "src/lib/vu/generated/vu1_native_dispatch.cpp", [
    ('#include "vu1_variants.inc"\n',
     '#include "vu1_variants.inc"\n'
     'extern int (*const kVu1Step_t4020[2048])(VU1Interpreter &, VuNativeCtx &); // generated/vu1_native_exec_t4020.cpp: executors for the pairs where image 4020... differs from main\n'
     'extern const bool kVu1HotStart_t4020[2048];                                  // generated/vu1_hot_blocks_t4020.cpp\n'
     'VuHotFn vu1HotLookup_t4020(uint32_t pc, uint64_t entryHash);\n'
     'VuHotFn vu1HotLookupXg_t4020(uint32_t pc, uint64_t entryHash);\n'),
    ('bool s_kOk[3] = {true, true, true};',
     'bool s_isT4020 = false;                                       // the image with its own executors / hot blocks for the differing pairs\n'
     'HotSlot s_hotSlotT[2048] = {}, s_hotSlotTX[2048] = {};\n'
     'bool s_kOk[3] = {true, true, true};'),
    ('void vu1NativeSelectImage(uint64_t hash)\n{\n    s_same = nullptr;\n',
     'void vu1NativeSelectImage(uint64_t hash)\n{\n    s_same = nullptr;\n    s_isT4020 = (hash == 0x4020410124328442ull);\n'),
    ('        if (kVu1HotStart[pc >> 3] && (!s_same || s_hotOk[pc >> 3]) && (s_xgHot',
     '        const bool useT = s_isT4020 && !s_same[pc >> 3] && kVu1HotStart_t4020[pc >> 3]; // PERF-VAR: pc where this image differs from main\n'
     '        if ((useT || (kVu1HotStart[pc >> 3] && (!s_same || s_hotOk[pc >> 3]))) && (s_xgHot'),
    ('            HotSlot &hs = (xa ? s_hotSlotX : s_hotSlot)[pc >> 3];',
     '            HotSlot &hs = (useT ? (xa ? s_hotSlotTX : s_hotSlotT) : (xa ? s_hotSlotX : s_hotSlot))[pc >> 3];'),
    ('                hf = xa ? vu1HotLookupXg(pc, c.nextHash) : vu1HotLookup(pc, c.nextHash);',
     '                hf = useT ? (xa ? vu1HotLookupXg_t4020(pc, c.nextHash) : vu1HotLookup_t4020(pc, c.nextHash))\n'
     '                          : (xa ? vu1HotLookupXg(pc, c.nextHash) : vu1HotLookup(pc, c.nextHash));'),
    ('        const StepFn fn = kStep[pc >> 3];\n        if (!fn || (s_same && !s_same[pc >> 3]))\n            return 2;',
     '        StepFn fn = kStep[pc >> 3];\n        if (s_same && !s_same[pc >> 3])\n            fn = s_isT4020 ? kVu1Step_t4020[pc >> 3] : nullptr; // PERF-VAR\n        if (!fn)\n            return 2;'),
])
edit(base + "CMakeLists.txt", [
    ('    src/lib/vu/generated/vu1_hot_blocks.cpp\n',
     '    src/lib/vu/generated/vu1_hot_blocks.cpp\n    src/lib/vu/generated/vu1_hot_blocks_t4020.cpp\n    src/lib/vu/generated/vu1_native_exec_t4020.cpp\n'),
])
print("ok")
