@echo off
setlocal enabledelayedexpansion
cd /d C:\ApeEscape3_Recomp

call build_release.bat < nul > build_output.tmp 2>&1
set BUILD_ERR=%ERRORLEVEL%

if %BUILD_ERR% equ 0 (
    echo BUILD OK
    del build_output.tmp 2>nul
    exit /b 0
) else (
    echo BUILD FAIL (%BUILD_ERR%)
    findstr /i "error fatal" build_output.tmp | powershell -Command "$input | Select-Object -First 30"
    del build_output.tmp 2>nul
    exit /b %BUILD_ERR%
)
