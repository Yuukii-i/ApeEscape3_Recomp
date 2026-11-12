"""One-shot patch (PERF-FZ, v2): zero-result lanes are resolved inside the existing slow branch of fmacR (before the out-of-line double classification),
so the common fast path is unchanged. Valid when every out-of-window destination lane is exactly +-0 with a certainly-zero exact result (add/sub: always;
mul: an operand lane is zero). madd/msub keep the full slow path."""
p = "C:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/vu/vu1_hot_ops.h"
t = open(p, encoding="utf-8", newline="").read()
crlf = "\r\n" in t
if crlf:
    t = t.replace("\r\n", "\n")
a = '''        else
        {
            // PERF-CS: the double-precision classification runs out of line, so the fast path stays contiguous in the instruction cache
            const FmacSlow sl = fmacSlow<KIND, DEST>(a4, b4, ac4, val);
            vb = sl.vb;
            mac = sl.mac;
            status4 = sl.status4;
            extra = sl.extra;
        }'''
assert t.count(a) == 1, t.count(a)
b = '''        else
        {
            uint32_t zl = 0u; // PERF-FZ: out-of-window lanes whose float result is exactly +-0 and whose exact result is certainly zero
            if constexpr (!madd)
            {
                const uint32_t zv = static_cast<uint32_t>(_mm_movemask_ps(_mm_cmpeq_ps(val, _mm_setzero_ps())));
                uint32_t g = 0xFu;
                if constexpr (KIND == 4)
                    g = static_cast<uint32_t>(_mm_movemask_ps(_mm_cmpeq_ps(a4, _mm_setzero_ps()))) |
                        static_cast<uint32_t>(_mm_movemask_ps(_mm_cmpeq_ps(b4, _mm_setzero_ps())));
                zl = zv & g & bad & D4;
            }
            if (!madd && ((bad & D4) & ~zl) == 0u)
            {
                const uint32_t s = static_cast<uint32_t>(_mm_movemask_ps(val)) & D4;
                mac = (rev4(s) << 4) | rev4(zl);
                status4 = (s ? 2u : 0u) | (zl ? 1u : 0u);
            }
            else
            {
                // PERF-CS: the double-precision classification runs out of line, so the fast path stays contiguous in the instruction cache
                const FmacSlow sl = fmacSlow<KIND, DEST>(a4, b4, ac4, val);
                vb = sl.vb;
                mac = sl.mac;
                status4 = sl.status4;
                extra = sl.extra;
            }
        }'''
t = t.replace(a, b)
if crlf:
    t = t.replace("\n", "\r\n")
open(p, "w", encoding="utf-8", newline="").write(t)
print("ok")
