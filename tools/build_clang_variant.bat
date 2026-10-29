@echo off
rem Usage: tools\build_clang_variant.bat <tag> "<semicolon separated extra flags>"   e.g.  o3z3 "-O3;-march=znver3"
rem Builds build_clang_<tag>\recomp_source_clang.lib in its own tree. Does not touch build\ or build_clang\.
setlocal
cd /d C:\ApeEscape3_Recomp
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b 1
set CLANGCL=C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/Llvm/x64/bin/clang-cl.exe
if not exist build_clang_%1\CMakeCache.txt (
  cmake -S tools\clang_recomp -B build_clang_%1 -G Ninja -DCMAKE_BUILD_TYPE=Release "-DCMAKE_CXX_COMPILER=%CLANGCL%" "-DRECOMP_CLANG_EXTRA_FLAGS=%~2"
  if errorlevel 1 exit /b 1
)
cmake --build build_clang_%1
exit /b %ERRORLEVEL%
