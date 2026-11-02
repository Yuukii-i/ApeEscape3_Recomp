"""One-shot patch (PERF-CL): vuhot::clip computes the six comparisons with two SSE compares + movemask instead of six scalar compare/branch pairs."""
p = "C:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/vu/vu1_hot_ops.h"
t = open(p, encoding="utf-8", newline="").read()
crlf = "\r\n" in t
if crlf:
    t = t.replace("\r\n", "\n")
i = t.index("        const auto exceeds = [limit](float value, uint32_t signMask)")
j = t.index("        v.m_workingClip = ((v.m_workingClip << 6)")
new = '''        // PERF-CL: flag bit 2k = +component k exceeds, bit 2k+1 = -component k exceeds (signed compare of the sign-folded integer value)
        const __m128i vi = _mm_castps_si128(_mm_loadu_ps(v.m_state.vf[fs]));
        const __m128i lim = _mm_set1_epi32(limit);
        const uint32_t pm = static_cast<uint32_t>(_mm_movemask_ps(_mm_castsi128_ps(_mm_cmpgt_epi32(vi, lim)))) & 7u;
        const uint32_t nm = static_cast<uint32_t>(_mm_movemask_ps(_mm_castsi128_ps(_mm_cmpgt_epi32(_mm_xor_si128(vi, _mm_set1_epi32(static_cast<int>(0x80000000u))), lim)))) & 7u;
        const auto spread = [](uint32_t b) { return (b & 1u) | ((b & 2u) << 1) | ((b & 4u) << 2); };
        const uint32_t flags = spread(pm) | (spread(nm) << 1);
'''
t = t[:i] + new + t[j:]
if crlf:
    t = t.replace("\n", "\r\n")
open(p, "w", encoding="utf-8", newline="").write(t)
print("ok")
