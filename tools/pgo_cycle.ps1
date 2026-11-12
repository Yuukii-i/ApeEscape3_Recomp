# tools/pgo_cycle.ps1 - PGO GEN -> train (pad replay to the shop, then normal window close) -> USE.
# Usage: pwsh -NoProfile -File tools\pgo_cycle.ps1 [-TrainSeconds 90]
# Result: build\PS2Recomp\ps2xRuntime\ps2EntryRunner_pgo.exe. Afterwards tools\build_dev.bat resets the build folder to dev.
param([int]$TrainSeconds = 90, [string]$Pad = "logs\selftest.padrec")
$ErrorActionPreference = "Continue"
Set-Location C:\ApeEscape3_Recomp
$bin = "build\PS2Recomp\ps2xRuntime"

function Build([string]$mode) {
    $cmd = "call `"C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat`" >nul 2>&1 && set VULKAN_SDK=C:\VulkanSDK\1.4.363.0&& cmake -B build -DPS2X_DEV_BUILD=OFF -DPS2X_PGO=$mode >nul && cmake --build build --config Release --target ps2EntryRunner --parallel %NUMBER_OF_PROCESSORS%"
    $t = Get-Date
    $o = cmd /c $cmd 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        Write-Host "PGO $mode BUILD FAIL"
        ($o -split "`n" | Select-String -Pattern 'error|fatal' | Select-Object -First 15) | ForEach-Object { Write-Host $_ }
        exit 1
    }
    Write-Host ("PGO {0} BUILD OK {1:N0}s" -f $mode, ((Get-Date) - $t).TotalSeconds)
}

Build "GEN"
Get-ChildItem "$bin\*.pgc" -ErrorAction SilentlyContinue | Remove-Item -Force
if (-not (Test-Path "$bin\pgort140.dll")) {
    $src = Get-ChildItem "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC\*\bin\Hostx64\x64\pgort140.dll" | Select-Object -Last 1
    if ($src) { Copy-Item $src.FullName "$bin\pgort140.dll" }
}

Get-ChildItem env:PS2X_* -ErrorAction SilentlyContinue | ForEach-Object { Remove-Item "env:$($_.Name)" -Force }
$env:PS2X_GS_ASYNC = "1"; $env:PS2X_VIF1_ASYNC = "1"; $env:PS2X_GS_VULKAN = "1"; $env:PS2X_VU1_KERNEL = "1"
$env:PS2X_PRESENT_ASYNC = "1"; $env:PS2X_PRESENT_GPU = "1"; $env:PS2X_PAD_PLAY = $Pad; $env:PS2X_PAD_PLAY_HOLD = "1"
$err = "logs\pgo_train.err"
$proc = Start-Process -FilePath "$bin\ps2EntryRunner_pgogen.exe" -ArgumentList "SCUS_975.01" -WorkingDirectory "C:\ApeEscape3_Recomp" -RedirectStandardOutput "logs\pgo_train.out" -RedirectStandardError $err -PassThru
$sw = [Diagnostics.Stopwatch]::StartNew(); $started = $false
while ($sw.Elapsed.TotalSeconds -lt 600 -and -not $proc.HasExited) {
    try { $fs = [IO.FileStream]::new($err, 'Open', 'Read', 'ReadWrite'); $sr = [IO.StreamReader]::new($fs); $txt = $sr.ReadToEnd(); $sr.Close(); $fs.Close(); if ($txt -match '\[bench\] START') { $started = $true; break } } catch {}
    Start-Sleep -Seconds 2
}
if (-not $started) { Write-Host "TRAIN FAIL: shop marker not reached"; if (-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force }; exit 1 }
Start-Sleep -Seconds $TrainSeconds
$null = $proc.CloseMainWindow()
if (-not $proc.WaitForExit(60000)) { Write-Host "TRAIN WARN: no normal exit, killing"; Stop-Process -Id $proc.Id -Force }
Start-Sleep -Seconds 2
$pgc = Get-ChildItem "$bin\*.pgc" -ErrorAction SilentlyContinue
if (-not $pgc) { Write-Host "TRAIN FAIL: no .pgc written"; exit 1 }
Write-Host ("TRAIN OK pgc={0}" -f (($pgc | ForEach-Object Name) -join ','))

Build "USE"
Write-Host "PGO DONE $bin\ps2EntryRunner_pgo.exe"
