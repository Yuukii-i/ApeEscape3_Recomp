# Task IG Report
- Build result: BUILD OK via tools\build.bat (ps2_runtime.cpp only, zero warnings).
- diff --stat: ps2xRuntime/src/lib/ps2_runtime.cpp | 13 ++++++++----- (no .h touched).
- Gated FQ/FM/FZ2/GX/GY dispatch debug probes behind PS2X_DISPATCH_PROBES.
- PS2Recomp commit: a730766 (branch task/IG).