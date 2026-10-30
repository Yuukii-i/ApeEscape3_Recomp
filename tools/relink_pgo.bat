@echo off
rem PERF-KA: Usage: tools\relink_pgo.bat <lib path> <exe tag> <withprofilert: 1|0>
rem Relinks ps2EntryRunner.exe against the clang lib, optionally adding the LLVM profile runtime (needed for the instrumented lib),
rem copies it to build\PS2Recomp\ps2xRuntime\ps2EntryRunner_<tag>.exe, then resets the linker flags.
setlocal
cd /d C:\ApeEscape3_Recomp
if not defined VULKAN_SDK set "VULKAN_SDK=C:\VulkanSDK\1.4.363.0"
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b 1
for %%I in ("C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\Llvm\x64\lib\clang\22\lib\windows\clang_rt.profile-x86_64.lib") do set "PGORT=%%~sI"
if "%~3"=="1" (
  cmake -B build -DRECOMP_CLANG_LIB=%1 "-DCMAKE_EXE_LINKER_FLAGS=%PGORT%"
) else (
  cmake -B build -DRECOMP_CLANG_LIB=%1 "-DCMAKE_EXE_LINKER_FLAGS="
)
if errorlevel 1 exit /b 1
cmake --build build --config Release
if errorlevel 1 exit /b 1
copy /y build\PS2Recomp\ps2xRuntime\ps2EntryRunner.exe build\PS2Recomp\ps2xRuntime\ps2EntryRunner_%2.exe
cmake -B build "-DCMAKE_EXE_LINKER_FLAGS="
exit /b %ERRORLEVEL%
