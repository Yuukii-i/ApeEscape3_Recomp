@echo off
rem Usage: tools\relink_with_lib.bat <lib path> <exe tag>   -> relinks ps2EntryRunner.exe against that lib and copies it to build\ps2EntryRunner_<tag>.exe
setlocal
cd /d C:\ApeEscape3_Recomp
if not defined VULKAN_SDK set "VULKAN_SDK=C:\VulkanSDK\1.4.363.0"
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b 1
cmake -B build -DRECOMP_CLANG_LIB=%1
if errorlevel 1 exit /b 1
cmake --build build --config Release
if errorlevel 1 exit /b 1
copy /y build\PS2Recomp\ps2xRuntime\ps2EntryRunner.exe build\ps2EntryRunner_%2.exe
exit /b %ERRORLEVEL%
