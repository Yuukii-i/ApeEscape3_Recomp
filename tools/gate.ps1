# gate.ps1 - one-command A/B gate for candidate build (perf + visual + optional tour + optional promote)
param(
    [string]$tag = 'g',
    [string]$candidate = 'build_avx2\PS2Recomp\ps2xRuntime\ps2EntryRunner_dev.exe',
    [string]$baseline = 'build_avx2\PS2Recomp\ps2xRuntime\base_overnight.exe',
    [ValidateSet('quick', 'full')][string]$level = 'quick',
    [ValidateSet('alt', 'base', 'cand')][string]$order = 'alt',
    [switch]$tour,
    [switch]$promote,
    [string]$extraEnv = ''
)

$ErrorActionPreference = 'Continue'
Set-Location C:\ApeEscape3_Recomp

$stdEnv = 'PS2X_RD_VIEW=1;PS2X_RD_TAKEOVER=1;PS2X_RD_2DFEEDBACK=1;PS2X_RD_2DLATE=1;PS2X_RD_FORCECLASSIC=0'
$fullEnv = if ($extraEnv) { "$stdEnv;$extraEnv" } else { $stdEnv }

# (1) Kill stray game processes and verify both exes exist
Stop-Process -Name ps2EntryRunner_dev, base_overnight -Force -ErrorAction SilentlyContinue
if (-not (Test-Path $candidate)) {
    Write-Error "Candidate exe missing: $candidate"
    exit 1
}
if (-not (Test-Path $baseline)) {
    Write-Error "Baseline exe missing: $baseline"
    exit 1
}

$reportDir = "logs\gate_$tag"
New-Item -ItemType Directory -Force $reportDir | Out-Null
$reportPath = "$reportDir\report.txt"

if ($level -eq 'quick') {
    $perfStages = @('castle_a', 'studio_d', 'toyhouse_a')
    $reps = 1
    $shotStages = @('castle_a', 'studio_d')
    $regThresh = 8.0
    $imp2Thresh = 9.0
    $imp1Thresh = 14.0
} else {
    $perfStages = @('castle_a', 'studio_c', 'studio_d', 'toyhouse_a', 'arabian_a', 'ciscocity_c')
    $reps = 3
    $shotStages = @('castle_a', 'studio_c', 'toyhouse_a', 'arabian_a', 'ciscocity_c', 'travel_a')
    $regThresh = 4.0
    $imp2Thresh = 3.0
    $imp1Thresh = 8.0
}

$perfOnly = $perfStages -join ','
$shotOnly = $shotStages -join ','
$failReasons = New-Object System.Collections.Generic.List[string]

function Get-Median([double[]]$vals) {
    $sorted = $vals | Sort-Object
    $n = $sorted.Count
    if ($n -eq 0) { return 0.0 }
    if ($n % 2 -eq 1) { return [double]$sorted[[int]($n / 2)] }
    return ([double]$sorted[$n / 2 - 1] + [double]$sorted[$n / 2]) / 2.0
}

function Parse-BenchFile([string]$path, [string[]]$expectedStages) {
    $res = @{}
    $crashed = $false
    if (-not (Test-Path $path)) { return @{ Data = $res; Crashed = $true } }
    $lines = Get-Content $path
    foreach ($line in $lines) {
        if ($line -match 'GAME EXITED') { $crashed = $true }
        if ($line -match '^(\S+)\s+fps=\s*([0-9.]+)\s+cpu/frame=\s*([0-9.]+)\s+ms') {
            $st = $matches[1]
            $res[$st] = @{
                Fps = [double]$matches[2]
                Cpu = [double]$matches[3]
            }
        }
    }
    foreach ($st in $expectedStages) {
        if (-not $res.ContainsKey($st) -or $res[$st].Fps -le 0) {
            $crashed = $true
        }
    }
    return @{ Data = $res; Crashed = $crashed }
}

# (2) Perf A/B: alternate baseline and candidate across reps
$baseFpsMap = @{}
$baseCpuMap = @{}
$candFpsMap = @{}
$candCpuMap = @{}
foreach ($st in $perfStages) {
    $baseFpsMap[$st] = New-Object System.Collections.Generic.List[double]
    $baseCpuMap[$st] = New-Object System.Collections.Generic.List[double]
    $candFpsMap[$st] = New-Object System.Collections.Generic.List[double]
    $candCpuMap[$st] = New-Object System.Collections.Generic.List[double]
}

