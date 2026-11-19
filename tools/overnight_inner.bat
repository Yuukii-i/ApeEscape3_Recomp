@echo off
rem Inner part of the overnight build: called by overnight_build.bat with all output redirected to the log.
if not defined VULKAN_SDK set "VULKAN_SDK=C:\VulkanSDK\1.4.363.0"
echo [inner] setting up VS environment
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat"
cd /d C:\ApeEscape3_Recomp
echo [inner] cwd=%CD%
echo [inner] configure (clearing RECOMP_CLANG_LIB so recomp_source is really rebuilt)
cmake -B build -DRECOMP_CLANG_LIB=
if errorlevel 1 exit /b 11
echo [inner] building (several hours)
cmake --build build --config Release
exit /b %ERRORLEVEL%
