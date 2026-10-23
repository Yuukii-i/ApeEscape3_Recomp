<#
.SYNOPSIS
    Runs a non-destructive dry-run of the PS2 static recompiler into a temporary folder.

.DESCRIPTION
    Clones config.toml to a temporary configuration with an isolated output directory in $env:TEMP,
    executes ps2_recomp.exe, and compares generated output against the current recomp_source/ directory.
    Never modifies or writes into recomp_source/.

.PARAMETER ConfigPath
    Path to recompiler configuration TOML file. Defaults to "config.toml".

.PARAMETER RecompExe
    Path to ps2_recomp.exe executable. Defaults to "ps2_recomp.exe".

.PARAMETER KeepTemp
    If specified, preserves the temporary output folder after comparison.
#>

[CmdletBinding()]
param(
    [string]$ConfigPath = "config.toml",
    [string]$RecompExe = "ps2_recomp.exe",
    [switch]$KeepTemp
)

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " PS2Recomp Dry-Run Regeneration Check" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Validation of required files
if (-not (Test-Path $RecompExe)) {
    Write-Error "Recompiler executable not found at: $RecompExe"
    exit 1
}

if (-not (Test-Path $ConfigPath)) {
    Write-Error "Configuration TOML file not found at: $ConfigPath"
    exit 1
}

$elfPath = "SCUS_975.01"
if (-not (Test-Path $elfPath)) {
    Write-Error "Target ELF not found at: $elfPath. Ensure SCUS_975.01 is in the repository root."
    exit 1
}

# 2. Check disk space on temp drive (require >= 1.0 GB)
$tempDrive = [System.IO.Path]::GetPathRoot([System.IO.Path]::GetFullPath($env:TEMP))
$driveInfo = [System.IO.DriveInfo]::new($tempDrive)
$freeGb = [math]::Round($driveInfo.AvailableFreeSpace / 1GB, 2)

Write-Host "[info] Free space on $tempDrive : $freeGb GB"
if ($freeGb -lt 1.0) {
    Write-Error "Insufficient disk space on $tempDrive ($freeGb GB available). At least 1.0 GB is required for dry-run output."
    exit 1
}

# 3. Create isolated temporary directory
$timestamp = [DateTime]::UtcNow.ToString("yyyyMMdd_HHmmss")
$tempOutputDir = Join-Path $env:TEMP ("ps2x_dryrun_" + $timestamp)
New-Item -ItemType Directory -Path $tempOutputDir -Force | Out-Null
Write-Host "[info] Temporary output directory: $tempOutputDir"

try {
    # 4. Clone config.toml with changed output path
    $configContent = Get-Content -Raw -Path $ConfigPath
    $sanitizedOutputDir = $tempOutputDir.Replace('\', '/')
    $modifiedConfig = $configContent -replace 'output\s*=\s*"recomp_source"', "output = `"$sanitizedOutputDir`""

    $tempConfigPath = Join-Path $env:TEMP ("ps2x_dryrun_config_" + $timestamp + ".toml")
    Set-Content -Path $tempConfigPath -Value $modifiedConfig -Encoding UTF8
    Write-Host "[info] Temporary config created at: $tempConfigPath"

    # 5. Execute recompiler targeting temp directory
    Write-Host "[info] Running recompiler into temp directory..." -ForegroundColor Yellow
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $process = Start-Process -FilePath (Resolve-Path $RecompExe) -ArgumentList "`"$tempConfigPath`"" -NoNewWindow -Wait -PassThru
    $sw.Stop()

    if ($process.ExitCode -ne 0) {
        Write-Error "Recompiler exited with non-zero exit code: $($process.ExitCode)"
        exit $process.ExitCode
    }
    Write-Host "[info] Recompilation finished in $([math]::Round($sw.Elapsed.TotalSeconds, 2)) seconds." -ForegroundColor Green

    # 6. Compare generated files against recomp_source/
    $currentDir = "recomp_source"
    if (-not (Test-Path $currentDir)) {
        Write-Warning "Current recomp_source/ folder does not exist. Cannot perform diff comparison."
        exit 0
    }

    Write-Host "`n[info] Comparing generated output against $currentDir/..." -ForegroundColor Cyan

    $tempFiles = Get-ChildItem -Path $tempOutputDir -File
    $currFiles = Get-ChildItem -Path $currentDir -File

    Write-Host "  - Files in newly generated output : $($tempFiles.Count)"
    Write-Host "  - Files in current recomp_source/ : $($currFiles.Count)"

    $currFileMap = @{}
    foreach ($f in $currFiles) {
        $currFileMap[$f.Name] = $f
    }

    $differingFiles = [System.Collections.Generic.List[string]]::new()
    $newFiles = [System.Collections.Generic.List[string]]::new()

    foreach ($f in $tempFiles) {
        if (-not $currFileMap.ContainsKey($f.Name)) {
            $newFiles.Add($f.Name)
            continue
        }

        $currFile = $currFileMap[$f.Name]
        if ($f.Length -ne $currFile.Length) {
            $differingFiles.Add($f.Name)
            continue
        }

        # Compare contents if lengths match
        $tempBytes = [System.IO.File]::ReadAllBytes($f.FullName)
        $currBytes = [System.IO.File]::ReadAllBytes($currFile.FullName)
        $isEqual = $true
        for ($i = 0; $i -lt $tempBytes.Length; $i++) {
            if ($tempBytes[$i] -ne $currBytes[$i]) {
                $isEqual = $false
                break
            }
        }
        if (-not $isEqual) {
            $differingFiles.Add($f.Name)
        }
    }

    $tempFileMap = @{}
    foreach ($f in $tempFiles) {
        $tempFileMap[$f.Name] = $true
    }
    $missingFiles = [System.Collections.Generic.List[string]]::new()
    foreach ($f in $currFiles) {
        if (-not $tempFileMap.ContainsKey($f.Name)) {
            $missingFiles.Add($f.Name)
        }
    }

    Write-Host "`n============================================================" -ForegroundColor Cyan
    Write-Host " DRY-RUN COMPARISON REPORT" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "Identical files : $($tempFiles.Count - $differingFiles.Count - $newFiles.Count)" -ForegroundColor Green
    Write-Host "Differing files : $($differingFiles.Count)" -ForegroundColor Yellow
    Write-Host "New files       : $($newFiles.Count)" -ForegroundColor Yellow
    Write-Host "Missing files   : $($missingFiles.Count)" -ForegroundColor Yellow

    if ($differingFiles.Count -gt 0) {
        Write-Host "`nDiffering files list:" -ForegroundColor Yellow
        foreach ($d in $differingFiles) {
            Write-Host "  [MODIFIED] $d"
        }
    }

    if ($missingFiles.Count -gt 0) {
        Write-Host "`nFiles present in current recomp_source/ but omitted by recompiler:" -ForegroundColor Yellow
        foreach ($m in $missingFiles) {
            Write-Host "  [EXTRA] $m"
        }
    }

    Write-Host "`n[summary] Safe dry-run complete. No changes were made to recomp_source/." -ForegroundColor Green
}
finally {
    if (Test-Path $tempConfigPath) {
        Remove-Item -Path $tempConfigPath -Force -ErrorAction SilentlyContinue
    }
    if ($KeepTemp) {
        Write-Host "[info] Preserving temporary directory at: $tempOutputDir" -ForegroundColor Yellow
    } else {
        Write-Host "[info] Cleaning up temporary directory: $tempOutputDir"
        Remove-Item -Path $tempOutputDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
