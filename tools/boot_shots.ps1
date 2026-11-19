param([string]$tag='boot', [string]$extraEnv='', [int]$every=4, [int]$count=12)
Set-Location C:\ApeEscape3_Recomp
Add-Type -AssemblyName System.Drawing
Add-Type -Namespace Win -Name Shot3 -MemberDefinition @"
[System.Runtime.InteropServices.StructLayout(System.Runtime.InteropServices.LayoutKind.Sequential)]
public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
[System.Runtime.InteropServices.DllImport("user32.dll")] public static extern bool GetWindowRect(System.IntPtr h, out RECT r);
[System.Runtime.InteropServices.DllImport("user32.dll")] public static extern bool PrintWindow(System.IntPtr h, System.IntPtr hdc, uint flags);
"@
function Capture([IntPtr]$hwnd, [string]$path) { $r = New-Object Win.Shot3+RECT; [void][Win.Shot3]::GetWindowRect($hwnd, [ref]$r); $w=$r.Right-$r.Left; $h=$r.Bottom-$r.Top; if ($w -le 0) { return }
  $b = New-Object System.Drawing.Bitmap($w,$h); $g=[System.Drawing.Graphics]::FromImage($b); $hdc=$g.GetHdc(); [void][Win.Shot3]::PrintWindow($hwnd,$hdc,2); $g.ReleaseHdc($hdc); $g.Dispose()
  $s=New-Object System.Drawing.Bitmap(400,[int]($h*400/$w)); $g=[System.Drawing.Graphics]::FromImage($s); $g.DrawImage($b,0,0,$s.Width,$s.Height); $g.Dispose(); $s.Save($path); $s.Dispose(); $b.Dispose() }
New-Item -ItemType Directory -Force logs\shots | Out-Null
$env:PS2X_GS_ASYNC='1';$env:PS2X_VIF1_ASYNC='1';$env:PS2X_GS_VULKAN='1';$env:PS2X_SG2_LLE='1';$env:PS2X_LOG_SYNC='1';$env:PS2X_WINDOW_BACKGROUND='1';$env:PS2X_EEDC='1'
$env:PS2X_PAD_PLAY='logs\to_hub_fresh.padrec'
foreach ($kv in ($extraEnv.Split(';') | Where-Object { $_ })) { $k,$v = $kv.Split('=',2); Set-Item -Path "env:$k" -Value $v }
$p = Start-Process build\PS2Recomp\ps2xRuntime\ps2EntryRunner_dev.exe -ArgumentList 'SCUS_975.01' -RedirectStandardOutput "logs\${tag}_run.txt" -RedirectStandardError "logs\${tag}_err.txt" -PassThru
for ($i=1; $i -le $count; $i++) { Start-Sleep $every; if ($p.HasExited) { "exited"; break }; $p.Refresh(); Capture $p.MainWindowHandle ("logs\shots\{0}_{1:D2}.png" -f $tag,$i) }
if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force }
