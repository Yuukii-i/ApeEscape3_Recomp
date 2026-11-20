# Frame-time + CPU-per-frame collector for any running process (e.g. pcsx2-qt, ps2EntryRunner_dev).
# Usage:
#   powershell -File tools\pcsx2_frametime.ps1 -Name pcsx2-qt [-Seconds 0] [-Interval 2] [-Warmup 5] [-Out logs\ft_<name>_<yyyyMMdd_HHmmss>] [-PresentMon <path>]
param(
    [string]$Name = 'pcsx2-qt',
    [int]$Seconds = 0,
    [double]$Interval = 2,
    [int]$Warmup = 5,
    [string]$Out = '',
    [string]$PresentMon = '',
    [switch]$Elevate
)

$ErrorActionPreference = 'Stop'

if (-not $PresentMon) {
    $pm110 = 'C:\Program Files (x86)\RivaTuner Statistics Server\Plugins\Client\PresentMonDataProvider\PresentMon-1.10.0-x64.exe'
    $pmNv  = 'C:\Program Files\NVIDIA Corporation\FrameViewSDK\bin\PresentMon_x64.exe'
    $PresentMon = if (Test-Path -LiteralPath $pm110) { $pm110 } else { $pmNv }
}

# PresentMon needs admin rights or 'Performance Log Users' membership.
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$isAdmin = ([Security.Principal.WindowsPrincipal]$identity).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
$inPerfGroup = $false
try {
    foreach ($g in $identity.Groups) {
        try {
            if ($g.Translate([Security.Principal.NTAccount]).Value -like '*\Performance Log Users') { $inPerfGroup = $true; break }
        } catch {}
    }
} catch {}
if (-not ($isAdmin -or $inPerfGroup)) {
    if ($Elevate) {
        $argList = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$($MyInvocation.MyCommand.Path)`"",
            '-Name', "`"$Name`"", '-Seconds', $Seconds, '-Interval', $Interval, '-Warmup', $Warmup, '-PresentMon', "`"$PresentMon`"")
        if ($Out) { $argList += @('-Out', "`"$((Join-Path (Get-Location) $Out))`"") }
        $p = Start-Process -FilePath (Get-Process -Id $PID).Path -ArgumentList $argList -Verb RunAs -Wait -PassThru
        exit $p.ExitCode
    }
    Write-Host "PresentMon needs elevation: this shell is not Administrator and not in 'Performance Log Users'."
    Write-Host "Run PowerShell as Administrator, or add yourself to the 'Performance Log Users' group and log off/on."
    Write-Host "Or re-run this script with -Elevate to relaunch it elevated."
    exit 2
}

if (-not (Test-Path -LiteralPath $PresentMon)) {
    Write-Error "PresentMon not found at '$PresentMon'. Pass -PresentMon <path> to override."
    exit 1
}

$procBase = $Name -replace '\.exe$', ''
if (-not $Out) {
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $Out = "logs\ft_${procBase}_${stamp}"
}
$Out = [IO.Path]::GetFullPath([IO.Path]::Combine((Get-Location).ProviderPath, $Out))

$outDir = Split-Path -Parent $Out
if ($outDir -and -not (Test-Path -LiteralPath $outDir)) {
    New-Item -ItemType Directory -Force -Path $outDir | Out-Null
}

$presentsCsv = "${Out}_presents.csv"
$cpuCsv = "${Out}_cpu.csv"
$pmOutTxt = "${Out}_pm_out.txt"
$pmErrTxt = "${Out}_pm_err.txt"

Add-Type -Namespace Win -Name FtThr -MemberDefinition @'
[System.Runtime.InteropServices.DllImport("kernel32.dll")] public static extern System.IntPtr OpenThread(uint access, bool inherit, uint id);
[System.Runtime.InteropServices.DllImport("kernel32.dll")] public static extern int GetThreadDescription(System.IntPtr h, out System.IntPtr desc);
[System.Runtime.InteropServices.DllImport("kernel32.dll")] public static extern bool CloseHandle(System.IntPtr h);
[System.Runtime.InteropServices.DllImport("kernel32.dll")] public static extern System.IntPtr LocalFree(System.IntPtr h);
'@ -ErrorAction SilentlyContinue

function Get-ThreadLabel([int]$tid) {
    try {
        $h = [Win.FtThr]::OpenThread(0x800, $false, [uint32]$tid)
        if ($h -eq [IntPtr]::Zero) { return "tid$tid" }
        $d = [IntPtr]::Zero
        $n = ''
        if ([Win.FtThr]::GetThreadDescription($h, [ref]$d) -ge 0 -and $d -ne [IntPtr]::Zero) {
            $n = [System.Runtime.InteropServices.Marshal]::PtrToStringUni($d)
            [void][Win.FtThr]::LocalFree($d)
        }
        [void][Win.FtThr]::CloseHandle($h)
        $n = ($n -replace '[\r\n,"]', '_').Trim()
        if ($n) { return $n }
    } catch {}
    return "tid$tid"
}

function Get-ThreadCpuSnap($proc) {
    $proc.Refresh()
    $snap = @{}
    foreach ($t in $proc.Threads) {
        try {
            $snap[$t.Id] = $t.TotalProcessorTime.TotalMilliseconds
        } catch {}
    }
    return $snap
}

function Count-NewPresentLines([string]$path, [ref]$offset, [ref]$headerSkipped) {
    if (-not (Test-Path -LiteralPath $path)) { return 0 }
    try {
        $fs = [System.IO.File]::Open($path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
        try {
            if ($fs.Length -le $offset.Value) { return 0 }
            [void]$fs.Seek($offset.Value, [System.IO.SeekOrigin]::Begin)
            $sr = New-Object System.IO.StreamReader($fs)
            $count = 0
            while ($null -ne ($line = $sr.ReadLine())) {
                if (-not $headerSkipped.Value) {
                    $headerSkipped.Value = $true
                    continue
                }
                if ($line.Trim().Length -gt 0) { $count++ }
            }
            $offset.Value = $fs.Position
            return $count
        } finally {
            $fs.Dispose()
        }
    } catch {
        return 0
    }
}

Write-Host "Waiting for process '$procBase' (up to 30s)..."
$proc = $null
$waitDeadline = (Get-Date).AddSeconds(30)
while ((Get-Date) -lt $waitDeadline) {
    $proc = Get-Process -Name $procBase -ErrorAction SilentlyContinue | Sort-Object CPU -Descending | Select-Object -First 1
    if ($proc) { break }
    Start-Sleep -Milliseconds 500
}
if (-not $proc) {
    Write-Error "Process '$procBase' not found within 30 seconds."
    exit 1
}

Write-Host ("Found {0} (pid {1}). Starting PresentMon -> {2}" -f $proc.ProcessName, $proc.Id, $presentsCsv)

$pmLeaf = Split-Path -Leaf $PresentMon
if ($pmLeaf -match 'PresentMon-1\.') {
    $pmArgs = @(
        '-process_name', "$($proc.ProcessName).exe",
        '-output_file', $presentsCsv,
        '-terminate_on_proc_exit',
        '-no_top',
        '-stop_existing_session'
    )
} else {
    $pmArgs = @(
        '--process_name', "$($proc.ProcessName).exe",
        '--output_file', $presentsCsv,
        '--terminate_on_proc_exit',
        '--no_console_stats',
        '--v1_metrics',
        '--stop_existing_session'
    )
}
$pmProc = Start-Process -FilePath $PresentMon -ArgumentList $pmArgs -NoNewWindow -RedirectStandardOutput $pmOutTxt -RedirectStandardError $pmErrTxt -PassThru
$startTime = Get-Date
$pmDeadline = $startTime.AddSeconds(20)
while ((Get-Date) -lt $pmDeadline) {
    if ($pmProc.HasExited -or (Test-Path -LiteralPath $presentsCsv)) { break }
    Start-Sleep -Milliseconds 500
}
if ($pmProc.HasExited -or -not (Test-Path -LiteralPath $presentsCsv)) {
    $code = if ($pmProc.HasExited) { $pmProc.ExitCode } else { 'still running' }
    Write-Host "PresentMon failed to start: exit code $code, presents csv exists: $(Test-Path -LiteralPath $presentsCsv). Stopping."
    if (-not $pmProc.HasExited) {
        Write-Host "PresentMon is running but saw no presents from $($proc.ProcessName): is the game window actually rendering (not paused/minimised)?"
    }
    if (Test-Path -LiteralPath $pmOutTxt) {
        Write-Host "--- $pmOutTxt (first 10 lines) ---"
        Get-Content -LiteralPath $pmOutTxt -TotalCount 10 | ForEach-Object { Write-Host $_ }
    }
    if (Test-Path -LiteralPath $pmErrTxt) {
        Write-Host "--- $pmErrTxt (first 10 lines) ---"
        Get-Content -LiteralPath $pmErrTxt -TotalCount 10 | ForEach-Object { Write-Host $_ }
    }
    if (-not $pmProc.HasExited) { Stop-Process -Id $pmProc.Id -Force -ErrorAction SilentlyContinue }
    exit 3
}

$prevSnap = Get-ThreadCpuSnap $proc
$prevProcCpu = $proc.TotalProcessorTime.TotalMilliseconds
$prevTime = $startTime
$tidLabels = @{}
foreach ($tid in $prevSnap.Keys) {
    $tidLabels[$tid] = Get-ThreadLabel $tid
}

$threadCols = New-Object System.Collections.Generic.List[string]
$rows = New-Object System.Collections.Generic.List[object]
$tag = 0
$pmOffset = [long]0
$pmHeaderSkipped = $false
$interactive = $false
try {
    if (-not [Console]::IsInputRedirected) {
        [Console]::TreatControlCAsInput = $true
        $interactive = $true
    }
} catch {
    $interactive = $false
}

Write-Host "Collecting (Interval=${Interval}s, Seconds=$Seconds, Warmup=${Warmup}s). Keys: 0-9 = set tag, Q/Ctrl+C = stop."

try {
    $stopRequested = $false
    while (-not $stopRequested) {
        $sliceEnd = (Get-Date).AddSeconds($Interval)
        while ((Get-Date) -lt $sliceEnd) {
            if ($proc.HasExited) { $stopRequested = $true; break }
            if ($Seconds -gt 0 -and ((Get-Date) - $startTime).TotalSeconds -ge $Seconds) { $stopRequested = $true; break }
            if ($interactive) {
                try {
                    while ([Console]::KeyAvailable) {
                        $k = [Console]::ReadKey($true)
                        if ($k.Key -eq 'C' -and ($k.Modifiers -band [ConsoleModifiers]::Control)) {
                            $stopRequested = $true; break
                        }
                        if ($k.KeyChar -eq 'q' -or $k.KeyChar -eq 'Q') {
                            $stopRequested = $true; break
                        }
                        if ($k.KeyChar -ge '0' -and $k.KeyChar -le '9') {
                            $tag = [int][string]$k.KeyChar
                            Write-Host ("  [tag={0}]" -f $tag)
                        }
                    }
                } catch {}
                if ($stopRequested) { break }
            }
            Start-Sleep -Milliseconds 100
        }

        $proc.Refresh()
        $now = Get-Date
        $dt = ($now - $prevTime).TotalSeconds
        if ($dt -le 0.05) { break }

        $currSnap = Get-ThreadCpuSnap $proc
        $currProcCpu = $proc.TotalProcessorTime.TotalMilliseconds
        $totalCpuDelta = [math]::Max(0.0, $currProcCpu - $prevProcCpu)

        $byName = @{}
        $sumThreadDelta = 0.0
        foreach ($tid in $currSnap.Keys) {
            if (-not $tidLabels.ContainsKey($tid)) {
                $tidLabels[$tid] = Get-ThreadLabel $tid
            }
            $lbl = $tidLabels[$tid]
            $prevVal = if ($prevSnap.ContainsKey($tid)) { $prevSnap[$tid] } else { 0.0 }
            $d = [math]::Max(0.0, $currSnap[$tid] - $prevVal)
            $sumThreadDelta += $d
            if ($byName.ContainsKey($lbl)) { $byName[$lbl] += $d } else { $byName[$lbl] = $d }
            if (-not $threadCols.Contains($lbl)) {
                $threadCols.Add($lbl)
                $headerDirty = $true
            }
        }
        if ($totalCpuDelta -lt $sumThreadDelta) { $totalCpuDelta = $sumThreadDelta }

        $tSec = ($now - $startTime).TotalSeconds
        $rowObj = [pscustomobject]@{
            t = $tSec
            tag = $tag
            total = $totalCpuDelta
            threads = $byName
        }
        $rows.Add($rowObj)

        # Write/rewrite CPU CSV so columns stay aligned even as new threads appear
        $header = (@('t_seconds_since_start', 'tag', 'total_cpu_ms_delta') + $threadCols) -join ','
        if ($headerDirty -or -not (Test-Path -LiteralPath $cpuCsv)) {
            $lines = New-Object System.Collections.Generic.List[string]
            $lines.Add($header)
            foreach ($r in $rows) {
                $vals = @(([math]::Round($r.t, 3)), $r.tag, ([math]::Round($r.total, 3)))
                foreach ($c in $threadCols) {
                    $v = if ($r.threads.ContainsKey($c)) { $r.threads[$c] } else { 0.0 }
                    $vals += [math]::Round($v, 3)
                }
                $lines.Add(($vals -join ','))
            }
            [System.IO.File]::WriteAllLines($cpuCsv, $lines)
            $headerDirty = $false
        } else {
            $vals = @(([math]::Round($rowObj.t, 3)), $rowObj.tag, ([math]::Round($rowObj.total, 3)))
            foreach ($c in $threadCols) {
                $v = if ($rowObj.threads.ContainsKey($c)) { $rowObj.threads[$c] } else { 0.0 }
                $vals += [math]::Round($v, 3)
            }
            [System.IO.File]::AppendAllText($cpuCsv, ($vals -join ',') + [Environment]::NewLine)
        }

        $newPresents = Count-NewPresentLines $presentsCsv ([ref]$pmOffset) ([ref]$pmHeaderSkipped)
        $fpsApprox = if ($dt -gt 0) { $newPresents / $dt } else { 0.0 }
        $cpuPerFrame = if ($newPresents -gt 0) { $totalCpuDelta / $newPresents } else { 0.0 }
        Write-Host ("t={0:N1}s tag={1} fps~{2:N1} cpu/frame={3:N2} ms" -f $tSec, $tag, $fpsApprox, $cpuPerFrame)

        $prevSnap = $currSnap
        $prevProcCpu = $currProcCpu
        $prevTime = $now
    }
} finally {
    if ($interactive) {
        try { [Console]::TreatControlCAsInput = $false } catch {}
    }
    if ($pmProc -and -not $pmProc.HasExited) {
        Stop-Process -Id $pmProc.Id -Force -ErrorAction SilentlyContinue
        try { [void]$pmProc.WaitForExit(3000) } catch {}
    }
}

Write-Host "Collection stopped. Running frametime_report.py..."
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$reportPy = Join-Path $scriptDir 'frametime_report.py'
python $reportPy $Out --drop-warmup $Warmup
