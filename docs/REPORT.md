# Task GZ Report
- Fixed EE ABI stack argument reading (8-byte slots starting at sp+0) in `Support.h` Ps2VarArgCursor.
- Files touched: PS2Recomp ps2xRuntime/src/lib/Kernel/Stubs/Helpers/Support.h (Kernel/Stubs only, no recomp_source rebuild).
- Build status: BUILD OK via tools\build.bat.
- PS2Recomp commit: 310c96f (branch task/GZ).