for ($r = 1; $r -le $reps; $r++) {
    $baseFirst = ($order -eq 'base') -or ($order -eq 'alt' -and ($r % 2 -eq 1))
    $runs = if ($baseFirst) {
        @(
            @{ Role = 'baseline'; Tag = "gate_${tag}_b$r"; Exe = $baseline; FpsMap = $baseFpsMap; CpuMap = $baseCpuMap },
            @{ Role = 'candidate'; Tag = "gate_${tag}_c$r"; Exe = $candidate; FpsMap = $candFpsMap; CpuMap = $candCpuMap }
        )
    } else {
        @(
            @{ Role = 'candidate'; Tag = "gate_${tag}_c$r"; Exe = $candidate; FpsMap = $candFpsMap; CpuMap = $candCpuMap },
            @{ Role = 'baseline'; Tag = "gate_${tag}_b$r"; Exe = $baseline; FpsMap = $baseFpsMap; CpuMap = $baseCpuMap }
        )
    }

    foreach ($run in $runs) {
        & powershell -NoProfile -ExecutionPolicy Bypass -File tools\stage_bench.ps1 -tag $run.Tag -only $perfOnly -extraEnv $fullEnv -exe $run.Exe | Out-Null
        $parsed = Parse-BenchFile "logs\$($run.Tag)_bench.txt" $perfStages
        if ($parsed.Crashed) { $failReasons.Add("$($run.Role) crash/exit in $($run.Tag)") }
        foreach ($st in $perfStages) {
            if ($parsed.Data.ContainsKey($st)) {
                $run.FpsMap[$st].Add($parsed.Data[$st].Fps)
                $run.CpuMap[$st].Add($parsed.Data[$st].Cpu)
            }
        }
    }
}

$perfRows = New-Object System.Collections.Generic.List[string]
$perfRows.Add(("{0,-12} {1,8} {2,8} {3,8} | {4,8} {5,8} {6,8}" -f 'stage', 'base_fps', 'cand_fps', 'fps_%', 'base_cpu', 'cand_cpu', 'cpu_%'))

$imp2Count = 0
$imp1Hit = $false

foreach ($st in $perfStages) {
    $bf = Get-Median $baseFpsMap[$st].ToArray()
    $cf = Get-Median $candFpsMap[$st].ToArray()
    $bc = Get-Median $baseCpuMap[$st].ToArray()
    $cc = Get-Median $candCpuMap[$st].ToArray()

    $fpsDelta = if ($bf -gt 0) { (($cf - $bf) / $bf) * 100.0 } else { 0.0 }
    $cpuDelta = if ($bc -gt 0) { (($cc - $bc) / $bc) * 100.0 } else { 0.0 }

    if ($bf -le 0 -or $cf -le 0) {
        $failReasons.Add("missing perf for $st")
    } else {
        if ($fpsDelta -lt -$regThresh) {
            $failReasons.Add(("{0} fps {1:+0.0;-0.0;0.0}%" -f $st, $fpsDelta))
        }
        if ($cpuDelta -gt $regThresh) {
            $failReasons.Add(("{0} cpu {1:+0.0;-0.0;0.0}%" -f $st, $cpuDelta))
        }
        if ($fpsDelta -ge $imp2Thresh -or $cpuDelta -le -$imp2Thresh) { $imp2Count++ }
        if ($fpsDelta -ge $imp1Thresh -or $cpuDelta -le -$imp1Thresh) { $imp1Hit = $true }
    }

    $perfRows.Add(("{0,-12} {1,8:N1} {2,8:N1} {3,7:+0.0;-0.0;0.0}% | {4,8:N1} {5,8:N1} {6,7:+0.0;-0.0;0.0}%" -f $st, $bf, $cf, $fpsDelta, $bc, $cc, $cpuDelta))
}

$improved = ($imp2Count -ge 2) -or $imp1Hit

# (3) Visual: warp_shot baseline twice, candidate once
$vb1Tag = "gate_${tag}_vb1"
$vb2Tag = "gate_${tag}_vb2"
$vc1Tag = "gate_${tag}_vc1"

$vb1Out = & powershell -NoProfile -ExecutionPolicy Bypass -File tools\warp_shot.ps1 -tag $vb1Tag -only $shotOnly -extraEnv $fullEnv -exe $baseline 2>&1
$vb2Out = & powershell -NoProfile -ExecutionPolicy Bypass -File tools\warp_shot.ps1 -tag $vb2Tag -only $shotOnly -extraEnv $fullEnv -exe $baseline 2>&1
$vc1Out = & powershell -NoProfile -ExecutionPolicy Bypass -File tools\warp_shot.ps1 -tag $vc1Tag -only $shotOnly -extraEnv $fullEnv -exe $candidate 2>&1

