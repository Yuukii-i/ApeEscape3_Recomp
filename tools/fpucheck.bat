@echo off
cd /d C:\ApeEscape3_Recomp

echo [fpucheck] Setting up VS 2026 x64 environment...
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b 1

if not exist build mkdir build

echo [fpucheck] Compiling tools\fpucheck.cpp...
cl /nologo /O2 /EHsc /std:c++20 /I PS2Recomp\ps2xRuntime\include /I PS2Recomp\ps2xIOP\include tools\fpucheck.cpp /Fe:build\fpucheck.exe
if errorlevel 1 exit /b 1

echo [fpucheck] Running with RTZ (default)...
build\fpucheck.exe
if errorlevel 1 exit /b 1

echo [fpucheck] Running with --rn (round-to-nearest)...
build\fpucheck.exe --rn
if errorlevel 1 exit /b 1

exit /b 0

