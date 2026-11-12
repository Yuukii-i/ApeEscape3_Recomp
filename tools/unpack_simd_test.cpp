#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdint>
#include <random>
#include <vector>
#include <algorithm>
#include <immintrin.h>
// PERF-UV: UNPACK writes for cl >= wl in one SIMD loop. Every destination lane is exactly one of decoded / constant (row, col) / protected
// (keeps the old VU data word), selected per write-cycle position by the masks the caller derives from the same act[][] table as the scalar loop.
namespace
{
    template <int VL, int VN, bool ZX>
    inline __m128i vifDecode(const uint8_t *p)
    {
        if constexpr (VL == 0)
        {
            if constexpr (VN == 0)
            {
                uint32_t s;
                std::memcpy(&s, p, 4);
                return _mm_set1_epi32(static_cast<int>(s));
            }
            else if constexpr (VN == 1)
                return _mm_loadl_epi64(reinterpret_cast<const __m128i *>(p));
            else if constexpr (VN == 2)
            {
                uint32_t w[3];
                std::memcpy(w, p, 12);
                return _mm_set_epi32(0, static_cast<int>(w[2]), static_cast<int>(w[1]), static_cast<int>(w[0]));
            }
            else
                return _mm_loadu_si128(reinterpret_cast<const __m128i *>(p));
        }
        else if constexpr (VL == 1)
        {
            if constexpr (VN == 0)
            {
                uint16_t r;
                std::memcpy(&r, p, 2);
                return _mm_set1_epi32(ZX ? static_cast<int>(r) : static_cast<int>(static_cast<int16_t>(r)));
            }
            else
            {
                uint64_t t = 0;
                std::memcpy(&t, p, VN == 1 ? 4 : (VN == 2 ? 6 : 8));
                const __m128i v = _mm_cvtsi64_si128(static_cast<long long>(t));
                return ZX ? _mm_cvtepu16_epi32(v) : _mm_cvtepi16_epi32(v);
            }
        }
        else
        {
            if constexpr (VN == 0)
                return _mm_set1_epi32(ZX ? static_cast<int>(p[0]) : static_cast<int>(static_cast<int8_t>(p[0])));
            else
            {
                uint32_t t = 0;
                std::memcpy(&t, p, VN == 1 ? 2 : (VN == 2 ? 3 : 4));
                const __m128i v = _mm_cvtsi32_si128(static_cast<int>(t));
                return ZX ? _mm_cvtepu8_epi32(v) : _mm_cvtepi8_epi32(v);
            }
        }
    }

    template <int VL, int VN, bool ZX>
    void vifUnpackLoop(uint8_t *vuData, const uint8_t *src, uint32_t count, uint32_t destVec, uint32_t cl, uint32_t wl, uint32_t bytesPerVector,
                       const __m128i *dm, const __m128i *cv, const __m128i *pm)
    {
        uint32_t cyclePos = 0;
        for (uint32_t i = 0; i < count; ++i)
        {
            const __m128i dec = vifDecode<VL, VN, ZX>(src);
            const uint32_t c = (cyclePos > 3u) ? 3u : cyclePos;
            __m128i *d = reinterpret_cast<__m128i *>(vuData) + destVec;
            const __m128i old = _mm_loadu_si128(d);
            _mm_storeu_si128(d, _mm_or_si128(_mm_or_si128(_mm_and_si128(dec, dm[c]), cv[c]), _mm_and_si128(old, pm[c])));
            src += bytesPerVector;
            ++cyclePos;
            ++destVec;
            if (cyclePos == wl)
            {
                cyclePos = 0;
                destVec += (cl - wl);
            }
        }
    }

    template <int VL, int VN>
    void vifUnpackZx(bool zx, uint8_t *vuData, const uint8_t *src, uint32_t count, uint32_t destVec, uint32_t cl, uint32_t wl, uint32_t bpv,
                     const __m128i *dm, const __m128i *cv, const __m128i *pm)
    {
        if (zx)
            vifUnpackLoop<VL, VN, true>(vuData, src, count, destVec, cl, wl, bpv, dm, cv, pm);
        else
            vifUnpackLoop<VL, VN, false>(vuData, src, count, destVec, cl, wl, bpv, dm, cv, pm);
    }