if (($vb1Out -join "`n") -match 'GAME EXITED|exit code' -or ($vb2Out -join "`n") -match 'GAME EXITED|exit code') {
    $failReasons.Add('baseline shot crash/exit')
}
if (($vc1Out -join "`n") -match 'GAME EXITED|exit code') {
    $failReasons.Add('candidate shot crash/exit')
}

$visualRows = New-Object System.Collections.Generic.List[string]
foreach ($st in $shotStages) {
    $p1 = "logs\shots\${vb1Tag}_${st}.png"
    $p2 = "logs\shots\${vb2Tag}_${st}.png"
    $p3 = "logs\shots\${vc1Tag}_${st}.png"
    $cmpOut = & python tools\gate_compare.py $p1 $p2 $p3 2>&1
    $cmpExit = $LASTEXITCODE
    $cmpLine = ($cmpOut | Select-Object -Last 1)
    $visualRows.Add([string]$cmpLine)
    if ($cmpExit -ne 0) {
        $failReasons.Add("visual $st")
    }
}

# (4) Optional tour
function Get-TourAlive([string]$path) {
    if (-not (Test-Path $path)) { return @{ Alive = -1; Crashed = $true } }
    $lines = Get-Content $path
    $crashed = $false
    $alive = 0
    foreach ($l in $lines) {
        if ($l -match 'GAME EXITED') { $crashed = $true }
        if ($l -match 'alive=True') { $alive++ }
    }
    return @{ Alive = $alive; Crashed = $crashed }
}

$tourLine = 'tour: skipped'
if ($tour) {
    $baseTourRef = 'logs\gate_baseline_tour.txt'
    if (-not (Test-Path $baseTourRef)) {
        & powershell -NoProfile -ExecutionPolicy Bypass -File tools\warp_tour.ps1 -tag 'gate_baseline_tour' -extraEnv $fullEnv -exe $baseline | Out-Null
        if (Test-Path 'logs\gate_baseline_tour_summary.txt') {
            Copy-Item 'logs\gate_baseline_tour_summary.txt' $baseTourRef -Force
        }
    }
    $candTourTag = "gate_${tag}_tour"
    & powershell -NoProfile -ExecutionPolicy Bypass -File tools\warp_tour.ps1 -tag $candTourTag -extraEnv $fullEnv -exe $candidate | Out-Null
    $baseTour = Get-TourAlive $baseTourRef
    $candTour = Get-TourAlive "logs\${candTourTag}_summary.txt"
    $tourLine = "tour: candidate_alive=$($candTour.Alive) baseline_alive=$($baseTour.Alive) crashed=$($candTour.Crashed)"
    if ($candTour.Crashed) {
        $failReasons.Add('tour crash/exit')
    } elseif ($candTour.Alive -lt $baseTour.Alive) {
        $failReasons.Add("tour alive $($candTour.Alive)<$($baseTour.Alive)")
    }
}

# (5) Write report and verdict
$impStr = if ($improved) { 'yes' } else { 'no' }
$passed = ($failReasons.Count -eq 0)
$verdictLine = if ($passed) {
    "GATE PASS | improved=$impStr"
} else {
    $reason = ($failReasons | Select-Object -Unique) -join '; '
    "GATE FAIL $reason | improved=$impStr"
}

$report = New-Object System.Collections.Generic.List[string]
$report.Add("gate tag=$tag level=$level order=$order reg=${regThresh}% imp2=${imp2Thresh}% imp1=${imp1Thresh}% candidate=$candidate baseline=$baseline")
$report.Add("--- PERF (median across $reps rep(s), order=$order, regression limit ${regThresh}%, improved >=2@${imp2Thresh}% or >=1@${imp1Thresh}%) ---")
foreach ($r in $perfRows) { $report.Add($r) }
$report.Add("--- VISUAL ---")
foreach ($v in $visualRows) { $report.Add($v) }
$report.Add("--- TOUR ---")
$report.Add($tourLine)
$report.Add($verdictLine)
Set-Content -Path $reportPath -Value $report

if ($promote -and $passed -and $improved) {
    Copy-Item -Path $candidate -Destination $baseline -Force
    $candPdb = [System.IO.Path]::ChangeExtension($candidate, '.pdb')
    $basePdb = [System.IO.Path]::ChangeExtension($baseline, '.pdb')
    if (Test-Path $candPdb) {
        Copy-Item -Path $candPdb -Destination $basePdb -Force
    }
}

Write-Output $verdictLine
if ($passed) { exit 0 } else { exit 1 }
