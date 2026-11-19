# stage_bench.ps1 - per-stage CPU cost: boot to hub (padrec), warp to each stage, settle, then measure CPU ms per thread
# for -measure seconds (same method as cpu_per_frame.ps1) plus the game's [fps]. One row per stage -> logs\<tag>_bench.txt
# Usage: powershell -File tools\stage_bench.ps1 -tag base_off -extraEnv 'PS2X_EEDC=0' [-only 'travel_a,woods_a'] [-settle 8 -measure 12]
param([string]$tag = 'bench', [string]$padrec = 'logs\to_hub_fresh.padrec', [int]$settle = 8, [int]$measure = 12,
      [string]$only = 'travel_a,travel_b,woods_a,castle_a,studio_a,snowfesta_f,toyhouse_a,arabian_a,hong_a,space_a',
      [string]$extraEnv = '', [string]$exe = 'build\PS2Recomp\ps2xRuntime\ps2EntryRunner_dev.exe')
$ErrorActionPreference = 'Continue'
Set-Location C:\ApeEscape3_Recomp
Add-Type -Namespace Win -Name Thr2 -MemberDefinition @'
[System.Runtime.InteropServices.DllImport("kernel32.dll")] public static extern System.IntPtr OpenThread(uint access, bool inherit, uint id);
[System.Runtime.InteropServices.DllImport("kernel32.dll")] public static extern int GetThreadDescription(System.IntPtr h, out System.IntPtr desc);
[System.Runtime.InteropServices.DllImport("kernel32.dll")] public static extern bool CloseHandle(System.IntPtr h);
[System.Runtime.InteropServices.DllImport("kernel32.dll")] public static extern System.IntPtr LocalFree(System.IntPtr h);
'@ -ErrorAction SilentlyContinue
function ThreadName([int]$id) {
  try { $h = [Win.Thr2]::OpenThread(0x800, $false, [uint32]$id); if ($h -eq [IntPtr]::Zero) { return "" }
    $d = [IntPtr]::Zero; $n = ""
    if ([Win.Thr2]::GetThreadDescription($h, [ref]$d) -ge 0 -and $d -ne [IntPtr]::Zero) { $n = [System.Runtime.InteropServices.Marshal]::PtrToStringUni($d); [void][Win.Thr2]::LocalFree($d) }
    [void][Win.Thr2]::CloseHandle($h); return $n } catch { return "" } }
function Snap($proc) { $proc.Refresh(); $h = @{}; foreach ($t in $proc.Threads) { try { $h[$t.Id] = $t.TotalProcessorTime.TotalMilliseconds } catch {} }; return $h }
$err = "logs\${tag}_err.txt"; $run = "logs\${tag}_run.txt"; $out = "logs\${tag}_bench.txt"
Remove-Item logs\dev_cmd.txt -ErrorAction SilentlyContinue
$env:PS2X_GS_ASYNC='1';$env:PS2X_VIF1_ASYNC='1';$env:PS2X_GS_VULKAN='1';$env:PS2X_SG2_LLE='1';$env:PS2X_LOG_SYNC='1'
$env:PS2X_EEDC='1';$env:PS2X_EEDC_CHECK='0';$env:PS2X_EEDC_CENSUS='0';$env:PS2X_EEDC_DISABLE='';$env:PS2X_EEDC_ONLY='';$env:PS2X_EEDC_CHECK_JALR=''
$env:PS2X_MC='';$env:PS2X_PAD_REC='';$env:PS2X_PAD_PLAY=$padrec;$env:PS2X_PAD_STOP_MARK=''
foreach ($kv in ($extraEnv.Split(';') | Where-Object { $_ })) { $k,$v = $kv.Split('=',2); Set-Item -Path "env:$k" -Value $v }
Set-Content $out ("bench {0} {1} settle={2}s measure={3}s env='{4}'" -f $tag, (Get-Date -Format 'yyyy-MM-dd HH:mm'), $settle, $measure, $extraEnv)
$p = Start-Process $exe -ArgumentList 'SCUS_975.01' -RedirectStandardOutput $run -RedirectStandardError $err -PassThru
$t0 = Get-Date
while (((Get-Date) - $t0).TotalSeconds -lt 120 -and -not $p.HasExited) { if (Select-String -Path $err -Pattern 'stage/travel_a/actionseq' -Quiet) { break }; Start-Sleep 1 }
Start-Sleep 8
foreach ($s in $only.Split(',')) {
  if ($p.HasExited) { Add-Content $out "GAME EXITED before $s"; break }
  $before = (Select-String -Path $err -Pattern "\[dev\] warp -> " | Measure-Object).Count
  Add-Content logs\dev_cmd.txt "warp $s"
  $t1 = Get-Date
  while (((Get-Date) - $t1).TotalSeconds -lt 30 -and -not $p.HasExited) { if ((Select-String -Path $err -Pattern "\[dev\] warp -> " | Measure-Object).Count -gt $before) { break }; Start-Sleep -Milliseconds 300 }
  Start-Sleep $settle
  $fpsBefore = (Select-String -Path $err,$run -Pattern '\[fps\] FPS: (\d+)' | Measure-Object).Count
  $a = Snap $p; $ta = Get-Date
  Start-Sleep $measure
  $b = Snap $p; $wall = ((Get-Date) - $ta).TotalSeconds
  $fl = Select-String -Path $err,$run -Pattern '\[fps\] FPS: (\d+)' | Select-Object -Skip $fpsBefore
  $fps = if ($fl) { [math]::Round((($fl | % { [double]$_.Matches[0].Groups[1].Value } | Measure-Object -Average).Average), 1) } else { 0 }
  $rows = foreach ($id in $b.Keys) { $d = $b[$id] - $(if ($a.ContainsKey($id)) { $a[$id] } else { 0 }); [pscustomobject]@{ L = (ThreadName $id); Ms = $d / $wall } }
  $rows = $rows | Where-Object { $_.Ms -ge 5 } | Sort-Object Ms -Descending
  $tot = ($rows | Measure-Object Ms -Sum).Sum
  $f = if ($fps -gt 0) { $fps } else { 60 }
  $parts = ($rows | Select-Object -First 6 | % { "{0}={1:N1}" -f $(if ($_.L) { $_.L } else { 'thr' }), ($_.Ms / $f) }) -join ' '
  Add-Content $out ("{0,-12} fps={1,5} cpu/frame={2,6:N1} ms ({3:N2} cores) | {4}" -f $s, $fps, ($tot / $f), ($tot / 1000.0), $parts)
}
Add-Content $out "end $(Get-Date -Format HH:mm:ss)"
if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force }
