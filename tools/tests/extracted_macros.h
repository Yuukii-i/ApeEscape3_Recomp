#pragma once
#include <immintrin.h>
#include <cstdint>

// PMFHL function implementations
inline __m128i ps2_pmfhl_lw(uint64_t hi, uint64_t lo, uint64_t hi1, uint64_t lo1)
{
    return _mm_set_epi32(
        static_cast<int32_t>(hi1 & 0xFFFFFFFFu),
        static_cast<int32_t>(lo1 & 0xFFFFFFFFu),
        static_cast<int32_t>(hi  & 0xFFFFFFFFu),
        static_cast<int32_t>(lo  & 0xFFFFFFFFu)
    );
}

inline __m128i ps2_pmfhl_uw(uint64_t hi, uint64_t lo, uint64_t hi1, uint64_t lo1)
{
    return _mm_set_epi32(
        static_cast<int32_t>(hi1 >> 32),
        static_cast<int32_t>(lo1 >> 32),
        static_cast<int32_t>(hi  >> 32),
        static_cast<int32_t>(lo  >> 32)
    );
}

inline __m128i ps2_pmfhl_slw(uint64_t hi, uint64_t lo, uint64_t hi1, uint64_t lo1)
{
    int64_t prod0 = static_cast<int64_t>((hi << 32) | (lo & 0xFFFFFFFFu));
    int64_t prod1 = static_cast<int64_t>((hi1 << 32) | (lo1 & 0xFFFFFFFFu));
    int32_t w0 = static_cast<int32_t>(prod0 >> 16);
    int32_t w1 = static_cast<int32_t>(prod0 >> 48);
    int32_t w2 = static_cast<int32_t>(prod1 >> 16);
    int32_t w3 = static_cast<int32_t>(prod1 >> 48);
    return _mm_set_epi32(w3, w2, w1, w0);
}

inline __m128i ps2_pmfhl_lh(uint64_t hi, uint64_t lo, uint64_t hi1, uint64_t lo1)
{
    return _mm_set_epi16(
        static_cast<int16_t>((hi1 >> 32) & 0xFFFFu),
        static_cast<int16_t>((lo1 >> 32) & 0xFFFFu),
        static_cast<int16_t>(hi1 & 0xFFFFu),
        static_cast<int16_t>(lo1 & 0xFFFFu),
        static_cast<int16_t>((hi >> 32) & 0xFFFFu),
        static_cast<int16_t>((lo >> 32) & 0xFFFFu),
        static_cast<int16_t>(hi & 0xFFFFu),
        static_cast<int16_t>(lo & 0xFFFFu)
    );
}

inline __m128i ps2_pmfhl_sh(uint64_t hi, uint64_t lo, uint64_t hi1, uint64_t lo1)
{
    return _mm_set_epi16(
        static_cast<int16_t>(hi1 >> 48),
        static_cast<int16_t>(lo1 >> 48),
        static_cast<int16_t>((hi1 >> 16) & 0xFFFFu),
        static_cast<int16_t>((lo1 >> 16) & 0xFFFFu),
        static_cast<int16_t>(hi >> 48),
        static_cast<int16_t>(lo >> 48),
        static_cast<int16_t>((hi >> 16) & 0xFFFFu),
        static_cast<int16_t>((lo >> 16) & 0xFFFFu)
    );
}

#define PS2_PMFHL_LW(hi, lo, hi1, lo1) ps2_pmfhl_lw((hi), (lo), (hi1), (lo1))
#define PS2_PMFHL_UW(hi, lo, hi1, lo1) ps2_pmfhl_uw((hi), (lo), (hi1), (lo1))
#define PS2_PMFHL_SLW(hi, lo, hi1, lo1) ps2_pmfhl_slw((hi), (lo), (hi1), (lo1))
#define PS2_PMFHL_LH(hi, lo, hi1, lo1) ps2_pmfhl_lh((hi), (lo), (hi1), (lo1))
#define PS2_PMFHL_SH(hi, lo, hi1, lo1) ps2_pmfhl_sh((hi), (lo), (hi1), (lo1))
