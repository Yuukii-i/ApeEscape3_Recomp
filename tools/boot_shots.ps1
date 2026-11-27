# boot_shots.ps1 - capture the boot-to-hub sequence at fixed intervals and build a contact sheet
# Usage: powershell -File tools\boot_shots.ps1 [-tag boot] [-interval 3] [-count 45] [-extraEnv 'K=V;K2=V2']
param(
    [string]$tag = 'boot',
    [string]$exe = 'build_avx2\PS2Recomp\ps2xRuntime\ps2EntryRunner_dev.exe',
    [string]$extraEnv = '',
    [int]$interval = 3,
    [int]$count = 45,
    [string]$padrec = 'logs\to_hub_fresh.padrec',
    [string]$winSize = ''
)

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

function Save-BlackPlaceholder([string]$path) {
    $bmp = New-Object System.Drawing.Bitmap(16, 16)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.Clear([System.Drawing.Color]::Black)
    $g.Dispose()
    $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
    $bmp.Dispose()
}

function Capture([IntPtr]$hwnd, [string]$path) {
    if ($hwnd -eq [IntPtr]::Zero) { Save-BlackPlaceholder $path; return }
    try {
        $r = New-Object Win.Shot2+RECT; [void][Win.Shot2]::GetWindowRect($hwnd, [ref]$r)
        $w = $r.Right - $r.Left; $h = $r.Bottom - $r.Top
        if ($w -le 0 -or $h -le 0) { Save-BlackPlaceholder $path; return }
        $bmp = New-Object System.Drawing.Bitmap($w, $h); $g = [System.Drawing.Graphics]::FromImage($bmp)
        $hdc = $g.GetHdc(); $ok = [Win.Shot2]::PrintWindow($hwnd, $hdc, 2); $g.ReleaseHdc($hdc); $g.Dispose()
        if (-not $ok) { $bmp.Dispose(); Save-BlackPlaceholder $path; return }
        $tw = 800; $th = [int][math]::Round($h * $tw / $w); $small = New-Object System.Drawing.Bitmap($tw, $th)
        $g = [System.Drawing.Graphics]::FromImage($small); $g.InterpolationMode = 'HighQualityBicubic'; $g.DrawImage($bmp, 0, 0, $tw, $th); $g.Dispose()
        $small.Save($path, [System.Drawing.Imaging.ImageFormat]::Png); $small.Dispose(); $bmp.Dispose()
    } catch {
        Save-BlackPlaceholder $path
    }
}

Get-Process -Name 'ps2EntryRunner_dev', 'base_overnight' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

New-Item -ItemType Directory -Force logs\shots | Out-Null
$err = "logs\${tag}_err.txt"; $run = "logs\${tag}_run.txt"
Remove-Item logs\dev_cmd.txt -ErrorAction SilentlyContinue

$env:PS2X_GS_ASYNC='1';$env:PS2X_VIF1_ASYNC='1';$env:PS2X_GS_VULKAN='1';$env:PS2X_SG2_LLE='1';$env:PS2X_LOG_SYNC='1';$env:PS2X_WINDOW_BACKGROUND='1';$env:PS2X_NO_CONFIG='1'
$env:PS2X_EEDC='1';$env:PS2X_EEDC_CHECK='0';$env:PS2X_EEDC_CENSUS='0';$env:PS2X_EEDC_DISABLE='';$env:PS2X_EEDC_ONLY='';$env:PS2X_EEDC_CHECK_JALR=''
$env:PS2X_MC='';$env:PS2X_PAD_REC='';$env:PS2X_PAD_PLAY=$padrec;$env:PS2X_PAD_STOP_MARK=''
$env:PS2X_DEV_CMD='logs\dev_cmd.txt'
foreach ($kv in ($extraEnv.Split(';') | Where-Object { $_ })) { $k,$v = $kv.Split('=',2); Set-Item -Path "env:$k" -Value $v }

$p = Start-Process $exe -ArgumentList 'SCUS_975.01' -RedirectStandardOutput $run -RedirectStandardError $err -PassThru
$sized = $false

for ($i = 0; $i -lt $count; $i++) {
    if ($i -gt 0) { Start-Sleep $interval }
    $outPath = "logs\shots\${tag}_boot_{0:D2}.png" -f $i
    if ($p.HasExited) {
        Save-BlackPlaceholder $outPath
        continue
    }
    $p.Refresh()
    $hwnd = $p.MainWindowHandle
    if ($winSize -and -not $sized -and $hwnd -ne [IntPtr]::Zero) {
        $wh = $winSize.Split('x')
        [void][Win.Shot2]::SetWindowPos($hwnd, [IntPtr]1, 0, 0, [int]$wh[0], [int]$wh[1], 0x0012)
        $sized = $true
    }
    Capture $hwnd $outPath
}

if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force }

$prefix = "logs\shots\${tag}_boot_"
$sheet = python tools\contact_sheet.py $prefix 9 $interval
Write-Output $sheet
