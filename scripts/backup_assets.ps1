<#
.SYNOPSIS
    Backs up proprietary non-committable assets to $env:PS2X_BACKUP_DIR with a SHA-256 manifest.

.DESCRIPTION
    Scans for copyright-protected assets (SCUS_975.01, ISO files, extracted IRX modules),
    generates a manifest.sha256 file, and copies the assets to the designated backup folder.
    Fails with a clear message if $env:PS2X_BACKUP_DIR is not set.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Proprietary Asset Backup Tool" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Validate environment variable
$backupDir = $env:PS2X_BACKUP_DIR
if ([string]::IsNullOrWhiteSpace($backupDir)) {
    Write-Host @"
[ERROR] Environment variable PS2X_BACKUP_DIR is not set!

Please set the destination backup directory before running this script.
For example (PowerShell):
    `$env:PS2X_BACKUP_DIR = "D:\Backups\ApeEscape3_Assets"
    .\scripts\backup_assets.ps1
"@ -ForegroundColor Red
    exit 1
}

$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Write-Host "Source Repository : $repoRoot"
Write-Host "Backup Destination: $backupDir"

if (-not (Test-Path $backupDir)) {
    Write-Host "[info] Creating backup directory: $backupDir"
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
}

# 2. Identify candidate proprietary / non-committable files
$candidatePatterns = @(
    "SCUS_975.01",
    "*.iso",
    "DATA.BIN",
    "tools\iop\*.irx",
    "tools\iop\*.bin",
    "build\PS2Recomp\ps2xRuntime\*.iso"
)

$filesToBackup = [System.Collections.Generic.List[System.IO.FileInfo]]::new()
foreach ($pat in $candidatePatterns) {
    $matched = Get-ChildItem -Path (Join-Path $repoRoot $pat) -File -ErrorAction SilentlyContinue
    if ($matched) {
        foreach ($m in $matched) {
            # Deduplicate by full path
            $alreadyAdded = $false
            foreach ($existing in $filesToBackup) {
                if ($existing.FullName -eq $m.FullName) {
                    $alreadyAdded = $true
                    break
                }
            }
            if (-not $alreadyAdded) {
                $filesToBackup.Add($m)
            }
        }
    }
}

if ($filesToBackup.Count -eq 0) {
    Write-Warning "No candidate proprietary asset files found to back up."
    exit 0
}

Write-Host "`n[info] Found $($filesToBackup.Count) proprietary asset file(s) to back up:"

$manifestLines = [System.Collections.Generic.List[string]]::new()
$sha256 = [System.Security.Cryptography.SHA256]::Create()

foreach ($file in $filesToBackup) {
    $relPath = [System.IO.Path]::GetRelativePath($repoRoot, $file.FullName)
    Write-Host "  - Processing: $relPath ($([math]::Round($file.Length / 1MB, 2)) MB)..." -NoNewline

    # Compute SHA-256
    $stream = [System.IO.File]::OpenRead($file.FullName)
    $hashBytes = $sha256.ComputeHash($stream)
    $stream.Dispose()
    $hashHex = [System.BitConverter]::ToString($hashBytes).Replace('-', '').ToLowerInvariant()

    $manifestLines.Add("$hashHex *$relPath")

    # Determine destination path
    $destFile = Join-Path $backupDir $relPath
    $destFileDir = [System.IO.Path]::GetDirectoryName($destFile)
    if (-not (Test-Path $destFileDir)) {
        New-Item -ItemType Directory -Path $destFileDir -Force | Out-Null
    }

    Copy-Item -Path $file.FullName -Destination $destFile -Force
    Write-Host " [COPIED]" -ForegroundColor Green
}

$sha256.Dispose()

# Write manifest.sha256
$manifestPath = Join-Path $backupDir "manifest.sha256"
Set-Content -Path $manifestPath -Value $manifestLines -Encoding UTF8
Write-Host "`n[SUCCESS] All assets backed up successfully!" -ForegroundColor Green
Write-Host "Manifest written to: $manifestPath" -ForegroundColor Green
