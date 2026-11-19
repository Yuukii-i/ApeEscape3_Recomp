# warp_shot.ps1 - boot to hub (padrec), warp to each stage, settle, screenshot the game window (PrintWindow) -> logs\shots\<tag>_<stage>.png
# Usage: powershell -File tools\warp_shot.ps1 -tag rd1 -only 'travel_a,toyhouse_a' -extraEnv 'PS2X_RD_VIEW=1'
param([string]$tag = 'shot', [string]$padrec = 'logs\to_hub_fresh.padrec', [int]$settle = 8,
      [string]$only = 'travel_a,toyhouse_a', [string]$extraEnv = '', [string]$winSize = '', [string]$exe = 'build\PS2Recomp\ps2xRuntime\ps2EntryRunner_dev.exe')
$ErrorActionPreference = 'Continue'
Set-Location C:\ApeEscape3_Recomp
Add-Type -AssemblyName System.Drawing
Add-Type -Namespace Win -Name Shot2 -MemberDefinition @'
[System.Runtime.InteropServices.StructLayout(System.Runtime.InteropServices.LayoutKind.Sequential)]
public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
[System.Runtime.InteropServices.DllImport("user32.dll")] public static extern bool GetWindowRect(System.IntPtr h, out RECT r);
[System.Runtime.InteropServices.DllImport("user32.dll")] public static extern bool PrintWindow(System.IntPtr h, System.IntPtr hdc, uint flags);
[System.Runtime.InteropServices.DllImport("user32.dll")] public static extern bool SetWindowPos(System.IntPtr h, System.IntPtr after, int x, int y, int cx, int cy, uint flags);
'@ -ErrorAction SilentlyContinue
function Capture([IntPtr]$hwnd, [string]$path) {
  $r = New-Object Win.Shot2+RECT; [void][Win.Shot2]::GetWindowRect($hwnd, [ref]$r)
  $w = $r.Right - $r.Left; $h = $r.Bottom - $r.Top; if ($w -le 0 -or $h -le 0) { return }
  $bmp = New-Object System.Drawing.Bitmap($w, $h); $g = [System.Drawing.Graphics]::FromImage($bmp)
  $hdc = $g.GetHdc(); [void][Win.Shot2]::PrintWindow($hwnd, $hdc, 2); $g.ReleaseHdc($hdc); $g.Dispose()
  $tw = 800; $th = [int][math]::Round($h * $tw / $w); $small = New-Object System.Drawing.Bitmap($tw, $th)
  $g = [System.Drawing.Graphics]::FromImage($small); $g.InterpolationMode = 'HighQualityBicubic'; $g.DrawImage($bmp, 0, 0, $tw, $th); $g.Dispose()
  $small.Save($path, [System.Drawing.Imaging.ImageFormat]::Png); $small.Dispose(); $bmp.Dispose() }
New-Item -ItemType Directory -Force logs\shots | Out-Null
$err = "logs\${tag}_err.txt"; $run = "logs\${tag}_run.txt"
Remove-Item logs\dev_cmd.txt -ErrorAction SilentlyContinue
$env:PS2X_GS_ASYNC='1';$env:PS2X_VIF1_ASYNC='1';$env:PS2X_GS_VULKAN='1';$env:PS2X_SG2_LLE='1';$env:PS2X_LOG_SYNC='1';$env:PS2X_WINDOW_BACKGROUND='1'
$env:PS2X_EEDC='1';$env:PS2X_EEDC_CHECK='0';$env:PS2X_EEDC_CENSUS='0'
$env:PS2X_MC='';$env:PS2X_PAD_REC='';$env:PS2X_PAD_PLAY=$padrec;$env:PS2X_PAD_STOP_MARK=''
foreach ($kv in ($extraEnv.Split(';') | Where-Object { $_ })) { $k,$v = $kv.Split('=',2); Set-Item -Path "env:$k" -Value $v }
$p = Start-Process $exe -ArgumentList 'SCUS_975.01' -RedirectStandardOutput $run -RedirectStandardError $err -PassThru
$t0 = Get-Date
while (((Get-Date) - $t0).TotalSeconds -lt 120 -and -not $p.HasExited) { if (Select-String -Path $err -Pattern 'stage/travel_a/actionseq' -Quiet) { break }; Start-Sleep 1 }
Start-Sleep 8
if ($winSize) { $wh = $winSize.Split('x'); $p.Refresh(); [void][Win.Shot2]::SetWindowPos($p.MainWindowHandle, [IntPtr]1, 0, 0, [int]$wh[0], [int]$wh[1], 0x0012) } # HWND_BOTTOM, NOMOVE|NOACTIVATE
foreach ($s in $only.Split(',')) {
  if ($p.HasExited) { "GAME EXITED before $s"; break }
  $before = (Select-String -Path $err -Pattern "\[dev\] warp -> " | Measure-Object).Count
  Add-Content logs\dev_cmd.txt "warp $s"
  $t1 = Get-Date
  while (((Get-Date) - $t1).TotalSeconds -lt 30 -and -not $p.HasExited) { if ((Select-String -Path $err -Pattern "\[dev\] warp -> " | Measure-Object).Count -gt $before) { break }; Start-Sleep -Milliseconds 300 }
  Start-Sleep $settle
  $p.Refresh(); Capture $p.MainWindowHandle "logs\shots\${tag}_$s.png"; "shot $s"
}
if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force } else { "exit code $($p.ExitCode)" }
