# tools/ab.ps1 - A/B benchmarking runner
# Runs ExeA and ExeB alternately (A B A B ...) with deterministic env and pad playback.
param(
    [string]$ExeA = "build\PS2Recomp\ps2xRuntime\ps2EntryRunner_dev.exe",
    [string]$ExeB = "build\PS2Recomp\ps2xRuntime\ps2EntryRunner_dev.exe",
    [hashtable]$EnvA = @{},
    [hashtable]$EnvB = @{},
    [string]$Pad = "logs\selftest.padrec",
    [int]$Seconds = 20,
    [int]$Rounds = 2,
    [string]$Tag = "bench",
    [double]$Fps = 60
)

$ErrorActionPreference = "Continue"

if (-not ([System.Management.Automation.PSTypeName]'Win.Thr').Type) {
    Add-Type -Namespace Win -Name Thr -MemberDefinition @'
[System.Runtime.InteropServices.DllImport("kernel32.dll")] public static extern System.IntPtr OpenThread(uint access, bool inherit, uint id);
[System.Runtime.InteropServices.DllImport("kernel32.dll")] public static extern int GetThreadDescription(System.IntPtr h, out System.IntPtr desc);
[System.Runtime.InteropServices.DllImport("kernel32.dll")] public static extern bool CloseHandle(System.IntPtr h);
[System.Runtime.InteropServices.DllImport("kernel32.dll")] public static extern System.IntPtr LocalFree(System.IntPtr h);
'@
}

function ThreadName([int]$id) {
    try {
        $h = [Win.Thr]::OpenThread(0x800, $false, [uint32]$id)   # THREAD_QUERY_LIMITED_INFORMATION
        if ($h -eq [IntPtr]::Zero) { return "" }
        $d = [IntPtr]::Zero
        $name = ""
        if ([Win.Thr]::GetThreadDescription($h, [ref]$d) -ge 0 -and $d -ne [IntPtr]::Zero) {
            $name = [System.Runtime.InteropServices.Marshal]::PtrToStringUni($d)
            [void][Win.Thr]::LocalFree($d)
        }
        [void][Win.Thr]::CloseHandle($h)
        return $name
    } catch { return "" }
}

function Snap($proc) {
    $proc.Refresh()
    $h = @{}
    foreach ($t in $proc.Threads) {
        try { $h[$t.Id] = $t.TotalProcessorTime.TotalMilliseconds } catch {}
    }
    return $h
}

function Get-Median([double[]]$values) {
    if (-not $values -or $values.Count -eq 0) { return 0.0 }
    $sorted = $values | Sort-Object
    $count = $sorted.Count
    $mid = [math]::Floor($count / 2)
    if ($count % 2 -eq 1) {
        return $sorted[$mid]
    } else {
        return ($sorted[$mid - 1] + $sorted[$mid]) / 2.0
    }
}

if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
}

