@echo off
cd /d C:\ApeEscape3_Recomp

echo [build] Setting up VS 2026 x64 environment...
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 goto :error_env

if exist build\CMakeCache.txt goto :build

echo [build] Configuring with CMake (Release)...
cmake -B build -DCMAKE_BUILD_TYPE=Release -DPS2X_ENABLE_AGRESSIVE_LOGS=OFF
if errorlevel 1 goto :error_config

:build
echo [build] Building incrementally...
cmake --build build --config Release
if errorlevel 1 goto :error_build

echo [build] Done. Executable: build\PS2Recomp\ps2xRuntime\ps2EntryRunner.exe
pause
exit /b 0

:error_env
echo [build] ERROR: Failed to initialize VS environment.
pause
exit /b 1

:error_config
echo [build] ERROR: CMake configuration failed.
pause
exit /b 1

:error_build
echo [build] ERROR: Build failed.
pause
exit /b 1
