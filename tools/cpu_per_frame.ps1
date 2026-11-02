# CPU cost per frame of any running process (ours or PCSX2), so "cheaper than emulating on PCSX2" has a number.
# Usage (run while the game sits in the scene you care about, e.g. the shop):
#   powershell -File tools\cpu_per_frame.ps1 -Name ps2EntryRunner -Fps 60 [-Seconds 20]
#   powershell -File tools\cpu_per_frame.ps1 -Name pcsx2-qt -Fps 60
# -Fps is the frame rate the process shows during the run (our [fps] line, PCSX2's on-screen counter). Output: CPU ms per second and per frame, per thread.
# Thread names (GameThread, Vif1Worker, GsWorker, PresentLatch, MainLoop in our build; PCSX2 names its own) come from GetThreadDescription.
param([Parameter(Mandatory = $true)][string]$Name, [double]$Fps = 0, [int]$Seconds = 20)
Add-Type -Namespace Win -Name Thr -MemberDefinition @'
[System.Runtime.InteropServices.DllImport("kernel32.dll")] public static extern System.IntPtr OpenThread(uint access, bool inherit, uint id);
[System.Runtime.InteropServices.DllImport("kernel32.dll")] public static extern int GetThreadDescription(System.IntPtr h, out System.IntPtr desc);
[System.Runtime.InteropServices.DllImport("kernel32.dll")] public static extern bool CloseHandle(System.IntPtr h);
[System.Runtime.InteropServices.DllImport("kernel32.dll")] public static extern System.IntPtr LocalFree(System.IntPtr h);
'@
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
# several processes can share a name (launcher shims): take the one that has used the most CPU
$p = Get-Process -Name $Name -ErrorAction Stop | Sort-Object CPU -Descending | Select-Object -First 1
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
    [pscustomobject]@{ Thread = $id; CpuMsPerSec = [math]::Round($d / $wall, 1); Label = (ThreadName $id) }
}
$rows = $rows | Where-Object { $_.CpuMsPerSec -ge 5 } | Sort-Object CpuMsPerSec -Descending
$total = ($rows | Measure-Object CpuMsPerSec -Sum).Sum
Write-Host ("process {0} (pid {1}), {2:N1} s window" -f $p.ProcessName, $p.Id, $wall)
if ($Fps -gt 0) {
    $rows | ForEach-Object { Write-Host ("  thread {0,6} {1,-14}: {2,7:N1} ms/s  = {3,6:N2} ms/frame at {4} fps" -f $_.Thread, $_.Label, $_.CpuMsPerSec, ($_.CpuMsPerSec / $Fps), $Fps) }
    Write-Host ("TOTAL {0:N1} ms/s = {1:N2} CPU-ms per frame = {2:N2} cores busy" -f $total, ($total / $Fps), ($total / 1000.0))
} else {
    $rows | ForEach-Object { Write-Host ("  thread {0,6} {1,-14}: {2,7:N1} ms/s" -f $_.Thread, $_.Label, $_.CpuMsPerSec) }
    Write-Host ("TOTAL {0:N1} ms/s = {1:N2} cores busy (pass -Fps for per-frame numbers)" -f $total, ($total / 1000.0))
}
