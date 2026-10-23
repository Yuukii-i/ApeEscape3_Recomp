<#
.SYNOPSIS
    Configures and builds the ps2EntryRunner target using CMake and Ninja.

.DESCRIPTION
    Safely builds only the ps2EntryRunner executable. Warns the developer about
    unity-build header modification risks before starting the compilation.

.PARAMETER Clean
    If specified, removes the build directory before configuring.

.PARAMETER Generator
    CMake generator to use. Defaults to "Ninja".
#>

[CmdletBinding()]
param(
    [switch]$Clean,
    [string]$Generator = "Ninja"
)

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Building ps2EntryRunner (Ape Escape 3 Recompilation)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Prominent Unity Build Warning
Write-Host @"
[IMPORTANT BUILD WARNING]
------------------------------------------------------------
Unity build is enabled in root CMakeLists.txt (UNITY_BUILD_BATCH_SIZE 64).
Modifying widely-included headers:
  - PS2Recomp/ps2xRuntime/include/runtime/ps2_runtime.h
  - PS2Recomp/ps2xRuntime/include/runtime/ps2_runtime_macros.h
  - PS2Recomp/ps2xRuntime/src/lib/Kernel/Stubs/Helpers/Support.h
WILL FORCE RECOMPILATION OF ALL 23,350+ FUNCTIONS IN recomp_source/!
Keep edits isolated to individual .cpp files or runner/ stubs whenever possible.
------------------------------------------------------------
"@ -ForegroundColor Yellow

if ($Clean) {
    if (Test-Path "build") {
        Write-Host "[clean] Removing build directory..." -ForegroundColor Yellow
        Remove-Item -Path "build" -Recurse -Force
    }
}

# 1. CMake Configuration
Write-Host "`n[1/2] Configuring CMake build tree..." -ForegroundColor Cyan
$cmakeConfigArgs = @("-B", "build", "-G", $Generator)
$configProcess = Start-Process -FilePath "cmake" -ArgumentList $cmakeConfigArgs -NoNewWindow -Wait -PassThru

if ($configProcess.ExitCode -ne 0) {
    Write-Error "CMake configuration failed with exit code: $($configProcess.ExitCode)"
    exit $configProcess.ExitCode
}

# 2. Build ps2EntryRunner target only
Write-Host "`n[2/2] Building ps2EntryRunner target..." -ForegroundColor Cyan
$cmakeBuildArgs = @("--build", "build", "--target", "ps2EntryRunner")
$buildProcess = Start-Process -FilePath "cmake" -ArgumentList $cmakeBuildArgs -NoNewWindow -Wait -PassThru

if ($buildProcess.ExitCode -ne 0) {
    Write-Error "CMake build failed with exit code: $($buildProcess.ExitCode)"
    exit $buildProcess.ExitCode
}

Write-Host "`n[SUCCESS] ps2EntryRunner built successfully." -ForegroundColor Green
Write-Host "Binary location: build\PS2Recomp\ps2xRuntime\ps2EntryRunner.exe" -ForegroundColor Green
