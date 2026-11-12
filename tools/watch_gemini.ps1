# Live view of a background Antigravity job: job state, files Gemini touched, build progress.
# Usage:  powershell -File tools\watch_gemini.ps1 [-Job c4328ca7] [-Every 10]
param([string]$Job = "", [int]$Every = 10)

$companion = "$env:USERPROFILE\.claude\plugins\cache\antigravity\antigravity\2.0.0\scripts\antigravity-companion.mjs"
$repo = "C:\ApeEscape3_Recomp"
while ($true) {
    Clear-Host
    Write-Host ("=== {0}  (Ctrl+C to stop) ===" -f (Get-Date -Format "HH:mm:ss")) -ForegroundColor Cyan
    Write-Host "`n-- Antigravity job --" -ForegroundColor Yellow
    $st = & node $companion status $Job 2>$null | Where-Object { $_ -notmatch "DEP0190|trace-deprecation" }
    $st | Select-Object -First 14
    Write-Host "`n-- Files changed in PS2Recomp (git status) --" -ForegroundColor Yellow
    git -C "$repo\PS2Recomp" status --short | Select-Object -First 15
    Write-Host "`n-- Latest commits (main repo / fork) --" -ForegroundColor Yellow
    git -C $repo log --oneline -1
    git -C "$repo\PS2Recomp" log --oneline -1
    Write-Host "`n-- Build --" -ForegroundColor Yellow
    $bt = Join-Path $repo "build_output.tmp"
    if (Test-Path $bt) {
        $i = Get-Item $bt
        Write-Host ("build_output.tmp: {0} KB, last write {1:HH:mm:ss} ({2:N0}s ago)" -f [math]::Round($i.Length/1KB,1), $i.LastWriteTime, ((Get-Date) - $i.LastWriteTime).TotalSeconds)
        Get-Content $bt -Tail 4
    } else { Write-Host "no build running / finished (build_output.tmp absent)" }
    $cc = (Get-Process cl, cc1plus, clang, link, cmake, ninja, msbuild -ErrorAction SilentlyContinue | Measure-Object).Count
    Write-Host ("compiler/build processes alive: {0}" -f $cc)
    Start-Sleep -Seconds $Every
}
