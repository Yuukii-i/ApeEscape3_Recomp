@echo off
setlocal

if not defined VULKAN_SDK set "VULKAN_SDK=C:\VulkanSDK\1.4.363.0"
cd /d C:\ApeEscape3_Recomp

call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
if errorlevel 1 (
    echo BUILD FAIL
    exit /b 1
)

for /f "delims=" %%i in ('powershell -NoProfile -Command "(Get-Date).Ticks"') do set "START_TICKS=%%i"

cmake -S tools/sdl_smoke -B build_sdl_smoke -G Ninja -DCMAKE_BUILD_TYPE=Release > build_sdl_smoke_output.tmp 2>&1
if errorlevel 1 (
    echo BUILD FAIL
    findstr /i "error fatal" build_sdl_smoke_output.tmp | powershell -NoProfile -Command "$input | Select-Object -First 30"
    exit /b 1
)

cmake --build build_sdl_smoke >> build_sdl_smoke_output.tmp 2>&1
set BUILD_ERR=%ERRORLEVEL%

for /f "delims=" %%i in ('powershell -NoProfile -Command "$s = [Math]::Round(((Get-Date).Ticks - %START_TICKS%) / 1e7, 1); Write-Output $s"') do set "DURATION=%%i"

if %BUILD_ERR% equ 0 (
    echo BUILD OK %DURATION%s build_sdl_smoke\sdl_smoke.exe
    exit /b 0
) else (
    echo BUILD FAIL
    findstr /i "error fatal" build_sdl_smoke_output.tmp | powershell -NoProfile -Command "$input | Select-Object -First 30"
    exit /b 1
)
