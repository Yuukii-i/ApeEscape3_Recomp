# Task PA5c: pause tint is applied twice. One file, tiny edit. No header edits. Do NOT build, run or commit.
File: c:\ApeEscape3_Recomp\PS2Recomp\ps2xRuntime\src\lib\render\rd_view.cpp, in emit2dBatch (~5100-5240).
Cause: the substituted scene texture is tinted by the shader palette ramp (final colour), then TFX modulate
multiplies it again by the batch vertex colour. Measured 18,18,55; target 42,42,75.
Fix: where `// FIX-PA5` sets `texId = s_sceneTexId` (~5112), also set a local bool (declare it next to `palMode`)
`pauseSceneSub = true`. After the later `tfxVal = static_cast<int>((b0.tex0 >> 35) & 3ull);` block and before
`tfxVal` is passed to the `rdgfx::Uniform::Tfx` uniform: `if (pauseSceneSub) tfxVal = 1; // FIX-PA5` (decal:
vertex colour ignored). Nothing else. Reply in <=2 lines.
