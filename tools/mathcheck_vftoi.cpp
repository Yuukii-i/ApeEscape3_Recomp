// FIX-M2: standalone SSE check for saturating VFTOI expression
#include <cstdint>
#include <cstdio>
#include <emmintrin.h>

int main() {
    const float inputs[] = {
        1e20f,
        -1e20f,
        3.5f,
        -3.5f,
        2147483520.0f,
        2147483648.0f,
        0.0f,
    };
    const uint32_t expected[] = {
        0x7FFFFFFFu,
        0x80000000u,
        static_cast<uint32_t>(3),
        static_cast<uint32_t>(-3),
        0x7FFFFF80u,
        0x7FFFFFFFu,
        0u,
    };

    int failures = 0;
    constexpr int count = sizeof(inputs) / sizeof(inputs[0]);
    for (int i = 0; i < count; ++i) {
        __m128 src = _mm_set1_ps(inputs[i]);
        __m128i res_i = _mm_xor_si128(
            _mm_cvttps_epi32(src),
            _mm_castps_si128(_mm_cmpge_ps(src, _mm_set1_ps(2147483648.0f)))
        );
        uint32_t actual = static_cast<uint32_t>(_mm_cvtsi128_si32(res_i));
        bool ok = (actual == expected[i]);
        if (!ok) {
            ++failures;
        }
        std::printf("src=%g expected=0x%08X actual=0x%08X %s\n",
                    inputs[i], expected[i], actual, ok ? "OK" : "MISMATCH");
    }

    return failures == 0 ? 0 : 1;
}
