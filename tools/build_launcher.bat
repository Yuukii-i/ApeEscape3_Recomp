@echo off
setlocal

cd /d C:\ApeEscape3_Recomp

call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
if errorlevel 1 (
    echo BUILD FAIL
    exit /b 1
)

set "REPO_DIR=%CD:\=/%"
set "FETCH_ARGS="
if exist "build_avx2\_deps\sdl3-src" if exist "build_avx2\_deps\imgui-src" (
    set "FETCH_ARGS=-DFETCHCONTENT_SOURCE_DIR_SDL3=%REPO_DIR%/build_avx2/_deps/sdl3-src -DFETCHCONTENT_SOURCE_DIR_IMGUI=%REPO_DIR%/build_avx2/_deps/imgui-src -DFETCHCONTENT_FULLY_DISCONNECTED=ON"
)

cmake -S tools/launcher -B build_launcher -DCMAKE_BUILD_TYPE=Release %FETCH_ARGS% > cmake_launcher_config.tmp 2>&1
if errorlevel 1 (
    echo BUILD FAIL
    type cmake_launcher_config.tmp
    del cmake_launcher_config.tmp 2>nul
    exit /b 1
)
del cmake_launcher_config.tmp 2>nul

cmake --build build_launcher --config Release --parallel %NUMBER_OF_PROCESSORS% > build_launcher_output.tmp 2>&1
set BUILD_ERR=%ERRORLEVEL%
if %BUILD_ERR% neq 0 (
    echo BUILD FAIL
    type build_launcher_output.tmp
    del build_launcher_output.tmp 2>nul
    exit /b 1
)
del build_launcher_output.tmp 2>nul

if exist "build_launcher\Release\test_settings.exe" (
    "build_launcher\Release\test_settings.exe" ps2x.ini
) else (
    "build_launcher\test_settings.exe" ps2x.ini
)
if errorlevel 1 (
    echo TEST FAIL
    exit /b 1
)

if exist "build_launcher\Release\ape3_launcher.exe" (
    "build_launcher\Release\ape3_launcher.exe" --print-launch --ini ps2x.ini
) else (
    "build_launcher\ape3_launcher.exe" --print-launch --ini ps2x.ini
)
if %ERRORLEVEL% equ 1 (
    echo PRINT-LAUNCH FAIL
    exit /b 1
)

echo BUILD AND TEST OK
exit /b 0
