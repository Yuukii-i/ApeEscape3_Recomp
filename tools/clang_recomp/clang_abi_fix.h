// PERF-JC: force-included (/FI) into every clang-cl TU of the generated guest code.
// ABI mismatch: MSVC returns __m128i from a non-static MEMBER function through a hidden pointer (shifts this/args by one register),
// clang-cl returns it in xmm0. PS2Runtime::Load128 is MSVC-compiled, so the clang caller passed ctx/vaddr in the wrong registers
// (callee saw ctx == vaddr -> access violation). Route READ128 through a void-returning free function instead.
#pragma once
#include "ps2_runtime_macros.h"
extern "C" void ps2x_Load128Out(PS2Runtime *rt, uint8_t *rdram, R5900Context *ctx, uint32_t vaddr, __m128i *out);
static inline __m128i ps2x_Load128Abi(PS2Runtime *rt, uint8_t *rdram, R5900Context *ctx, uint32_t vaddr)
{
    __m128i v;
    ps2x_Load128Out(rt, rdram, ctx, vaddr, &v);
    return v;
}
#undef READ128
#define READ128(addr) ([&]() -> __m128i {                     \
    uint32_t _addr = (uint32_t)(addr);                        \
    return PS2Runtime::isSpecialAddress(_addr)                \
        ? ps2x_Load128Abi(runtime, rdram, ctx, _addr)         \
        : FAST_READ128(_addr); }())
