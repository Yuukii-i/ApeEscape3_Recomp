# stage_bench.ps1 - per-stage CPU cost: boot to hub (padrec), warp to each stage, settle, then measure CPU ms per thread
# for -measure seconds (same method as cpu_per_frame.ps1) plus the game's [fps]. One row per stage -> logs\<tag>_bench.txt
# Usage: powershell -File tools\stage_bench.ps1 -tag base_off -extraEnv 'PS2X_EEDC=0' [-only 'travel_a,woods_a'] [-settle 8 -measure 12]
param([string]$tag = 'bench', [string]$padrec = 'logs\to_hub_fresh.padrec', [int]$settle = 8, [int]$measure = 12,
      [string]$only = 'travel_a,travel_b,woods_a,castle_a,studio_a,snowfesta_f,toyhouse_a,arabian_a,hong_a,space_a',
      [string]$extraEnv = '', [string]$winSize = '', [string]$affinity = '', [string]$exe = 'build\PS2Recomp\ps2xRuntime\ps2EntryRunner_dev.exe')
$ErrorActionPreference = 'Continue'
Set-Location C:\ApeEscape3_Recomp
Add-Type -Namespace Win -Name Thr2 -MemberDefinition @'
[System.Runtime.InteropServices.DllImport("kernel32.dll")] public static extern System.IntPtr OpenThread(uint access, bool inherit, uint id);
[System.Runtime.InteropServices.DllImport("kernel32.dll")] public static extern int GetThreadDescription(System.IntPtr h, out System.IntPtr desc);
[System.Runtime.InteropServices.DllImport("kernel32.dll")] public static extern bool CloseHandle(System.IntPtr h);
[System.Runtime.InteropServices.DllImport("kernel32.dll")] public static extern System.IntPtr LocalFree(System.IntPtr h);
[System.Runtime.InteropServices.DllImport("user32.dll")] public static extern bool SetWindowPos(System.IntPtr h, System.IntPtr after, int x, int y, int cx, int cy, uint flags);
'@ -ErrorAction SilentlyContinue
function ThreadName([int]$id) {
  try { $h = [Win.Thr2]::OpenThread(0x800, $false, [uint32]$id); if ($h -eq [IntPtr]::Zero) { return "" }
    $d = [IntPtr]::Zero; $n = ""
    if ([Win.Thr2]::GetThreadDescription($h, [ref]$d) -ge 0 -and $d -ne [IntPtr]::Zero) { $n = [System.Runtime.InteropServices.Marshal]::PtrToStringUni($d); [void][Win.Thr2]::LocalFree($d) }
    [void][Win.Thr2]::CloseHandle($h); return $n } catch { return "" } }