    template <int VL>
    void vifUnpackVn(uint32_t vn, bool zx, uint8_t *vuData, const uint8_t *src, uint32_t count, uint32_t destVec, uint32_t cl, uint32_t wl,
                     uint32_t bpv, const __m128i *dm, const __m128i *cv, const __m128i *pm)
    {
        switch (vn)
        {
        case 0: vifUnpackZx<VL, 0>(zx, vuData, src, count, destVec, cl, wl, bpv, dm, cv, pm); break;
        case 1: vifUnpackZx<VL, 1>(zx, vuData, src, count, destVec, cl, wl, bpv, dm, cv, pm); break;
        case 2: vifUnpackZx<VL, 2>(zx, vuData, src, count, destVec, cl, wl, bpv, dm, cv, pm); break;
        default: vifUnpackZx<VL, 3>(zx, vuData, src, count, destVec, cl, wl, bpv, dm, cv, pm); break;
        }
    }
} // namespace

enum Act : uint8_t { ACT_DECODED = 0, ACT_CONST = 1, ACT_PROTECT = 2 };
static void refRun(uint8_t *targetVuData, const uint8_t *srcBase, uint32_t vl, uint32_t vn, bool zeroExtend, uint32_t cl, uint32_t wl,
                   uint32_t writeVectorCount, uint32_t vuAddr, uint32_t bytesPerVector, Act act[4][4], uint32_t constVal[4][4])
{
                    const uint8_t *srcPtr = srcBase;
                    uint32_t destVec = vuAddr;
                    uint32_t cyclePos = 0;

                    for (uint32_t i = 0; i < writeVectorCount; ++i) {
                        uint32_t decoded[4];

                        if (vl == 2u) {
                            if (zeroExtend) {
                                if (vn == 0u) {
                                    uint32_t s = srcPtr[0];
                                    decoded[0] = s; decoded[1] = s; decoded[2] = s; decoded[3] = s;
                                } else if (vn == 1u) {
                                    decoded[0] = srcPtr[0]; decoded[1] = srcPtr[1];
                                } else if (vn == 2u) {
                                    decoded[0] = srcPtr[0]; decoded[1] = srcPtr[1]; decoded[2] = srcPtr[2];
                                } else {
                                    decoded[0] = srcPtr[0]; decoded[1] = srcPtr[1]; decoded[2] = srcPtr[2]; decoded[3] = srcPtr[3];
                                }
                            } else {
                                if (vn == 0u) {
                                    uint32_t s = static_cast<uint32_t>(static_cast<int32_t>(static_cast<int8_t>(srcPtr[0])));
                                    decoded[0] = s; decoded[1] = s; decoded[2] = s; decoded[3] = s;
                                } else if (vn == 1u) {
                                    decoded[0] = static_cast<uint32_t>(static_cast<int32_t>(static_cast<int8_t>(srcPtr[0])));
                                    decoded[1] = static_cast<uint32_t>(static_cast<int32_t>(static_cast<int8_t>(srcPtr[1])));
                                } else if (vn == 2u) {
                                    decoded[0] = static_cast<uint32_t>(static_cast<int32_t>(static_cast<int8_t>(srcPtr[0])));
                                    decoded[1] = static_cast<uint32_t>(static_cast<int32_t>(static_cast<int8_t>(srcPtr[1])));
                                    decoded[2] = static_cast<uint32_t>(static_cast<int32_t>(static_cast<int8_t>(srcPtr[2])));
                                } else {
                                    decoded[0] = static_cast<uint32_t>(static_cast<int32_t>(static_cast<int8_t>(srcPtr[0])));
                                    decoded[1] = static_cast<uint32_t>(static_cast<int32_t>(static_cast<int8_t>(srcPtr[1])));
                                    decoded[2] = static_cast<uint32_t>(static_cast<int32_t>(static_cast<int8_t>(srcPtr[2])));
                                    decoded[3] = static_cast<uint32_t>(static_cast<int32_t>(static_cast<int8_t>(srcPtr[3])));
                                }
                            }
                        } else if (vl == 1u) {
                            if (zeroExtend) {
                                if (vn == 0u) {
                                    uint16_t r = 0; std::memcpy(&r, srcPtr, 2);
                                    uint32_t s = static_cast<uint32_t>(r);
                                    decoded[0] = s; decoded[1] = s; decoded[2] = s; decoded[3] = s;
                                } else if (vn == 1u) {
                                    uint16_t r[2]; std::memcpy(r, srcPtr, 4);
                                    decoded[0] = r[0]; decoded[1] = r[1];
                                } else if (vn == 2u) {
                                    uint16_t r[3]; std::memcpy(r, srcPtr, 6);
                                    decoded[0] = r[0]; decoded[1] = r[1]; decoded[2] = r[2];
                                } else {
                                    uint16_t r[4]; std::memcpy(r, srcPtr, 8);
                                    decoded[0] = r[0]; decoded[1] = r[1]; decoded[2] = r[2]; decoded[3] = r[3];
                                }
                            } else {
                                if (vn == 0u) {
                                    int16_t r = 0; std::memcpy(&r, srcPtr, 2);
                                    uint32_t s = static_cast<uint32_t>(static_cast<int32_t>(r));
                                    decoded[0] = s; decoded[1] = s; decoded[2] = s; decoded[3] = s;
                                } else if (vn == 1u) {
                                    int16_t r[2]; std::memcpy(r, srcPtr, 4);
                                    decoded[0] = static_cast<uint32_t>(static_cast<int32_t>(r[0]));
                                    decoded[1] = static_cast<uint32_t>(static_cast<int32_t>(r[1]));
                                } else if (vn == 2u) {
                                    int16_t r[3]; std::memcpy(r, srcPtr, 6);
                                    decoded[0] = static_cast<uint32_t>(static_cast<int32_t>(r[0]));
                                    decoded[1] = static_cast<uint32_t>(static_cast<int32_t>(r[1]));
                                    decoded[2] = static_cast<uint32_t>(static_cast<int32_t>(r[2]));
                                } else {
                                    int16_t r[4]; std::memcpy(r, srcPtr, 8);
                                    decoded[0] = static_cast<uint32_t>(static_cast<int32_t>(r[0]));
                                    decoded[1] = static_cast<uint32_t>(static_cast<int32_t>(r[1]));
                                    decoded[2] = static_cast<uint32_t>(static_cast<int32_t>(r[2]));
                                    decoded[3] = static_cast<uint32_t>(static_cast<int32_t>(r[3]));
                                }
                            }
                        } else { // vl == 0u
                            if (vn == 0u) {
                                uint32_t s = 0; std::memcpy(&s, srcPtr, 4);
                                decoded[0] = s; decoded[1] = s; decoded[2] = s; decoded[3] = s;
                            } else if (vn == 1u) {
                                std::memcpy(&decoded[0], srcPtr, 8);
                            } else if (vn == 2u) {
                                std::memcpy(&decoded[0], srcPtr, 12);
                            } else {
                                std::memcpy(&decoded[0], srcPtr, 16);
                            }
                        }

                        const uint32_t c = (cyclePos > 3u) ? 3u : cyclePos;
                        uint32_t *d = reinterpret_cast<uint32_t*>(targetVuData) + (destVec * 4u);

                        if (act[c][0] == ACT_DECODED) d[0] = decoded[0]; else if (act[c][0] == ACT_CONST) d[0] = constVal[c][0];
                        if (act[c][1] == ACT_DECODED) d[1] = decoded[1]; else if (act[c][1] == ACT_CONST) d[1] = constVal[c][1];
                        if (act[c][2] == ACT_DECODED) d[2] = decoded[2]; else if (act[c][2] == ACT_CONST) d[2] = constVal[c][2];
                        if (act[c][3] == ACT_DECODED) d[3] = decoded[3]; else if (act[c][3] == ACT_CONST) d[3] = constVal[c][3];

                        srcPtr += bytesPerVector;
                        cyclePos++;
                        destVec++;
                        if (cyclePos == wl) {
                            cyclePos = 0;
                            destVec += (cl - wl);
                        }
                    }

}
int main()
{
    std::mt19937 rng(1234);
    int bad = 0, total = 0;
    for (int it = 0; it < 400000; ++it)
    {
        uint32_t vl = rng() % 3, vn = rng() % 4;
        bool zx = rng() & 1;
        uint32_t wl = 1 + rng() % 5, cl = wl + rng() % 3, cnt = 1 + rng() % 24, vuAddr = rng() % 100;
        uint32_t comp = vn + 1, bits = (vl == 0 ? 32 : vl == 1 ? 16 : 8) * comp, bpv = (bits + 7) / 8;
        std::vector<uint8_t> src(cnt * bpv + 16);
        for (auto &b : src) b = (uint8_t)rng();
        bool maskEnable = rng() & 1;
        uint32_t mask = maskEnable ? (uint32_t)rng() : 0, row[4], col[4];
        for (int i = 0; i < 4; ++i) { row[i] = (uint32_t)rng(); col[i] = (uint32_t)rng(); }
        Act act[4][4];
        uint32_t constVal[4][4];
        uint32_t maxC = std::min<uint32_t>(wl, 4u);
        for (uint32_t c = 0; c < maxC; ++c)
            for (uint32_t f = 0; f < 4; ++f)
            {
                uint32_t spec = maskEnable ? ((mask >> (((c * 4u) + f) * 2u)) & 3u) : 0u;
                constVal[c][f] = 0;
                if (spec == 3u || (spec == 0u && vn != 0u && f >= comp)) act[c][f] = ACT_PROTECT;
                else if (spec == 1u) { act[c][f] = ACT_CONST; constVal[c][f] = row[f]; }
                else if (spec == 2u) { act[c][f] = ACT_CONST; constVal[c][f] = col[c]; }
                else act[c][f] = ACT_DECODED;
            }
        for (uint32_t c = maxC; c < 4; ++c)
            for (uint32_t f = 0; f < 4; ++f) { act[c][f] = act[3][f]; constVal[c][f] = constVal[3][f]; }
        uint32_t last = vuAddr + ((cnt - 1) / wl) * cl + ((cnt - 1) % wl);
        if (last >= 500) continue;
        alignas(16) static uint8_t a[16 * 512], b[16 * 512];
        for (auto &x : a) x = (uint8_t)rng();
        memcpy(b, a, sizeof a);
        refRun(a, src.data(), vl, vn, zx, cl, wl, cnt, vuAddr, bpv, act, constVal);
        alignas(16) uint32_t dmA[4][4] = {}, pmA[4][4] = {}, cvA[4][4] = {};
        for (uint32_t c = 0; c < maxC; ++c)
            for (uint32_t f = 0; f < 4; ++f)
            {
                dmA[c][f] = act[c][f] == ACT_DECODED ? ~0u : 0;
                pmA[c][f] = act[c][f] == ACT_PROTECT ? ~0u : 0;
                cvA[c][f] = act[c][f] == ACT_CONST ? constVal[c][f] : 0;
            }
        __m128i dm[4], pm[4], cv[4];
        for (uint32_t c = 0; c < 4; ++c)
        {
            uint32_t k = std::min(c, maxC - 1u);
            dm[c] = _mm_load_si128((const __m128i *)dmA[k]);
            pm[c] = _mm_load_si128((const __m128i *)pmA[k]);
            cv[c] = _mm_load_si128((const __m128i *)cvA[k]);
        }
        switch (vl)
        {
        case 0: vifUnpackVn<0>(vn, zx, b, src.data(), cnt, vuAddr, cl, wl, bpv, dm, cv, pm); break;
        case 1: vifUnpackVn<1>(vn, zx, b, src.data(), cnt, vuAddr, cl, wl, bpv, dm, cv, pm); break;
        default: vifUnpackVn<2>(vn, zx, b, src.data(), cnt, vuAddr, cl, wl, bpv, dm, cv, pm);
        }
        ++total;
        if (memcmp(a, b, sizeof a))
            if (++bad < 6) printf("MISMATCH vl=%u vn=%u zx=%d cl=%u wl=%u cnt=%u mask=%08x\n", vl, vn, zx, cl, wl, cnt, mask);
    }
    printf("total=%d bad=%d\n", total, bad);
    return bad != 0;
}
