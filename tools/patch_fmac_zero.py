"""One-shot patch (PERF-FZ): fmacR fast path also accepts destination lanes whose float result is exactly +-0 when the exact result is certainly zero
(add/sub: always; mul: an operand lane is zero). Those lanes used to take the out-of-line double-precision classification (fmacSlow, ~10% of native time in the replay)."""
p = "C:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/vu/vu1_hot_ops.h"
t = open(p, encoding="utf-8", newline="").read()
crlf = "\r\n" in t
if crlf:
    t = t.replace("\r\n", "\n")


def rep(a, b):
    global t
    assert t.count(a) == 1, (t.count(a), a[:80])
    t = t.replace(a, b)


rep('''        uint32_t mac, status4, extra = 0u;
        __m128i vb = _mm_castps_si128(val);
        if ((bad & D4) == 0u)
        {
            const uint32_t s = static_cast<uint32_t>(_mm_movemask_ps(val)) & D4;
            mac = rev4(s) << 4;
            status4 = s ? 2u : 0u;''', '''        uint32_t mac, status4, extra = 0u;
        __m128i vb = _mm_castps_si128(val);
        uint32_t zl = 0u; // PERF-FZ: lanes whose result is exactly +-0 (exact result certainly zero): flags zero (+ sign), value = the float result
        if constexpr (!madd)
        {
            if ((bad & D4) != 0u)
            {
                const uint32_t zv = static_cast<uint32_t>(_mm_movemask_ps(_mm_cmpeq_ps(val, _mm_setzero_ps())));
                uint32_t g = 0xFu;
                if constexpr (KIND == 4)
                    g = static_cast<uint32_t>(_mm_movemask_ps(_mm_cmpeq_ps(a4, _mm_setzero_ps()))) |
                        static_cast<uint32_t>(_mm_movemask_ps(_mm_cmpeq_ps(b4, _mm_setzero_ps())));
                zl = zv & g & bad & D4;
                bad &= ~zl;
            }
        }
        if ((bad & D4) == 0u)
        {
            const uint32_t s = static_cast<uint32_t>(_mm_movemask_ps(val)) & D4;
            mac = (rev4(s) << 4) | rev4(zl);
            status4 = (s ? 2u : 0u) | (zl ? 1u : 0u);''')
if crlf:
    t = t.replace("\n", "\r\n")
open(p, "w", encoding="utf-8", newline="").write(t)
print("ok")
