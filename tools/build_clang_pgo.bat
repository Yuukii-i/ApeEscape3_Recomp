@echo off
rem PERF-KA: clang-cl PGO build of the generated guest code. Usage: tools\build_clang_pgo.bat gen|use
rem   gen -> build_clang_pgogen\recomp_source_clang.lib (instrumented, -fprofile-instr-generate)
rem   use -> build_clang_pgouse\recomp_source_clang.lib (needs pgo\ae3.profdata from llvm-profdata merge)
rem Runs at BELOW NORMAL priority with 6 parallel jobs so the PC stays usable (override jobs with PS2X_JOBS).
setlocal
if not defined PS2X_LOW (
  set PS2X_LOW=1
  start "" /belownormal /wait cmd /c ""%~f0" %*"
  exit /b %ERRORLEVEL%
)
if not defined PS2X_JOBS set PS2X_JOBS=6
cd /d C:\ApeEscape3_Recomp
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b 1
set "CLANGCL=C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/Llvm/x64/bin/clang-cl.exe"
set "BASEFLAGS=-fno-strict-aliasing;-fwrapv;-ftrivial-auto-var-init=zero"
if /i "%~1"=="gen" (
  set "TAG=pgogen"
  set "FLAGS=%BASEFLAGS%;-fprofile-instr-generate"
) else if /i "%~1"=="use" (
  if not exist pgo\ae3.profdata ( echo pgo\ae3.profdata missing & exit /b 2 )
  set "TAG=pgouse"
  set "FLAGS=%BASEFLAGS%;-fprofile-instr-use=C:/ApeEscape3_Recomp/pgo/ae3.profdata;-Wno-profile-instr-unprofiled;-Wno-profile-instr-out-of-date"
) else (
  echo usage: build_clang_pgo.bat gen^|use
  exit /b 2
)
if not exist build_clang_%TAG%\CMakeCache.txt (
  cmake -S tools\clang_recomp -B build_clang_%TAG% -G Ninja -DCMAKE_BUILD_TYPE=Release "-DCMAKE_CXX_COMPILER=%CLANGCL%" "-DRECOMP_CLANG_EXTRA_FLAGS=%FLAGS%"
  if errorlevel 1 exit /b 1
)
cmake --build build_clang_%TAG% -j %PS2X_JOBS%
exit /b %ERRORLEVEL%
