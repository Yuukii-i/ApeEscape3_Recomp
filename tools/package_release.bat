@echo off
setlocal EnableDelayedExpansion

cd /d C:\ApeEscape3_Recomp

set "STAGING_DIR=release_staging"
set "RUNTIME_EXE=%~1"

if "%RUNTIME_EXE%"=="" (
    if exist "build_avx2\PS2Recomp\ps2xRuntime\ps2EntryRunner_dev.exe" (
        set "RUNTIME_EXE=build_avx2\PS2Recomp\ps2xRuntime\ps2EntryRunner_dev.exe"
    ) else if exist "build_avx2\PS2Recomp\ps2xRuntime\Release\ps2EntryRunner_dev.exe" (
        set "RUNTIME_EXE=build_avx2\PS2Recomp\ps2xRuntime\Release\ps2EntryRunner_dev.exe"
    ) else if exist "build_avx2\Release\ps2EntryRunner_dev.exe" (
        set "RUNTIME_EXE=build_avx2\Release\ps2EntryRunner_dev.exe"
    ) else if exist "build_avx2\ps2EntryRunner_dev.exe" (
        set "RUNTIME_EXE=build_avx2\ps2EntryRunner_dev.exe"
    )
)

if "%RUNTIME_EXE%"=="" (
    echo ERROR: Runtime executable not found in build_avx2 and no argument provided.
    exit /b 1
)
if not exist "%RUNTIME_EXE%" (
    echo ERROR: Runtime executable not found: %RUNTIME_EXE%
    exit /b 1
)

set "LAUNCHER_EXE="
if exist "build_launcher\ape3_launcher.exe" (
    set "LAUNCHER_EXE=build_launcher\ape3_launcher.exe"
) else if exist "build_launcher\Release\ape3_launcher.exe" (
    set "LAUNCHER_EXE=build_launcher\Release\ape3_launcher.exe"
)
if "%LAUNCHER_EXE%"=="" (
    echo ERROR: ape3_launcher.exe not found in build_launcher.
    exit /b 1
)

if not exist "ps2x.ini" (
    echo ERROR: Repo ps2x.ini not found.
    exit /b 1
)

for %%F in ("%RUNTIME_EXE%") do set "RUNTIME_NAME=%%~nxF"

if exist "%STAGING_DIR%" (
    rmdir /s /q "%STAGING_DIR%"
    if errorlevel 1 (
        echo ERROR: Failed to clean %STAGING_DIR%.
        exit /b 1
    )
)
mkdir "%STAGING_DIR%"
if errorlevel 1 (
    echo ERROR: Failed to create %STAGING_DIR%.
    exit /b 1
)

copy /y "%RUNTIME_EXE%" "%STAGING_DIR%\%RUNTIME_NAME%" >nul
if errorlevel 1 (
    echo ERROR: Failed to copy runtime executable.
    exit /b 1
)

copy /y "%LAUNCHER_EXE%" "%STAGING_DIR%\ape3_launcher.exe" >nul
if errorlevel 1 (
    echo ERROR: Failed to copy ape3_launcher.exe.
    exit /b 1
)

powershell -NoProfile -Command "$lines = Get-Content -LiteralPath 'ps2x.ini'; $out = $lines | ForEach-Object { if ($_ -match '^\s*fullscreen\s*=') { 'fullscreen = 0' } else { $_ } }; Set-Content -LiteralPath '%STAGING_DIR%\ps2x.ini' -Value $out -Encoding UTF8"
if errorlevel 1 (
    echo ERROR: Failed to generate %STAGING_DIR%\ps2x.ini.
    exit /b 1
)

(
    echo runtime_exe = %RUNTIME_NAME%
) > "%STAGING_DIR%\launcher.ini"
if errorlevel 1 (
    echo ERROR: Failed to write %STAGING_DIR%\launcher.ini.
    exit /b 1
)

(
    echo Ape Escape 3 Recomp
    echo ===================
    echo.
    echo No game data included.
    echo.
    echo To play, you must supply your own legally obtained Ape Escape 3 disc image
    echo ^(.iso^) or extracted game folder:
    echo   1. Run ape3_launcher.exe
    echo   2. In the Game tab, browse to your .iso file or extracted game folder
    echo   3. Click Play
) > "%STAGING_DIR%\README.txt"
if errorlevel 1 (
    echo ERROR: Failed to write %STAGING_DIR%\README.txt.
    exit /b 1
)

for /r "%STAGING_DIR%" %%F in (*) do (
    set "EXT=%%~xF"
    set "NAME=%%~nxF"
    if /i "!NAME!"=="SCUS_975.01" (
        echo ERROR: Refusing to package forbidden file: %%F
        exit /b 1
    )
    for %%E in (.iso .bin .elf .ps2 .padrec .gs .zst) do (
        if /i "!EXT!"=="%%E" (
            echo ERROR: Refusing to package forbidden extension !EXT!: %%F
            exit /b 1
        )
    )
)

echo Release staging files:
dir /b "%STAGING_DIR%"
exit /b 0
