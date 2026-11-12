# tools/shot.ps1 - screenshot of the game window at the replay's shop spot
param(
    [string]$Exe = "build\PS2Recomp\ps2xRuntime\ps2EntryRunner_dev.exe",
    [hashtable]$Env = @{},
    [string]$Pad = "logs\selftest.padrec",
    [string]$Tag = "shot",
    [int]$Delay = 4,
    [int]$Count = 3,
    [int]$Gap = 2
)

$ErrorActionPreference = "Continue"
Set-Location "C:\ApeEscape3_Recomp"
Add-Type -AssemblyName System.Drawing

if (-not ([System.Management.Automation.PSTypeName]'Win.Shot').Type) {
    Add-Type -Namespace Win -Name Shot -MemberDefinition @'
[System.Runtime.InteropServices.StructLayout(System.Runtime.InteropServices.LayoutKind.Sequential)]
public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
[System.Runtime.InteropServices.DllImport("user32.dll")] public static extern bool GetWindowRect(System.IntPtr h, out RECT r);
[System.Runtime.InteropServices.DllImport("user32.dll")] public static extern bool PrintWindow(System.IntPtr h, System.IntPtr hdc, uint flags);
'@
}

function Test-Uniform([System.Drawing.Bitmap]$bmp) {
    $first = $null
    $w = $bmp.Width; $h = $bmp.Height
    for ($i = 0; $i -lt 20; $i++) {
        for ($j = 0; $j -lt 20; $j++) {
            $px = $bmp.GetPixel([int](($w - 1) * $i / 19), [int](($h - 1) * $j / 19)).ToArgb()
            if ($null -eq $first) { $first = $px }
            elseif ($px -ne $first) { return $false }
        }
    }
    return $true
}

function Capture-Window([IntPtr]$hwnd, [string]$path) {
    $r = New-Object Win.Shot+RECT
    [void][Win.Shot]::GetWindowRect($hwnd, [ref]$r)
    $w = $r.Right - $r.Left
    $h = $r.Bottom - $r.Top
    if ($w -le 0 -or $h -le 0) { return $false }
    $bmp = New-Object System.Drawing.Bitmap($w, $h)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $hdc = $g.GetHdc()
    [void][Win.Shot]::PrintWindow($hwnd, $hdc, 2)
    $g.ReleaseHdc($hdc)
    $g.Dispose()
    if (Test-Uniform $bmp) {
        $g = [System.Drawing.Graphics]::FromImage($bmp)
        $g.CopyFromScreen($r.Left, $r.Top, 0, 0, (New-Object System.Drawing.Size($w, $h)))
        $g.Dispose()
    }
    $tw = 960
    $th = [int][math]::Round($h * $tw / $w)
    $small = New-Object System.Drawing.Bitmap($tw, $th)
    $g = [System.Drawing.Graphics]::FromImage($small)
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.DrawImage($bmp, 0, 0, $tw, $th)
    $g.Dispose()
    $small.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
    $small.Dispose()
    $bmp.Dispose()
    return $true
}

if (-not (Test-Path "logs")) { New-Item -ItemType Directory -Path "logs" -Force | Out-Null }

# Clean slate for PS2X_* env vars; save current to restore afterwards
$savedEnv = @{}
Get-ChildItem env:PS2X_* -ErrorAction SilentlyContinue | ForEach-Object {
    $savedEnv[$_.Name] = $_.Value
    Remove-Item "env:$($_.Name)" -Force -ErrorAction SilentlyContinue
}

$proc = $null
$saved = @()
try {
    $env:PS2X_GS_ASYNC = "1"
    $env:PS2X_VIF1_ASYNC = "1"
    $env:PS2X_GS_VULKAN = "1"
    $env:PS2X_VU1_KERNEL = "1"
    $env:PS2X_PRESENT_ASYNC = "1"
    $env:PS2X_PRESENT_GPU = "1"
    $env:PS2X_PAD_PLAY = $Pad
    $env:PS2X_PAD_PLAY_HOLD = "1"
    if ($Env) {
        foreach ($key in $Env.Keys) { Set-Item "env:$key" "$($Env[$key])" }
    }

    $outPath = "logs\shot_${Tag}.out"
    $errPath = "logs\shot_${Tag}.err"
    if (Test-Path $outPath) { Remove-Item $outPath -Force -ErrorAction SilentlyContinue }
    if (Test-Path $errPath) { Remove-Item $errPath -Force -ErrorAction SilentlyContinue }

    Write-Host "Starting $Exe ..."
    $proc = Start-Process -FilePath $Exe -ArgumentList "SCUS_975.01" -WorkingDirectory "C:\ApeEscape3_Recomp" -RedirectStandardOutput $outPath -RedirectStandardError $errPath -PassThru

    $started = $false
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    while ($sw.Elapsed.TotalSeconds -lt 300) {
        if ($proc.HasExited) { break }
        if (Test-Path $errPath) {
            try {
                $fs = [System.IO.FileStream]::new($errPath, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
                $sr = [System.IO.StreamReader]::new($fs)
                $text = $sr.ReadToEnd()
                $sr.Close(); $fs.Close()
                if ($text -match "\[bench\] START") { $started = $true; break }
            } catch {}
        }
        Start-Sleep -Seconds 1
    }

    if (-not $started) {
        Write-Host "ERROR: [bench] START not seen (exited=$($proc.HasExited))"
    }
    else {
        Start-Sleep -Seconds $Delay
        $hwnd = [IntPtr]::Zero
        $sw2 = [System.Diagnostics.Stopwatch]::StartNew()
        while ($sw2.Elapsed.TotalSeconds -lt 10) {
            $proc.Refresh()
            $hwnd = $proc.MainWindowHandle
            if ($hwnd -ne [IntPtr]::Zero) { break }
            Start-Sleep -Milliseconds 500
        }
        if ($hwnd -eq [IntPtr]::Zero) {
            Write-Host "ERROR: no MainWindowHandle"
        }
        else {
            for ($n = 1; $n -le $Count; $n++) {
                $png = "logs\shot_${Tag}_${n}.png"
                if (Capture-Window $hwnd $png) { $saved += $png } else { Write-Host "capture $n failed" }
                if ($n -lt $Count) { Start-Sleep -Seconds $Gap }
            }
        }
    }
}
finally {
    if ($proc -and -not $proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
    Get-ChildItem env:PS2X_* -ErrorAction SilentlyContinue | ForEach-Object { Remove-Item "env:$($_.Name)" -Force -ErrorAction SilentlyContinue }
    foreach ($k in $savedEnv.Keys) { Set-Item "env:$k" $savedEnv[$k] }
}

foreach ($p in $saved) { Write-Host (Resolve-Path $p).Path }