function Run-Side {
    param(
        [string]$Side,
        [int]$RoundNum,
        [string]$ExePath,
        [hashtable]$SideEnv
    )

    # 1. Clean slate for PS2X_* env vars; save current to restore afterwards
    $savedEnv = @{}
    Get-ChildItem env:PS2X_* -ErrorAction SilentlyContinue | ForEach-Object {
        $savedEnv[$_.Name] = $_.Value
        Remove-Item "env:$($_.Name)" -Force -ErrorAction SilentlyContinue
    }

    try {
        # 2. Set standard bench environment
        $env:PS2X_GS_ASYNC = "1"
        $env:PS2X_VIF1_ASYNC = "1"
        $env:PS2X_GS_VULKAN = "1"
        $env:PS2X_VU1_KERNEL = "1"
        $env:PS2X_PRESENT_ASYNC = "1"
        $env:PS2X_PRESENT_GPU = "1"
        $env:PS2X_PAD_PLAY = $Pad
        $env:PS2X_PAD_PLAY_HOLD = "1"

        # 3. Apply side-specific env
        if ($SideEnv) {
            foreach ($key in $SideEnv.Keys) {
                Set-Item "env:$key" "$($SideEnv[$key])"
            }
        }

        $outPath = "logs\ab_${Tag}_${Side}${RoundNum}.out"
        $errPath = "logs\ab_${Tag}_${Side}${RoundNum}.err"
        if (Test-Path $outPath) { Remove-Item $outPath -Force -ErrorAction SilentlyContinue }
        if (Test-Path $errPath) { Remove-Item $errPath -Force -ErrorAction SilentlyContinue }

        Write-Host ("[{0}{1}] Starting {2} ..." -f $Side, $RoundNum, $ExePath)
        $proc = Start-Process -FilePath $ExePath -ArgumentList "SCUS_975.01" -WorkingDirectory "C:\ApeEscape3_Recomp" -RedirectStandardOutput $outPath -RedirectStandardError $errPath -PassThru

        # 4. Wait for '[bench] START' (poll every 1 s, max 300 s)
        $timeoutSec = 300
        $started = $false
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        while ($sw.Elapsed.TotalSeconds -lt $timeoutSec) {
            if ($proc.HasExited) { break }
            if (Test-Path $errPath) {
                try {
                    $fs = [System.IO.FileStream]::new($errPath, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
                    $sr = [System.IO.StreamReader]::new($fs)
                    $text = $sr.ReadToEnd()
                    $sr.Close()
                    $fs.Close()
                    if ($text -match "\[bench\] START") {
                        $started = $true
                        break
                    }
                } catch {}
            }
            Start-Sleep -Seconds 1
        }

        if (-not $started -and (Test-Path $errPath)) {
            try {
                $text = [System.IO.File]::ReadAllText($errPath)
                if ($text -match "\[bench\] START") { $started = $true }
            } catch {}
        }

        if (-not $started -or $proc.HasExited) {
            Write-Host ("[{0}{1}] FAILED: '[bench] START' marker not reached or process exited." -f $Side, $RoundNum)
            if (-not $proc.HasExited) {
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            }
            return [pscustomobject]@{
                Side = $Side; Round = $RoundNum; Status = "FAILED";
                p50 = 0.0; p99 = 0.0;
                GameThread = 0.0; Vif1Worker = 0.0; GsWorker = 0.0;
                PresentLatch = 0.0; MainLoop = 0.0; other = 0.0; TOTAL = 0.0;
                'TOTALms/s' = 0.0
            }
        }

        Write-Host ("[{0}{1}] Marker reached. Waiting 3 s (settle) ..." -f $Side, $RoundNum)
        Start-Sleep -Seconds 3

        if ($proc.HasExited) {
            Write-Host ("[{0}{1}] FAILED: process exited during settle." -f $Side, $RoundNum)
            return [pscustomobject]@{
                Side = $Side; Round = $RoundNum; Status = "FAILED";
                p50 = 0.0; p99 = 0.0;
                GameThread = 0.0; Vif1Worker = 0.0; GsWorker = 0.0;
                PresentLatch = 0.0; MainLoop = 0.0; other = 0.0; TOTAL = 0.0;
                'TOTALms/s' = 0.0
            }
        }

        Write-Host ("[{0}{1}] Sampling CPU over {2} s ..." -f $Side, $RoundNum, $Seconds)
        $a = Snap $proc
        $t0 = Get-Date
        Start-Sleep -Seconds $Seconds
        $b = Snap $proc
        $names = @{}
        foreach ($id in $b.Keys) {
            $names[$id] = ThreadName $id
        }
        $wall = ((Get-Date) - $t0).TotalSeconds
        if ($wall -le 0) { $wall = $Seconds }

        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        try { $proc.WaitForExit(5000) } catch {}

        # Aggregate thread CPU ms/frame
        $effectiveFps = if ($Fps -gt 0) { $Fps } else { 60.0 }
        $knownThreads = @('GameThread', 'Vif1Worker', 'GsWorker', 'PresentLatch', 'MainLoop')
        $threadCpu = @{
            'GameThread'   = 0.0
            'Vif1Worker'   = 0.0
            'GsWorker'     = 0.0
            'PresentLatch' = 0.0
            'MainLoop'     = 0.0
            'other'        = 0.0
            'TOTAL'        = 0.0
        }

        foreach ($id in $b.Keys) {
            $prev = if ($a.ContainsKey($id)) { $a[$id] } else { 0.0 }
            $d = $b[$id] - $prev
            if ($d -lt 0) { $d = 0.0 }
            $cpuMsPerSec = $d / $wall
            $cpuMsPerFrame = $cpuMsPerSec / $effectiveFps
            $lbl = $names[$id]
            if ($knownThreads -contains $lbl) {
                $threadCpu[$lbl] += $cpuMsPerFrame
            } else {
                $threadCpu['other'] += $cpuMsPerFrame
            }
            $threadCpu['TOTAL'] += $cpuMsPerFrame
        }

        # Parse .err for [ft] lines after [bench] START
        $p50Val = 0.0
        $p99Val = 0.0
        if (Test-Path $errPath) {
            $lines = [System.IO.File]::ReadAllLines($errPath)
            $startIdx = -1
            for ($i = 0; $i -lt $lines.Count; $i++) {
                if ($lines[$i] -match "\[bench\] START") {
                    $startIdx = $i
                    break
                }
            }

            $p50List = [System.Collections.Generic.List[double]]::new()
            $p99List = [System.Collections.Generic.List[double]]::new()
            if ($startIdx -ge 0) {
                for ($i = $startIdx + 1; $i -lt $lines.Count; $i++) {
                    $ln = $lines[$i]
                    if ($ln -match "\[ft\].*p50=([0-9.]+).*p99=([0-9.]+)") {
                        $p50List.Add([double]::Parse($Matches[1], [System.Globalization.CultureInfo]::InvariantCulture))
                        $p99List.Add([double]::Parse($Matches[2], [System.Globalization.CultureInfo]::InvariantCulture))
                    }
                }
            }
            if ($p50List.Count -gt 0) {
                $p50Val = Get-Median $p50List.ToArray()
                $p99Val = Get-Median $p99List.ToArray()
            }
        }

        Write-Host ("[{0}{1}] Complete: p50={2:F2} p99={3:F2} Vif1={4:F2} Gs={5:F2} Total={6:F2}" -f $Side, $RoundNum, $p50Val, $p99Val, $threadCpu['Vif1Worker'], $threadCpu['GsWorker'], $threadCpu['TOTAL'])

        return [pscustomobject]@{
            Side = $Side; Round = $RoundNum; Status = "OK";
            p50 = $p50Val; p99 = $p99Val;
            GameThread = $threadCpu['GameThread'];
            Vif1Worker = $threadCpu['Vif1Worker'];
            GsWorker = $threadCpu['GsWorker'];
            PresentLatch = $threadCpu['PresentLatch'];
            MainLoop = $threadCpu['MainLoop'];
            other = $threadCpu['other'];
            TOTAL = $threadCpu['TOTAL'];
            'TOTALms/s' = ($threadCpu['TOTAL'] * $effectiveFps);
        }
    } finally {
        # Restore environment
        Get-ChildItem env:PS2X_* -ErrorAction SilentlyContinue | ForEach-Object {
            Remove-Item "env:$($_.Name)" -Force -ErrorAction SilentlyContinue
        }
        foreach ($k in $savedEnv.Keys) {
            Set-Item "env:$k" "$($savedEnv[$k])"
        }
    }
}

$results = [System.Collections.Generic.List[psobject]]::new()

for ($r = 1; $r -le $Rounds; $r++) {
    $resA = Run-Side -Side "A" -RoundNum $r -ExePath $ExeA -SideEnv $EnvA
    $results.Add($resA)

    $resB = Run-Side -Side "B" -RoundNum $r -ExePath $ExeB -SideEnv $EnvB
    $results.Add($resB)
}

function Mean-Val($items, [string]$prop) {
    $valid = $items | Where-Object { $_.Status -eq "OK" }
    if (-not $valid -or $valid.Count -eq 0) { return 0.0 }
    $sum = ($valid | ForEach-Object { [double]$_.$prop } | Measure-Object -Sum).Sum
    return ($sum / $valid.Count)
}

$aRuns = $results | Where-Object { $_.Side -eq "A" }
$bRuns = $results | Where-Object { $_.Side -eq "B" }

$metrics = @('p50', 'p99', 'GameThread', 'Vif1Worker', 'GsWorker', 'PresentLatch', 'MainLoop', 'other', 'TOTAL', 'TOTALms/s')

$meanA = @{}
$meanB = @{}
$diffMs = @{}
$diffPct = @{}

foreach ($m in $metrics) {
    $mA = Mean-Val $aRuns $m
    $mB = Mean-Val $bRuns $m
    $meanA[$m] = $mA
    $meanB[$m] = $mB
    $d = $mB - $mA
    $diffMs[$m] = $d
    $diffPct[$m] = if ($mA -ne 0.0) { ($d / $mA) * 100.0 } else { 0.0 }
}

# Calculate noise |A1 - A2|
$a1 = $results | Where-Object { $_.Side -eq "A" -and $_.Round -eq 1 -and $_.Status -eq "OK" } | Select-Object -First 1
$a2 = $results | Where-Object { $_.Side -eq "A" -and $_.Round -eq 2 -and $_.Status -eq "OK" } | Select-Object -First 1
$hasNoise = ($null -ne $a1 -and $null -ne $a2)

$noiseP50 = if ($hasNoise) { [math]::Abs($a1.p50 - $a2.p50) } else { 0.0 }
$noiseVif = if ($hasNoise) { [math]::Abs($a1.Vif1Worker - $a2.Vif1Worker) } else { 0.0 }
$noiseGs  = if ($hasNoise) { [math]::Abs($a1.GsWorker - $a2.GsWorker) } else { 0.0 }

# Format Table
$tbl = [System.Collections.Generic.List[string]]::new()
$tbl.Add(("{0,-5} {1,-5} {2,8} {3,8} {4,11} {5,11} {6,11} {7,13} {8,10} {9,9} {10,9} {11,10}" -f "Side", "Round", "p50", "p99", "GameThread", "Vif1Worker", "GsWorker", "PresentLatch", "MainLoop", "other", "TOTAL", "TOTALms/s"))
$tbl.Add("-" * 120)

foreach ($row in $results) {
    if ($row.Status -ne "OK") {
        $tbl.Add(("{0,-5} {1,-5} {2,8}" -f $row.Side, $row.Round, "FAILED"))
    } else {
        $tbl.Add(("{0,-5} {1,-5} {2,8:F2} {3,8:F2} {4,11:F2} {5,11:F2} {6,11:F2} {7,13:F2} {8,10:F2} {9,9:F2} {10,9:F2} {11,10:F2}" -f `
            $row.Side, $row.Round, $row.p50, $row.p99, $row.GameThread, $row.Vif1Worker, $row.GsWorker, $row.PresentLatch, $row.MainLoop, $row.other, $row.TOTAL, $row.'TOTALms/s'))
    }
}

$tbl.Add("-" * 120)
$tbl.Add(("{0,-11} {1,8:F2} {2,8:F2} {3,11:F2} {4,11:F2} {5,11:F2} {6,13:F2} {7,10:F2} {8,9:F2} {9,9:F2} {10,10:F2}" -f `
    "Mean A", $meanA['p50'], $meanA['p99'], $meanA['GameThread'], $meanA['Vif1Worker'], $meanA['GsWorker'], $meanA['PresentLatch'], $meanA['MainLoop'], $meanA['other'], $meanA['TOTAL'], $meanA['TOTALms/s']))
$tbl.Add(("{0,-11} {1,8:F2} {2,8:F2} {3,11:F2} {4,11:F2} {5,11:F2} {6,13:F2} {7,10:F2} {8,9:F2} {9,9:F2} {10,10:F2}" -f `
    "Mean B", $meanB['p50'], $meanB['p99'], $meanB['GameThread'], $meanB['Vif1Worker'], $meanB['GsWorker'], $meanB['PresentLatch'], $meanB['MainLoop'], $meanB['other'], $meanB['TOTAL'], $meanB['TOTALms/s']))
$tbl.Add(("{0,-11} {1,8:F2} {2,8:F2} {3,11:F2} {4,11:F2} {5,11:F2} {6,13:F2} {7,10:F2} {8,9:F2} {9,9:F2} {10,10:F2}" -f `
    "Diff(B-A)", $diffMs['p50'], $diffMs['p99'], $diffMs['GameThread'], $diffMs['Vif1Worker'], $diffMs['GsWorker'], $diffMs['PresentLatch'], $diffMs['MainLoop'], $diffMs['other'], $diffMs['TOTAL'], $diffMs['TOTALms/s']))
$tbl.Add(("{0,-11} {1,7:F1}% {2,7:F1}% {3,10:F1}% {4,10:F1}% {5,10:F1}% {6,12:F1}% {7,9:F1}% {8,8:F1}% {9,8:F1}% {10,9:F1}%" -f `
    "Diff(%)", $diffPct['p50'], $diffPct['p99'], $diffPct['GameThread'], $diffPct['Vif1Worker'], $diffPct['GsWorker'], $diffPct['PresentLatch'], $diffPct['MainLoop'], $diffPct['other'], $diffPct['TOTAL'], $diffPct['TOTALms/s']))

if ($hasNoise) {
    $tbl.Add(("{0,-11} {1,8:F2} {2,8} {3,11} {4,11:F2} {5,11:F2} {6,13} {7,10} {8,9} {9,9} {10,10}" -f `
        "Noise|A1-A2|", $noiseP50, "-", "-", $noiseVif, $noiseGs, "-", "-", "-", "-", "-"))
}

$tbl.Add("")
$summaryLine = ("AB {0} p50 A={1:F2} B={2:F2} | vif A={3:F2} B={4:F2} | gs A={5:F2} B={6:F2}" -f `
    $Tag, $meanA['p50'], $meanB['p50'], $meanA['Vif1Worker'], $meanB['Vif1Worker'], $meanA['GsWorker'], $meanB['GsWorker'])
$tbl.Add($summaryLine)

# Print table
$tbl | ForEach-Object { Write-Host $_ }

# Save table to logs\ab_<Tag>.txt
$reportPath = "logs\ab_${Tag}.txt"
$tbl | Set-Content -Path $reportPath -Encoding utf8