function Snap($proc) { $proc.Refresh(); $h = @{}; foreach ($t in $proc.Threads) { try { $sa = [int64]0; try { $sa = $t.StartAddress.ToInt64() } catch {}; $h[$t.Id] = @{ Cpu = $t.TotalProcessorTime.TotalMilliseconds; Addr = $sa } } catch {} }; return $h }
function ResolveAddr($mods, [int64]$sa) {
  if ($sa -ne 0 -and $mods) {
    foreach ($m in $mods) {
      try {
        $base = $m.BaseAddress.ToInt64()
        if ($sa -ge $base -and $sa -lt ($base + [int64]$m.ModuleMemorySize)) { return ("{0}+0x{1:X}" -f $m.ModuleName, ($sa - $base)) }
      } catch {}
    }
  }
  return 'unknown'
}
$err = "logs\${tag}_err.txt"; $run = "logs\${tag}_run.txt"; $out = "logs\${tag}_bench.txt"
Remove-Item logs\dev_cmd.txt -ErrorAction SilentlyContinue
$env:PS2X_GS_ASYNC='1';$env:PS2X_VIF1_ASYNC='1';$env:PS2X_GS_VULKAN='1';$env:PS2X_SG2_LLE='1';$env:PS2X_LOG_SYNC='1';$env:PS2X_WINDOW_BACKGROUND='1';$env:PS2X_NO_CONFIG='1'
$env:PS2X_EEDC='1';$env:PS2X_EEDC_CHECK='0';$env:PS2X_EEDC_CENSUS='0';$env:PS2X_EEDC_DISABLE='';$env:PS2X_EEDC_ONLY='';$env:PS2X_EEDC_CHECK_JALR=''
$env:PS2X_MC='';$env:PS2X_PAD_REC='';$env:PS2X_PAD_PLAY=$padrec;$env:PS2X_PAD_STOP_MARK=''
$env:PS2X_DEV_CMD='logs\dev_cmd.txt' # FIX-DC1
foreach ($kv in ($extraEnv.Split(';') | Where-Object { $_ })) { $k,$v = $kv.Split('=',2); Set-Item -Path "env:$k" -Value $v }
$p = Start-Process $exe -ArgumentList 'SCUS_975.01' -RedirectStandardOutput $run -RedirectStandardError $err -PassThru
if ($affinity) {
  $ok = $false
  for ($i = 0; $i -lt 5 -and -not $ok; $i++) {
    try {
      $p.ProcessorAffinity = [IntPtr][Convert]::ToInt64($affinity, 16)
      $ok = $true
    } catch {
      Start-Sleep -Milliseconds 100
    }
  }
  if (-not $ok) { Write-Warning "Failed to set ProcessorAffinity=$affinity" }
}
$effAff = try { $p.Refresh(); '0x{0:X}' -f $p.ProcessorAffinity.ToInt64() } catch { 'unknown' }
Set-Content $out ("bench {0} {1} settle={2}s measure={3}s env='{4}' affinity={5}" -f $tag, (Get-Date -Format 'yyyy-MM-dd HH:mm'), $settle, $measure, $extraEnv, $effAff)
$t0 = Get-Date
while (((Get-Date) - $t0).TotalSeconds -lt 120 -and -not $p.HasExited) { if (Select-String -Path $err -Pattern 'stage/travel_a/actionseq' -Quiet) { break }; Start-Sleep 1 }
Start-Sleep 8
if ($winSize) { $wh = $winSize.Split('x'); $p.Refresh(); [void][Win.Thr2]::SetWindowPos($p.MainWindowHandle, [IntPtr]1, 0, 0, [int]$wh[0], [int]$wh[1], 0x0012) }
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
  $mods = $null; try { $p.Refresh(); $mods = @($p.Modules) } catch {}
  $fl = Select-String -Path $err,$run -Pattern '\[fps\] FPS: (\d+)' | Select-Object -Skip $fpsBefore
  $fps = if ($fl) { [math]::Round((($fl | % { [double]$_.Matches[0].Groups[1].Value } | Measure-Object -Average).Average), 1) } else { 0 }
  $rows = foreach ($id in $b.Keys) { $d = $b[$id].Cpu - $(if ($a.ContainsKey($id)) { $a[$id].Cpu } else { 0 }); [pscustomobject]@{ L = (ThreadName $id); Ms = $d / $wall; Addr = $b[$id].Addr } }
  $rows = $rows | Where-Object { $_.Ms -ge 5 } | Sort-Object Ms -Descending
  $tot = ($rows | Measure-Object Ms -Sum).Sum
  $f = if ($fps -gt 0) { $fps } else { 60 }
  $parts = ($rows | Select-Object -First 6 | % { "{0}={1:N1}" -f $(if ($_.L) { $_.L } else { 'thr' }), ($_.Ms / $f) }) -join ' '
  $unnamedAgg = @{}
  foreach ($r in ($rows | Where-Object { -not $_.L })) {
    $lbl = ResolveAddr $mods $r.Addr
    $unnamedAgg[$lbl] = $(if ($unnamedAgg.ContainsKey($lbl)) { $unnamedAgg[$lbl] } else { 0.0 }) + $r.Ms
  }
  $unnamedParts = ($unnamedAgg.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 5 | % { "{0}={1:N1}" -f $_.Key, ($_.Value / $f) }) -join ' '
  $unnamedSuffix = if ($unnamedParts) { " | unnamed: $unnamedParts" } else { "" }
  Add-Content $out ("{0,-12} fps={1,5} cpu/frame={2,6:N1} ms ({3:N2} cores) | {4}{5}" -f $s, $fps, ($tot / $f), ($tot / 1000.0), $parts, $unnamedSuffix)
}
Add-Content $out "end $(Get-Date -Format HH:mm:ss)"
if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force }
