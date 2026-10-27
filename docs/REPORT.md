# Task EX Report
- BUILD OK (full rebuild succeeded).
- Grep verified: `ex hle` in `VU.cpp`, `ex badstore` and `ex fpu` in `ps2_runtime.cpp`.
- A. Fixed `sceVu0Normalize` in `VU.cpp`: computes `len = sqrt(x*x + y*y + z*z)` (xyz only); `out.w = 0.0f`; clamps zero-length to 0.
- B. Audited HLE in `VU.cpp`: wrapped all 42 `sceVu0*` stubs with input/output logging (first 6 per stub, cap 60 bad), bad detection, `OUT_BAD_FROM_SANE` marker, and 8-entry ring buffer.
- C. Store watch in `ps2_runtime.h`, `VU.cpp`, and `ps2_runtime.cpp`: monitors `0x785AF0..0x785C20` writes, logs `ex badstore` (cap 60), dumps 76 words and previous 8 HLE/vcallms calls on first hit.
- D. Region scan & snapshot in `ps2_runtime.cpp` and `ps2_vif1_interpreter.cpp`: scans camera block on every `vcallms` and UNPACK, prints `first_bad`, and takes 19-line `ex snap` at calls #1, #1000, #2000.
- E. EE FPU self-test in `ps2_runtime.cpp`: verifies div.s, sqrt.s, rsqrt.s, mul.s, add.s, cvt.w.s, cvt.s.w edge cases at startup (`ex fpu`).
- Touched files: `ps2xRuntime/include/ps2_runtime.h`, `ps2xRuntime/src/lib/Kernel/Stubs/VU.cpp`, `ps2xRuntime/src/lib/ps2_runtime.cpp`, `ps2xRuntime/src/lib/ps2_vif1_interpreter.cpp`, `docs/REPORT.md`.
- Committed on branch `task/EX` in PS2Recomp and ApeEscape3_Recomp.
