@echo off
setlocal
cd /d C:\ApeEscape3_Recomp
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b 1
set CLANGCL=C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/Llvm/x64/bin/clang-cl.exe
if not exist build_clang\CMakeCache.txt (
  cmake -S tools\clang_recomp -B build_clang -G Ninja -DCMAKE_BUILD_TYPE=Release "-DCMAKE_CXX_COMPILER=%CLANGCL%"
  if errorlevel 1 exit /b 1
)
cmake --build build_clang
exit /b %ERRORLEVEL%
