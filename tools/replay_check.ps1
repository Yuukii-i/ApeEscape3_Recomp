# Corpus replay checks for the VU1 native path (no gameplay needed, about a minute in total).
# Usage (from the repo root, after tools\build.bat):  powershell -File tools\replay_check.ps1 [-Tag rz]
# Runs, in order:  1 exactness of the hash tables (BLK_CHECK)   2 timing profile with kernels   3 verifier against the interpreter   4/5 true wall time (no TSC), kernels on/off
# Other microcode image: -Corpus logs/vu1corpus_snow.bin -Image 38aed21fa6906cf0 (the image hash is listed in the replay summary: 'image gen= hash=').
# Logs: logs\<Tag>1.log .. logs\<Tag>3.log, replay summaries copied to logs\vu1replay_<Tag>1.txt ..
param([string]$Tag = "rz", [string]$Corpus = "", [string]$Image = "")

$exe = ".\build\PS2Recomp\ps2xRuntime\ps2EntryRunner.exe"
$vars = @("PS2X_VU1_REPLAY", "PS2X_VU1_REPLAY_REPS", "PS2X_VU1_KERNEL", "PS2X_VU1_TSC", "PS2X_VU_BLK_CHECK", "PS2X_VU1_VERIFY", "PS2X_VU1_XG_HOT", "PS2X_VU1_FUSE", "PS2X_VU1_CORPUS", "PS2X_VU1_REPLAY_IMAGE")

function Run-One($n, $label, $envs) {
    foreach ($v in $vars) { Remove-Item "Env:$v" -ErrorAction SilentlyContinue }
    foreach ($k in $envs.Keys) { Set-Item "Env:$k" $envs[$k] }
    if ($Corpus) { $env:PS2X_VU1_CORPUS = $Corpus }
    if ($Image) { $env:PS2X_VU1_REPLAY_IMAGE = $Image }
    $log = "logs\$Tag$n.log"
    Write-Host "== run $n ($label) -> $log"
    & $exe SCUS_975.01 2>&1 | Out-File -Encoding utf8 $log
    Copy-Item logs\vu1replay.txt "logs\vu1replay_$Tag$n.txt" -Force
    $rep = Get-Content logs\vu1replay.txt
    $rep | Select-String -Pattern "^replayed=|^run_ms|^kernels|^slow-pair causes|^state split|^miss pcs|^noStart pcs|^declined pcs|^xg kernel" | ForEach-Object { Write-Host "   $($_.Line.Substring(0, [Math]::Min(230, $_.Line.Length)))" }
    $mm = (Select-String -Path $log -Pattern "exit-hash MISMATCH" -SimpleMatch).Count
    $gv = Select-String -Path $log -Pattern "gv summary" | Select-Object -Last 1
    Write-Host "   exit-hash MISMATCH lines: $mm"
    if ($gv) { Write-Host "   $($gv.Line)" }
}

Run-One 1 "hash tables exact (BLK_CHECK)" @{ PS2X_VU1_REPLAY = "1"; PS2X_VU1_REPLAY_REPS = "1"; PS2X_VU1_KERNEL = "1"; PS2X_VU1_TSC = "1"; PS2X_VU_BLK_CHECK = "1" }
Run-One 2 "timing profile, kernels on, 3 reps" @{ PS2X_VU1_REPLAY = "1"; PS2X_VU1_REPLAY_REPS = "3"; PS2X_VU1_KERNEL = "1"; PS2X_VU1_TSC = "1" }
Run-One 3 "verifier vs interpreter" @{ PS2X_VU1_REPLAY = "1"; PS2X_VU1_REPLAY_REPS = "1"; PS2X_VU1_KERNEL = "1"; PS2X_VU1_VERIFY = "3"; PS2X_VU_BLK_CHECK = "1" }
Run-One 4 "wall time, kernels on, no TSC counters, 5 reps" @{ PS2X_VU1_REPLAY = "1"; PS2X_VU1_REPLAY_REPS = "5"; PS2X_VU1_KERNEL = "1" }
Run-One 5 "wall time, kernels off (hot blocks only), no TSC counters, 5 reps" @{ PS2X_VU1_REPLAY = "1"; PS2X_VU1_REPLAY_REPS = "5"; PS2X_VU1_KERNEL = "0" }
Write-Host "done: paste me the lines above (or just say ready)."
