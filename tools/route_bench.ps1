# tools/route_bench.ps1 - per-segment route benchmark (pad replay with marks)
param(
    [string]$Exe = "build\PS2Recomp\ps2xRuntime\ps2EntryRunner_dev.exe",
    [string]$Pad = "logs\levels_run.padrec",
    [int]$StopMark = 11,
    [hashtable]$Env = @{},
    [string]$Tag = "route",
    [string]$Names = "",
    [int]$TimeoutS = 400
)
$ErrorActionPreference = "Continue"
Set-Location C:\ApeEscape3_Recomp
$inv = [System.Globalization.CultureInfo]::InvariantCulture

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
        $h = [Win.Thr]::OpenThread(0x800, $false, [uint32]$id)
        if ($h -eq [IntPtr]::Zero) { return "" }
        $d = [IntPtr]::Zero; $name = ""
        if ([Win.Thr]::GetThreadDescription($h, [ref]$d) -ge 0 -and $d -ne [IntPtr]::Zero) {
            $name = [System.Runtime.InteropServices.Marshal]::PtrToStringUni($d)
            [void][Win.Thr]::LocalFree($d)
        }
        [void][Win.Thr]::CloseHandle($h)
        return $name
    } catch { return "" }
}

# env: clear PS2X_* then set base + overrides
Get-ChildItem env:PS2X_* -ErrorAction SilentlyContinue | ForEach-Object { Remove-Item "env:$($_.Name)" -Force -ErrorAction SilentlyContinue }
$base = [ordered]@{ PS2X_GS_ASYNC="1"; PS2X_VIF1_ASYNC="1"; PS2X_GS_VULKAN="1"; PS2X_VU1_KERNEL="1";
    PS2X_PRESENT_ASYNC="1"; PS2X_PRESENT_GPU="1"; PS2X_PAD_PLAY=$Pad; PS2X_PAD_STOP_MARK="$StopMark" }
foreach ($k in $base.Keys) { Set-Item "env:$k" $base[$k] }
foreach ($k in $Env.Keys) { Set-Item "env:$k" "$($Env[$k])" }

New-Item -ItemType Directory -Path logs -Force | Out-Null
$errPath = "logs\route_$Tag.err"; $outPath = "logs\route_$Tag.out"; $txtPath = "logs\route_$Tag.txt"
foreach ($p in @($errPath, $outPath)) { if (Test-Path $p) { Remove-Item $p -Force -ErrorAction SilentlyContinue } }
$nameList = @(); if ($Names) { $nameList = $Names -split '\s*,\s*' }

$proc = Start-Process -FilePath $Exe -ArgumentList "SCUS_975.01" -WorkingDirectory "C:\ApeEscape3_Recomp" `
    -RedirectStandardOutput $outPath -RedirectStandardError $errPath -PassThru
$sw = [System.Diagnostics.Stopwatch]::StartNew()

$tname = @{}      # id -> name
$cum = @{}        # id -> last cpu ms (kept after thread exit)
$segBase = @{}    # id -> cpu ms at segment start
$segs = New-Object System.Collections.Generic.List[object]
$segStartT = 0.0
$fpsCur = New-Object System.Collections.Generic.List[double]
$offset = 0L; $partial = ""; $stopped = $false

function Poll-Cpu {
    try { $proc.Refresh() } catch { return }
    if ($proc.HasExited) { return }
    try {
        foreach ($t in $proc.Threads) {
            try {
                $id = $t.Id
                $cum[$id] = $t.TotalProcessorTime.TotalMilliseconds
                if (-not $tname.ContainsKey($id) -or -not $tname[$id]) { $tname[$id] = ThreadName $id }
            } catch {}
        }
    } catch {}
}
function Close-Seg([string]$label) {
    $now = $sw.Elapsed.TotalSeconds
    $d = @{}
    foreach ($id in $cum.Keys) {
        $b = 0.0; if ($segBase.ContainsKey($id)) { $b = $segBase[$id] }
        $v = $cum[$id] - $b
        if ($v -gt 0) {
            $n = $tname[$id]; if (-not $n) { $n = "other" }
            if ($d.ContainsKey($n)) { $d[$n] += $v } else { $d[$n] = $v }
        }
    }
    $script:segs.Add([pscustomobject]@{ Label=$label; Wall=($now - $script:segStartT); Fps=$script:fpsCur.ToArray(); Cpu=$d })
    $script:segBase = $cum.Clone()
    $script:segStartT = $now
    $script:fpsCur = New-Object System.Collections.Generic.List[double]
}
function Read-New {
    if (-not (Test-Path $errPath)) { return }
    $txt = ""
    try {
        $fs = [System.IO.FileStream]::new($errPath, 'Open', 'Read', 'ReadWrite')
        [void]$fs.Seek($script:offset, 'Begin')
        $sr = [System.IO.StreamReader]::new($fs)
        $txt = $sr.ReadToEnd()
        $script:offset = $fs.Position
        $sr.Close(); $fs.Close()
    } catch { return }
    if (-not $txt) { return }
    $txt = $script:partial + $txt
    $lines = $txt -split "`n"
    $script:partial = $lines[-1]
    for ($i = 0; $i -lt $lines.Count - 1; $i++) {
        $l = $lines[$i]
        if ($l -match '\[fps\] FPS:\s*([0-9.]+)') {
            $script:fpsCur.Add([double]::Parse($Matches[1], $inv))
        } elseif ($l -match '\[padplay\] mark (\d+) reached') {
            $k = [int]$Matches[1]
            $lab = if ($k -le $nameList.Count) { $nameList[$k-1] } else { "seg$k" }
            Poll-Cpu
            Close-Seg $lab
        } elseif ($l -match '\[padplay\] stop at mark') {
            $script:stopped = $true
        }
    }
}

