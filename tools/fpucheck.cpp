#include <algorithm>
#include <bit>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

#if defined(_MSC_VER)
#include <intrin.h>
#else
#include <immintrin.h>
#endif

#include "ps2_runtime_macros.h"

// Minimal stubs for externs referenced by ps2_runtime_macros.h / ps2_runtime.h
bool ps2xFpuProbeEnabled() { return false; }
void ps2xFpuProbe(void *, int) {}
uint32_t g_ps2wwBase = 0;
uint32_t g_ps2wwLen = 0;

int main(int argc, char **argv)
{
    bool roundToNearest = false;
    for (int i = 1; i < argc; ++i)
    {
        if (std::strcmp(argv[i], "--rn") == 0)
            roundToNearest = true;
    }

    if (!roundToNearest)
    {
        const char *rtz = std::getenv("PS2X_EE_RTZ");
        if (!(rtz && rtz[0] == '0'))
            _mm_setcsr(_mm_getcsr() | 0x6000u);
    }

    std::printf("MXCSR=0x%08x (%s)\n", _mm_getcsr(), roundToNearest ? "RN" : "RTZ");

    constexpr size_t kNumPairs = 64;
    constexpr size_t kNumOps = 12;

    std::FILE *fin = std::fopen("logs/fr/fpu_inputs.bin", "rb");
    if (!fin)
    {
        std::perror("fopen logs/fr/fpu_inputs.bin");
        return 1;
    }
    uint32_t inputs[kNumPairs][2]{};
    if (std::fread(inputs, sizeof(uint32_t), kNumPairs * 2, fin) != kNumPairs * 2)
    {
        std::fprintf(stderr, "Failed to read 64 pairs from logs/fr/fpu_inputs.bin\n");
        std::fclose(fin);
        return 1;
    }
    std::fclose(fin);

    std::FILE *fref = std::fopen("logs/fr/fpu_pcsx2_out.bin", "rb");
    if (!fref)
    {
        std::perror("fopen logs/fr/fpu_pcsx2_out.bin");
        return 1;
    }
    uint32_t pcsx2Out[kNumPairs][kNumOps]{};
    if (std::fread(pcsx2Out, sizeof(uint32_t), kNumPairs * kNumOps, fref) != kNumPairs * kNumOps)
    {
        std::fprintf(stderr, "Failed to read 64x12 results from logs/fr/fpu_pcsx2_out.bin\n");
        std::fclose(fref);
        return 1;
    }
    std::fclose(fref);

    const char *opNames[kNumOps] = {
        "add.s",
        "sub.s",
        "mul.s",
        "div.s",
        "sqrt.s",
        "rsqrt.s",
        "madd.s",
        "msub.s",
        "cvt.w.s",
        "cvt.s.w",
        "max.s",
        "min.s",
    };

    uint32_t oursOut[kNumPairs][kNumOps]{};
    R5900Context ctx{};
    R5900Context *ctxPtr = &ctx;

    for (size_t i = 0; i < kNumPairs; ++i)
    {
        const uint32_t ua = inputs[i][0];
        const uint32_t ub = inputs[i][1];
        std::memcpy(&ctx.f[1], &ua, sizeof(ua));
        std::memcpy(&ctx.f[2], &ub, sizeof(ub));

        // 0: add.s a+b
        ctx.f[3] = FPU_ADD_S(ctx.f[1], ctx.f[2]);
        std::memcpy(&oursOut[i][0], &ctx.f[3], sizeof(uint32_t));

        // 1: sub.s a-b
        ctx.f[3] = FPU_SUB_S(ctx.f[1], ctx.f[2]);
        std::memcpy(&oursOut[i][1], &ctx.f[3], sizeof(uint32_t));

        // 2: mul.s a*b
        ctx.f[3] = FPU_MUL_S(ctx.f[1], ctx.f[2]);
        std::memcpy(&oursOut[i][2], &ctx.f[3], sizeof(uint32_t));

        // 3: div.s a/b
        ctx.f[3] = FPU_DIV_S(ctx.f[1], ctx.f[2]);
        std::memcpy(&oursOut[i][3], &ctx.f[3], sizeof(uint32_t));

        // 4: sqrt.s f3, f2
        ctx.f[3] = FPU_SQRT_S(ctx.f[2]);
        std::memcpy(&oursOut[i][4], &ctx.f[3], sizeof(uint32_t));

        // 5: rsqrt.s f3, f1, f2
        ctx.f[3] = FPU_RSQRT_S(ctx.f[1], ctx.f[2]);
        std::memcpy(&oursOut[i][5], &ctx.f[3], sizeof(uint32_t));

        // 6: adda.s(a,b) then madd.s f3,f1,f2 => ACC + a*b
        FPU_SET_ACC(ctxPtr, FPU_ADD_S(ctx.f[1], ctx.f[2]));
        ctx.f[3] = FPU_ADD_S(ctx.f_acc, FPU_MUL_S(ctx.f[1], ctx.f[2]));
        std::memcpy(&oursOut[i][6], &ctx.f[3], sizeof(uint32_t));

        // 7: adda.s(a,b) then msub.s f3,f1,f2 => ACC - a*b
        FPU_SET_ACC(ctxPtr, FPU_ADD_S(ctx.f[1], ctx.f[2]));
        ctx.f[3] = FPU_SUB_S(ctx.f_acc, FPU_MUL_S(ctx.f[1], ctx.f[2]));
        std::memcpy(&oursOut[i][7], &ctx.f[3], sizeof(uint32_t));

        // 8: cvt.w.s f3, f1 (raw int bits of result)
        {
            int32_t tmp = FPU_CVT_W_S(ctx.f[1]);
            std::memcpy(&ctx.f[3], &tmp, sizeof(tmp));
            std::memcpy(&oursOut[i][8], &ctx.f[3], sizeof(uint32_t));
        }

        // 9: cvt.s.w f3, f1 (f1's raw bits taken as int32)
        {
            int32_t tmp;
            std::memcpy(&tmp, &ctx.f[1], sizeof(tmp));
            ctx.f[3] = FPU_CVT_S_W(tmp);
            std::memcpy(&oursOut[i][9], &ctx.f[3], sizeof(uint32_t));
        }

        // 10: max.s a, b
        ctx.f[3] = std::max(ctx.f[1], ctx.f[2]);
        std::memcpy(&oursOut[i][10], &ctx.f[3], sizeof(uint32_t));

        // 11: min.s a, b
        ctx.f[3] = std::min(ctx.f[1], ctx.f[2]);
        std::memcpy(&oursOut[i][11], &ctx.f[3], sizeof(uint32_t));
    }

    // FIX-FC2: classify mismatches into KNOWN (denormal input or PCSX2 +-0x7f7fffff vs ours +-0x7fffffff clamp) vs REAL.
    auto isDenormal = [](uint32_t bits) -> bool {
        const uint32_t mag = bits & 0x7FFFFFFFu;
        return mag != 0u && mag < 0x00800000u;
    };
    auto isKnownMismatch = [&](size_t op, uint32_t ua, uint32_t ub, uint32_t pcsx2, uint32_t ours) -> bool {
        const bool denorm = (op == 4) ? isDenormal(ub)
                          : (op == 8) ? isDenormal(ua)
                          : (op == 9) ? false
                                      : (isDenormal(ua) || isDenormal(ub));
        if (denorm)
            return true;
        return (pcsx2 & 0x7FFFFFFFu) == 0x7F7FFFFFu &&
               (ours & 0x7FFFFFFFu) == 0x7FFFFFFFu &&
               ((pcsx2 ^ ours) & 0x80000000u) == 0u;
    };

    for (size_t op = 0; op < kNumOps; ++op)
    {
        size_t realCount = 0;
        size_t knownCount = 0;
        for (size_t i = 0; i < kNumPairs; ++i)
        {
            if (oursOut[i][op] != pcsx2Out[i][op])
            {
                if (isKnownMismatch(op, inputs[i][0], inputs[i][1], pcsx2Out[i][op], oursOut[i][op]))
                    ++knownCount;
                else
                    ++realCount;
            }
        }
        std::printf("op %s: REAL %zu KNOWN %zu\n", opNames[op], realCount, knownCount);

        size_t printed = 0;
        for (size_t i = 0; i < kNumPairs && printed < 6; ++i)
        {
            if (oursOut[i][op] != pcsx2Out[i][op] &&
                !isKnownMismatch(op, inputs[i][0], inputs[i][1], pcsx2Out[i][op], oursOut[i][op]))
            {
                std::printf("  a=0x%08x b=0x%08x pcsx2=0x%08x ours=0x%08x\n",
                            inputs[i][0], inputs[i][1], pcsx2Out[i][op], oursOut[i][op]);
                ++printed;
            }
        }
    }

    return 0;
}
