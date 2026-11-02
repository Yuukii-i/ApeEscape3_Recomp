# CPU cost per frame of any running process (ours or PCSX2), so "cheaper than emulating on PCSX2" has a number.
# Usage (run while the game sits in the scene you care about, e.g. the shop):
#   powershell -File tools\cpu_per_frame.ps1 -Name ps2EntryRunner -Fps 60 [-Seconds 20]
#   powershell -File tools\cpu_per_frame.ps1 -Name pcsx2-qt -Fps 60
# -Fps is the frame rate the process shows during the run (our [fps] line, PCSX2's on-screen counter). Output: CPU ms per second and per frame, per thread.
param([Parameter(Mandatory = $true)][string]$Name, [double]$Fps = 0, [int]$Seconds = 20)
$p = Get-Process -Name $Name -ErrorAction Stop | Select-Object -First 1
function Snap($proc) {
    $proc.Refresh()
    $h = @{}
    foreach ($t in $proc.Threads) { try { $h[$t.Id] = $t.TotalProcessorTime.TotalMilliseconds } catch {} }
    return $h
}
$a = Snap $p
$t0 = Get-Date
Start-Sleep -Seconds $Seconds
$b = Snap $p
$wall = ((Get-Date) - $t0).TotalSeconds
$rows = foreach ($id in $b.Keys) {
    $d = $b[$id] - $(if ($a.ContainsKey($id)) { $a[$id] } else { 0 })
    [pscustomobject]@{ Thread = $id; CpuMsPerSec = [math]::Round($d / $wall, 1) }
}
$rows = $rows | Where-Object { $_.CpuMsPerSec -ge 5 } | Sort-Object CpuMsPerSec -Descending
$total = ($rows | Measure-Object CpuMsPerSec -Sum).Sum
Write-Host ("process {0} (pid {1}), {2:N1} s window" -f $p.ProcessName, $p.Id, $wall)
if ($Fps -gt 0) {
    $rows | ForEach-Object { Write-Host ("  thread {0,6}: {1,7:N1} ms/s  = {2,6:N2} ms/frame at {3} fps" -f $_.Thread, $_.CpuMsPerSec, ($_.CpuMsPerSec / $Fps), $Fps) }
    Write-Host ("TOTAL {0:N1} ms/s = {1:N2} CPU-ms per frame = {2:N2} cores busy" -f $total, ($total / $Fps), ($total / 1000.0))
} else {
    $rows | ForEach-Object { Write-Host ("  thread {0,6}: {1,7:N1} ms/s" -f $_.Thread, $_.CpuMsPerSec) }
    Write-Host ("TOTAL {0:N1} ms/s = {1:N2} cores busy (pass -Fps for per-frame numbers)" -f $total, ($total / 1000.0))
}