$timedOut = $false
while (-not $proc.HasExited) {
    Poll-Cpu
    Read-New
    if ($sw.Elapsed.TotalSeconds -gt $TimeoutS) {
        $timedOut = $true
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        break
    }
    Start-Sleep -Milliseconds 250
}
try { $proc.WaitForExit(3000) | Out-Null } catch {}
Read-New
if (-not $stopped) {
    $n = $segs.Count + 1
    $lab = if ($n -le $nameList.Count) { $nameList[$n-1] } else { "seg$n(end)" }
    Close-Seg $lab
}

# report
$allThr = @{}
foreach ($s in $segs) {
    $frames = 0.0
    foreach ($x in $s.Fps) { $frames += $x }
    if ($s.Fps.Count -eq 0) { $frames = 60.0 * $s.Wall }
    $s | Add-Member -NotePropertyName Frames -NotePropertyValue $frames -Force
    foreach ($n in $s.Cpu.Keys) {
        if ($n -ne "other" -and ($s.Cpu[$n] / 1000.0 / [math]::Max($s.Wall, 0.001)) -gt 0.02) { $allThr[$n] = 1 }
    }
}
$cols = @($allThr.Keys | Sort-Object) + @("other")
$out = New-Object System.Collections.Generic.List[string]
$tot = [math]::Round($sw.Elapsed.TotalSeconds, 1)
$out.Add("route_bench tag=$Tag exe=$Exe pad=$Pad stopMark=$StopMark total=${tot}s" + $(if ($timedOut) { " TIMEOUT" } else { "" }))
$out.Add("cells: ms/frame (%core). fpsMed/fpsMin = median/min (worst 1s window) of [fps] lines in segment.")
$hdr = "{0,-8} {1,6} {2,7} {3,6} {4,7}" -f "segment", "wall_s", "fpsMed", "fpsMin", "frames"
foreach ($c in $cols) { $hdr += " {0,16}" -f $c }
$out.Add($hdr)
foreach ($s in $segs) {
    $sorted = @($s.Fps | Sort-Object)
    $med = 0.0; $min = 0.0
    if ($sorted.Count -gt 0) {
        $m = [math]::Floor($sorted.Count / 2)
        $med = if ($sorted.Count % 2) { $sorted[$m] } else { ($sorted[$m-1] + $sorted[$m]) / 2.0 }
        $min = $sorted[0]
    }
    $row = "{0,-8} {1,6:N1} {2,7:N1} {3,6:N0} {4,7:N0}" -f $s.Label, $s.Wall, $med, $min, $s.Frames
    $other = 0.0
    foreach ($n in $s.Cpu.Keys) { if (-not $allThr.ContainsKey($n)) { $other += $s.Cpu[$n] } }
    foreach ($c in $cols) {
        $ms = if ($c -eq "other") { $other } elseif ($s.Cpu.ContainsKey($c)) { $s.Cpu[$c] } else { 0.0 }
        $mpf = if ($s.Frames -gt 0) { $ms / $s.Frames } else { 0.0 }
        $pct = 100.0 * $ms / 1000.0 / [math]::Max($s.Wall, 0.001)
        $row += " {0,16}" -f ("{0:N2} ({1:N0}%)" -f $mpf, $pct)
    }
    $out.Add($row)
}
$out | ForEach-Object { Write-Host $_ }
$out | Set-Content -Path $txtPath -Encoding UTF8
