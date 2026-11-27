@echo off
cd /d C:\ApeEscape3_Recomp
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
if not exist build mkdir build
if not exist build\vucheck_obj mkdir build\vucheck_obj
set REC=PS2Recomp\ps2xRecomp
echo [vucheck] building vucheck_gen.exe (real VU translator)...
cl /nologo /O1 /EHsc /std:c++20 /Zc:preprocessor /I tools\vucheck\shim /I %REC%\include /I PS2Recomp\ps2xRuntime\include /Fobuild\vucheck_obj\ ^
  tools\vucheck\vucheck_gen.cpp %REC%\src\lib\vu_translator.cpp %REC%\src\lib\vu_translation_helpers.cpp ^
  /Fe:build\vucheck_gen.exe
if errorlevel 1 exit /b 1
build\vucheck_gen.exe tools\vucheck\ops.txt tools\vucheck\vucheck_ops.inc
if errorlevel 1 exit /b 1
echo [vucheck] building vucheck.exe...
cl /nologo /O2 /EHsc /std:c++20 /I PS2Recomp\ps2xRuntime\include /I PS2Recomp\ps2xIOP\include tools\vucheck\vucheck.cpp /Fe:build\vucheck.exe /Fo:build\vucheck_main.obj
if errorlevel 1 exit /b 1
echo [vucheck] OK: build\vucheck.exe  (run: build\vucheck.exe --selftest)
exit /b 0



