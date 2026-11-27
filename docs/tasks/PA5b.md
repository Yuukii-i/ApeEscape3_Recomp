# Task PA5b: fix a scope error from PA5. One file. No header edits. Do NOT build, run or commit.
File: c:\ApeEscape3_Recomp\PS2Recomp\ps2xRuntime\src\lib\render\rd_view.cpp
Error: line ~7751 `pauseBgOn`, `pauseFrame`, `sceneSnapped`, `takeScene` undeclared (declared ~4937 in an inner block).
Fix: move these declarations to directly after `bool palDrawnThisFrame = false; // FIX-RD86` (~4357), same scope:
- `static const bool pauseBgOn = ...;` (unchanged initializer)
- `bool pauseFrame = false;` and `bool sceneSnapped = false;`
- the whole `auto takeScene = [&]() { ... };` lambda (it uses vx, vy, vw, vh, g_rdc and the s_scene* statics, all visible there).
At the old place (~4937) keep copyTargets, the lambdas isPauseTint/isPauseBlur and the scan loop, and replace
`const bool pauseFrame = ...` with an assignment: `pauseFrame = pauseBgOn && hasPauseTint && hasPauseBlur;`.
Delete the old duplicate declarations there. Keep // FIX-PA5 marks. Reply in <=3 lines.
