# Does the interpreter's existing "no stalls" fast mode (PS2X_VU1_FAST=1) reproduce the exact outputs? (decides the design of the VU1 recompiler)
# Usage (repo root, no build needed):  powershell -File tools\fast_check.ps1 [-Tag fa] [-Corpus logs\vu1corpus_snow.bin]
# Every call of the corpus is replayed in fast mode and compared with the recorded exact result. Cycle counts are EXPECTED to differ (no stalls);
# what matters is vf/vi/acc/qpi/flags/mem/gif. Native blocks and kernels are off so the plain interpreter runs.
param([string]$Tag = "fa", [string]$Corpus = "")
$exe = ".\build\PS2Recomp\ps2xRuntime\ps2EntryRunner.exe"
foreach ($v in @("PS2X_VU1_REPLAY","PS2X_VU1_REPLAY_REPS","PS2X_VU1_KERNEL","PS2X_VU1_TSC","PS2X_VU_BLK_CHECK","PS2X_VU1_VERIFY","PS2X_VU1_FAST","PS2X_VU1_NATIVE","PS2X_VU1_CORPUS")) { Remove-Item "Env:$v" -ErrorAction SilentlyContinue }
if ($Corpus) { $env:PS2X_VU1_CORPUS = $Corpus }
function Run-One($n, $label, $envs) {
    foreach ($k in $envs.Keys) { Set-Item "Env:$k" $envs[$k] }
    $log = "logs\$Tag$n.log"
    Write-Host "== run $n ($label)"
    & $exe SCUS_975.01 2>&1 | Out-File -Encoding utf8 $log
    Copy-Item logs\vu1replay.txt "logs\vu1replay_$Tag$n.txt" -Force
    Get-Content logs\vu1replay.txt | Select-String -Pattern "^replayed=|^run_ms|^MISMATCH" | Select-Object -First 8 | ForEach-Object { Write-Host "   $($_.Line.Substring(0, [Math]::Min(300, $_.Line.Length)))" }
    foreach ($k in $envs.Keys) { Remove-Item "Env:$k" -ErrorAction SilentlyContinue }
}
Run-One 1 "exact interpreter reference (must be 0 mismatches)" @{ PS2X_VU1_REPLAY = "1"; PS2X_VU1_REPLAY_REPS = "1"; PS2X_VU1_KERNEL = "0" }
Run-One 2 "FAST mode (no stalls, immediate flags and Q)" @{ PS2X_VU1_REPLAY = "1"; PS2X_VU1_REPLAY_REPS = "1"; PS2X_VU1_KERNEL = "0"; PS2X_VU1_FAST = "1" }
Run-One 3 "FAST mode wall time, 5 reps" @{ PS2X_VU1_REPLAY = "1"; PS2X_VU1_REPLAY_REPS = "5"; PS2X_VU1_KERNEL = "0"; PS2X_VU1_FAST = "1" }
Write-Host "done: paste the lines above (or just say ready)."
