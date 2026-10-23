#include <iostream>
#include <iomanip>
#include <cstdint>
#include <cstdlib>
#include <immintrin.h>
#include "extracted_macros.h"

struct TestResult {
    bool passed;
    const char *name;
    uint32_t expected[4];
    uint32_t actual[4];
};

void printLanes(const char *label, const uint32_t w[4]) {
    std::cout << label << ": [0x" << std::hex << std::setfill('0')
              << std::setw(8) << w[0] << ", 0x"
              << std::setw(8) << w[1] << ", 0x"
              << std::setw(8) << w[2] << ", 0x"
              << std::setw(8) << w[3] << "]\n";
}

int main() {
    std::cout << "========================================\n";
    std::cout << "PS2 MMI HI/LO Reference Semantics Test\n";
    #if defined(TEST_MACRO_TAKES_2_ARGS)
    std::cout << "Testing Mode: CURRENT MACROS (2 arguments)\n";
    #else
    std::cout << "Testing Mode: UPDATED MACROS (4 arguments)\n";
    #endif
    std::cout << "========================================\n\n";

    int totalTests = 0;
    int passedTests = 0;

    auto testLW = [&](const char *name, uint64_t hi, uint64_t lo, uint64_t hi1, uint64_t lo1,
                      uint32_t exp0, uint32_t exp1, uint32_t exp2, uint32_t exp3) {
        totalTests++;
        #if defined(TEST_MACRO_TAKES_2_ARGS)
        __m128i val = PS2_PMFHL_LW(hi, lo);
        #else
        __m128i val = PS2_PMFHL_LW(hi, lo, hi1, lo1);
        #endif

        uint32_t act[4];
        act[0] = static_cast<uint32_t>(_mm_extract_epi32(val, 0));
        act[1] = static_cast<uint32_t>(_mm_extract_epi32(val, 1));
        act[2] = static_cast<uint32_t>(_mm_extract_epi32(val, 2));
        act[3] = static_cast<uint32_t>(_mm_extract_epi32(val, 3));

        uint32_t exp[4] = { exp0, exp1, exp2, exp3 };
        bool ok = (act[0] == exp[0] && act[1] == exp[1] && act[2] == exp[2] && act[3] == exp[3]);

        std::cout << "[TEST] " << name << ": " << (ok ? "PASS" : "FAIL") << "\n";
        printLanes("  Expected", exp);
        printLanes("  Actual  ", act);
        if (ok) passedTests++;
        std::cout << "\n";
        return ok;
    };

    auto testMuldi3 = [&](const char *name, uint32_t v0_val, uint32_t a1_val) {
        totalTests++;
        // Emulate sub_00421A80 (__muldi3):
        // $a0 = v0_val, $a1 = a1_val
        // mult  $zero, $v0, $t7 ($t7 = a1 >> 32 = 0) -> hi=0, lo=0
        uint64_t hi = 0, lo = 0;
        // multu1 $zero, $v0, $a1
        uint64_t prod1 = static_cast<uint64_t>(v0_val) * static_cast<uint64_t>(a1_val);
        uint64_t lo1 = static_cast<uint64_t>(static_cast<int64_t>(static_cast<int32_t>(prod1 & 0xFFFFFFFFu)));
        uint64_t hi1 = static_cast<uint64_t>(static_cast<int64_t>(static_cast<int32_t>(prod1 >> 32)));

        // pmfhl.lw $at
        #if defined(TEST_MACRO_TAKES_2_ARGS)
        __m128i at_vec = PS2_PMFHL_LW(hi, lo);
        #else
        __m128i at_vec = PS2_PMFHL_LW(hi, lo, hi1, lo1);
        #endif

        // pcpyud $at, $at, $zero: copies upper 64 bits to lower 64 bits
        __m128i at_unpacked = _mm_unpackhi_epi64(at_vec, _mm_setzero_si128());
        uint64_t at_lo = static_cast<uint64_t>(_mm_cvtsi128_si64(at_unpacked));

        // daddu $v0, $at, $zero -> v0 = at_lo
        uint64_t expected = prod1;
        bool ok = (at_lo == expected);

        std::cout << "[TEST] " << name << " (multu1(" << v0_val << ", " << a1_val << ")): "
                  << (ok ? "PASS" : "FAIL") << "\n";
        std::cout << "  Expected result: " << std::dec << expected << " (0x" << std::hex << expected << ")\n";
        std::cout << "  Actual result:   " << std::dec << at_lo << " (0x" << std::hex << at_lo << ")\n";
        if (ok) passedTests++;
        std::cout << "\n";
        return ok;
    };

    // Vector 1: Zero
    testLW("PMFHL.LW: Zero Vector",
           0ull, 0ull, 0ull, 0ull,
           0u, 0u, 0u, 0u);

    // Vector 2: Positive 32-bit values
    testLW("PMFHL.LW: Positive Vector",
           0x22222222ull, 0x11111111ull, 0x44444444ull, 0x33333333ull,
           0x11111111u, 0x22222222u, 0x33333333u, 0x44444444u);

    // Vector 3: Negative sign-extended 64-bit HI/LO
    testLW("PMFHL.LW: Negative Sign-Extended Vector",
           0xFFFFFFFFFFFFFFFFull, 0xFFFFFFFFFFFFFFF6ull, 0xFFFFFFFFFFFFFFFEull, 0xFFFFFFFFFFFFFFECull,
           0xFFFFFFF6u, 0xFFFFFFFFu, 0xFFFFFFECu, 0xFFFFFFFEu);

    // Vector 4: Nonzero upper 32 bits
    testLW("PMFHL.LW: Nonzero Upper 32 Bits",
           0x0FEDCBA987654321ull, 0x123456789ABCDEF0ull, 0x89ABCDEF01234567ull, 0xA1B2C3D4E5F60718ull,
           0x9ABCDEF0u, 0x87654321u, 0xE5F60718u, 0x01234567u);

    // Vector 5: __muldi3 multu1(10, 5) -> 50
    testMuldi3("__muldi3 exact case 1", 5, 10);

    // Vector 6: __muldi3 multu1(1, 10) -> 10 (atoi accumulator step)
    testMuldi3("__muldi3 exact case 2", 1, 10);

    // Vector 7: __muldi3 multu1(11, 10) -> 110 (atoi parsing "115" second digit)
    testMuldi3("__muldi3 exact case 3", 11, 10);

    std::cout << "========================================\n";
    std::cout << "SUMMARY: " << passedTests << " / " << totalTests << " passed.\n";
    std::cout << "========================================\n";

    return (passedTests == totalTests) ? 0 : 1;
}
