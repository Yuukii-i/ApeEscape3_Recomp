<#
.SYNOPSIS
    Runs ps2EntryRunner from build\PS2Recomp\ps2xRuntime with a bounded timeout and timestamped logging.

.DESCRIPTION
    Launches ps2EntryRunner.exe with the specified ELF executable and arguments.
    Enforces a strict execution timeout (default: 15s) to prevent hanging,
    and tees both stdout and stderr simultaneously to console and a timestamped log file.

.PARAMETER TimeoutSeconds
    Maximum duration in seconds to let the process run before stopping it. Defaults to 15.

.PARAMETER ElfPath
    Path to PS2 ELF executable. Defaults to "SCUS_975.01" in the repository root.

.PARAMETER AdditionalArgs
    Additional arguments passed to ps2EntryRunner.exe.

.PARAMETER CheckOnly
    If specified, performs a quick 2-second sanity run to verify the executable starts.
#>

[CmdletBinding()]
param(
    [int]$TimeoutSeconds = 15,
    [string]$ElfPath = "SCUS_975.01",
    [string[]]$AdditionalArgs = @(),
    [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"

if ($CheckOnly) {
    $TimeoutSeconds = 2
}

$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName
$runnerDir = Join-Path $repoRoot "build\PS2Recomp\ps2xRuntime"
$runnerExe = Join-Path $runnerDir "ps2EntryRunner.exe"

if (-not (Test-Path $runnerExe)) {
    Write-Error "ps2EntryRunner executable not found at: $runnerExe. Build it first with scripts\build.ps1."
    exit 1
}

$resolvedElf = $ElfPath
if (-not [System.IO.Path]::IsPathRooted($resolvedElf)) {
    $resolvedElf = Join-Path $repoRoot $ElfPath
}

if (-not (Test-Path $resolvedElf)) {
    Write-Error "Target ELF not found at: $resolvedElf"
    exit 1
}

# Ensure logs directory exists
$logsDir = Join-Path $repoRoot "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
}

$timestamp = [DateTime]::UtcNow.ToString("yyyyMMdd_HHmmss")
$logFile = Join-Path $logsDir ("run_" + $timestamp + ".log")

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Running ps2EntryRunner (Timeout: ${TimeoutSeconds}s)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Working Directory : $runnerDir"
Write-Host "Binary            : $runnerExe"
Write-Host "ELF Executable    : $resolvedElf"
Write-Host "Log File          : $logFile"
Write-Host "------------------------------------------------------------"

$psi = [System.Diagnostics.ProcessStartInfo]::new()
$psi.FileName = $runnerExe
$psi.WorkingDirectory = $runnerDir

# Build argument string
$argList = [System.Collections.Generic.List[string]]::new()
$argList.Add("`"$resolvedElf`"")
foreach ($arg in $AdditionalArgs) {
    $argList.Add($arg)
}
$psi.Arguments = [string]::Join(" ", $argList)

$tempOut = [System.IO.Path]::GetTempFileName()
$tempErr = [System.IO.Path]::GetTempFileName()

$process = Start-Process -FilePath $runnerExe -WorkingDirectory $runnerDir -ArgumentList ($argList -join " ") -RedirectStandardOutput $tempOut -RedirectStandardError $tempErr -PassThru

$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$logWriter = [System.IO.StreamWriter]::new($logFile, $false, [System.Text.Encoding]::UTF8)

$outFs = [System.IO.FileStream]::new($tempOut, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
$errFs = [System.IO.FileStream]::new($tempErr, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
$outReader = [System.IO.StreamReader]::new($outFs, [System.Text.Encoding]::UTF8)
$errReader = [System.IO.StreamReader]::new($errFs, [System.Text.Encoding]::UTF8)

try {
    while (-not $process.HasExited -and $stopwatch.Elapsed.TotalSeconds -lt $TimeoutSeconds) {
        while (-not $outReader.EndOfStream) {
            $line = $outReader.ReadLine()
            [System.Console]::Out.WriteLine($line)
            $logWriter.WriteLine($line)
        }
        while (-not $errReader.EndOfStream) {
            $line = $errReader.ReadLine()
            [System.Console]::Error.WriteLine($line)
            $logWriter.WriteLine($line)
        }
        $logWriter.Flush()
        Start-Sleep -Milliseconds 50
    }

    $stopwatch.Stop()

    if (-not $process.HasExited) {
        Write-Host "`n[timeout] Bounded execution timeout (${TimeoutSeconds}s) expired. Stopping process..." -ForegroundColor Yellow
        try {
            $process.Kill($true)
            $process.WaitForExit(3000)
        } catch {
            # Process may have already terminated
        }
        Write-Host "[timeout] Process terminated after $([math]::Round($stopwatch.Elapsed.TotalSeconds, 2))s." -ForegroundColor Yellow
    } else {
        Write-Host "`n[info] Process completed in $([math]::Round($stopwatch.Elapsed.TotalSeconds, 2))s with exit code: $($process.ExitCode)." -ForegroundColor Green
    }

    # Flush any trailing lines
    while (-not $outReader.EndOfStream) {
        $line = $outReader.ReadLine()
        [System.Console]::Out.WriteLine($line)
        $logWriter.WriteLine($line)
    }
    while (-not $errReader.EndOfStream) {
        $line = $errReader.ReadLine()
        [System.Console]::Error.WriteLine($line)
        $logWriter.WriteLine($line)
    }
    $logWriter.Flush()
}
finally {
    $outReader.Dispose()
    $errReader.Dispose()
    $outFs.Dispose()
    $errFs.Dispose()
    $logWriter.Dispose()
    Remove-Item $tempOut, $tempErr -Force -ErrorAction SilentlyContinue
}
$process.Dispose()

Write-Host "Execution log captured at: $logFile" -ForegroundColor Green
