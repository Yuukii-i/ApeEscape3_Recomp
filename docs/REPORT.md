# Task IV Report
- Build result: BUILD OK (clang-cl recomp_source_clang.lib + relinked ps2EntryRunner.exe, 0 errors/warnings).
- Durations: build_clang_recomp.bat ~10m 38s (15:26:29 to 15:37:07); CMake configure + relink ~57s (15:37:25 to 15:38:22).
- Sizes: recomp_source_clang.lib = 195023112 bytes; ps2EntryRunner.exe = 140518912 bytes (vs MSVC 157841920 bytes).
- Diff: CMakeLists.txt, tools/build_clang_recomp.bat, tools/clang_recomp/CMakeLists.txt.