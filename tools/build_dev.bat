@echo off
rem 2026-11-15: dev build = build_avx2 (/arch:AVX2, Release); exe copied to build\ so all tools/commands keep their path
setlocal

if not defined VULKAN_SDK set "VULKAN_SDK=C:\VulkanSDK\1.4.363.0"
cd /d C:\ApeEscape3_Recomp

call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
if errorlevel 1 (
    echo BUILD FAIL
    exit /b 1
)

cmake -S . -B build_avx2 -DCMAKE_BUILD_TYPE=Release -DPS2X_DEV_BUILD=ON -DPS2X_PGO=OFF "-DCMAKE_CXX_FLAGS=/DWIN32 /D_WINDOWS /EHsc /arch:AVX2" "-DCMAKE_C_FLAGS=/DWIN32 /D_WINDOWS /arch:AVX2" > cmake_config.tmp 2>&1
if errorlevel 1 (
    echo BUILD FAIL
    type cmake_config.tmp
    del cmake_config.tmp 2>nul
    exit /b 1
)
del cmake_config.tmp 2>nul

for /f "delims=" %%i in ('powershell -NoProfile -Command "(Get-Date).Ticks"') do set "START_TICKS=%%i"

cmake --build build_avx2 --config Release --target ps2EntryRunner --parallel %NUMBER_OF_PROCESSORS% > build_dev_output.tmp 2>&1
set BUILD_ERR=%ERRORLEVEL%

for /f "delims=" %%i in ('powershell -NoProfile -Command "$s = [Math]::Round(((Get-Date).Ticks - %START_TICKS%) / 1e7, 1); Write-Output $s"') do set "DURATION=%%i"

if %BUILD_ERR% equ 0 (
    if not exist build\PS2Recomp\ps2xRuntime mkdir build\PS2Recomp\ps2xRuntime
    copy /Y build_avx2\PS2Recomp\ps2xRuntime\ps2EntryRunner_dev.exe build\PS2Recomp\ps2xRuntime\ps2EntryRunner_dev.exe >nul
    echo BUILD OK %DURATION%s build\PS2Recomp\ps2xRuntime\ps2EntryRunner_dev.exe (avx2)
    del build_dev_output.tmp 2>nul
    exit /b 0
) else (
    echo BUILD FAIL
    findstr /i "error fatal" build_dev_output.tmp | powershell -NoProfile -Command "$input | Select-Object -First 30"
    del build_dev_output.tmp 2>nul
    exit /b 1
)
