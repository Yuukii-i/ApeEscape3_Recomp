@echo off
rem Overnight FULL rebuild (headers + ~570 generated files changed). BELOW NORMAL priority. Log: C:\ApeEscape3_Recomp\logs\overnight_build.log
rem Keep the laptop plugged in with sleep set to "never". All work is in overnight_inner.bat.
setlocal
if not defined PS2X_LOW (
  set PS2X_LOW=1
  start "" /belownormal /wait cmd /c ""%~f0""
  exit /b %ERRORLEVEL%
)
if not exist C:\ApeEscape3_Recomp\logs mkdir C:\ApeEscape3_Recomp\logs
echo [overnight] start %date% %time% > C:\ApeEscape3_Recomp\logs\overnight_build.log
call C:\ApeEscape3_Recomp\tools\overnight_inner.bat < nul >> C:\ApeEscape3_Recomp\logs\overnight_build.log 2>&1
set RC=%ERRORLEVEL%
echo [overnight] end %date% %time% errorlevel=%RC% >> C:\ApeEscape3_Recomp\logs\overnight_build.log
if %RC% neq 0 goto :fail
copy /y C:\ApeEscape3_Recomp\build\PS2Recomp\ps2xRuntime\ps2EntryRunner.exe C:\ApeEscape3_Recomp\build\PS2Recomp\ps2xRuntime\ps2EntryRunner_c317.exe >> C:\ApeEscape3_Recomp\logs\overnight_build.log 2>&1
echo [overnight] BUILD OK >> C:\ApeEscape3_Recomp\logs\overnight_build.log
exit /b 0

:fail
echo [overnight] BUILD FAIL >> C:\ApeEscape3_Recomp\logs\overnight_build.log
findstr /i /c:"error C" /c:"fatal error" /c:"LNK" C:\ApeEscape3_Recomp\logs\overnight_build.log > C:\ApeEscape3_Recomp\logs\overnight_build_errors.txt
exit /b %RC%
