# warp_tour.ps1 - boot to hub with a padrec, then warp through stages via the dev console (logs\dev_cmd.txt).
# Params: -tag name (logs\<tag>_run/_err/_summary.txt), -padrec, -hold seconds after each warp executes,
#         -check N (PS2X_EEDC_CHECK), -only 'a,b,c' (stage subset), -startAt index, -extraEnv 'K=V;K2=V2'
param([string]$tag = 'tour', [string]$padrec = 'logs\to_hub_fresh.padrec', [int]$hold = 3, [int]$check = 0,
      [string]$only = '', [int]$startAt = 1, [string]$extraEnv = '', [string]$exe = 'build\PS2Recomp\ps2xRuntime\ps2EntryRunner_dev.exe')
$ErrorActionPreference = 'Continue'
Set-Location C:\ApeEscape3_Recomp
$all = @(
 'travel_a','travel_b',
 'seaside_a','seaside_b','seaside_d','woods_a','woods_b','woods_c','woods_d',
 'castle_a','castle_b','castle_c','castle_d','castle_e','castle_f','boss1_a',
 'ciscocity_a','ciscocity_b','ciscocity_c','ciscocity_d','ciscocity_e',
 'studio_a','studio_b','studio_c','studio_d','studio_e','studio_f','studio_g',
 'halloween_a','halloween_b','halloween_c','halloween_d','halloween_e','halloween_f',
 'western_a','western_b','western_c','western_d','western_e','western_f','boss2_a',
 'onsen_a','onsen_b','onsen_c','onsen_d','onsen_e',
 'snowfesta_a','snowfesta_b','snowfesta_c','snowfesta_d','snowfesta_e','snowfesta_f','snowfesta_g',
 'asia_a','asia_b','asia_d','asia_e','asia_f','boss3_a',
 'heaven_a','heaven_b','heaven_c','heaven_d','heaven_e',
 'toyhouse_a','toyhouse_b','toyhouse_c','toyhouse_d','toyhouse_e','toyhouse_f','toyhouse_g','toyhouse_h',
 'iceland_a','iceland_b','iceland_d','iceland_e','iceland_f',
 'arabian_a','arabian_b','arabian_c','arabian_e','arabian_f','arabian_g','boss4_a',
 'edotown_a','edotown_b','edotown_c','edotown_d','edotown_e','edotown_f',
 'plane_a','plane_b','plane_c','plane_d','plane_e','plane_f','plane_g','plane_h',
 'hong_a','hong_b','hong_c','hong_d','hong_e','hong_f','hong_g','hong_h',
 'boss5_a','boss5_b','boss5_c','bay_a','bay_b','bay_c','bay_d','bay_e','bay_f',
 'tomo_a','tomo_b','tomo_c','tomo_e','tomo_f','tomo_g','tomo_h','boss6_a',
 'tb_ara','tb_cow','tb_hro','tb_kni','tb_kun','tb_nin','tb_saru','zero_a',
 'tomo_i','tomo_j','specter1_a','specter1_b','specter1_c','specter2_a',
 'space_a','space_b','space_c','space_d','space_e','space_f','space_g','space_h','space_i','space_j','space_k'
)  # iceland_c excluded (W1 crash), mgs*/snake_a/tg_* excluded
$stages = if ($only) { $only.Split(',') } else { $all }
$err = "logs\${tag}_err.txt"; $run = "logs\${tag}_run.txt"; $sum = "logs\${tag}_summary.txt"
Set-Content $sum "tour $tag start $(Get-Date -Format HH:mm:ss) stages=$($stages.Count) hold=$hold check=$check"
Remove-Item logs\dev_cmd.txt -ErrorAction SilentlyContinue
$env:PS2X_GS_ASYNC='1';$env:PS2X_VIF1_ASYNC='1';$env:PS2X_GS_VULKAN='1';$env:PS2X_SG2_LLE='1';$env:PS2X_LOG_SYNC='1';$env:PS2X_WINDOW_BACKGROUND='1'
$env:PS2X_EEDC='1';$env:PS2X_EEDC_CHECK="$check";$env:PS2X_EEDC_CENSUS='1';$env:PS2X_EEDC_DISABLE='';$env:PS2X_EEDC_ONLY='';$env:PS2X_EEDC_CHECK_JALR=''
$env:PS2X_MC='';$env:PS2X_PAD_REC='';$env:PS2X_PAD_PLAY=$padrec;$env:PS2X_PAD_STOP_MARK=''
foreach ($kv in ($extraEnv.Split(';') | Where-Object { $_ })) { $k,$v = $kv.Split('=',2); Set-Item -Path "env:$k" -Value $v }
$p = Start-Process $exe -ArgumentList 'SCUS_975.01' -RedirectStandardOutput $run -RedirectStandardError $err -PassThru
$t0 = Get-Date
while (((Get-Date) - $t0).TotalSeconds -lt 120 -and -not $p.HasExited) {
  if (Select-String -Path $err -Pattern 'stage/travel_a/actionseq' -Quiet) { break }; Start-Sleep 1 }
Start-Sleep 8
$i = 0
foreach ($s in $stages) {
  $i++
  if ($i -lt $startAt) { continue }
  if ($p.HasExited) { Add-Content $sum "GAME EXITED before #$i $s (code $($p.ExitCode))"; break }
  $before = (Select-String -Path $err -Pattern "\[dev\] warp -> " | Measure-Object).Count
  Add-Content logs\dev_cmd.txt "warp $s"
  $t1 = Get-Date
  while (((Get-Date) - $t1).TotalSeconds -lt 30 -and -not $p.HasExited) {
    if ((Select-String -Path $err -Pattern "\[dev\] warp -> " | Measure-Object).Count -gt $before) { break }
    Start-Sleep -Milliseconds 300 }
  Start-Sleep $hold
  Add-Content logs\dev_cmd.txt 'where'
  Start-Sleep -Milliseconds 600
  $w = Select-String -Path $err -Pattern "\[dev\] warp -> '$s'" -Quiet
  $wh = (Select-String -Path $err -Pattern "\[dev\] where " | Select-Object -Last 1).Line
  $fps = (Select-String -Path $err,$run -Pattern '\[fps\] FPS: (\d+)' | Select-Object -Last 1)
  $f = if ($fps) { $fps.Matches[0].Groups[1].Value } else { '?' }
  $st = if ($wh -match "stage='([^']*)'") { $matches[1] } else { '?' }
  Add-Content $sum ("#{0} {1}: warped={2} where={3} fps={4} alive={5}" -f $i, $s, $w, $st, $f, (-not $p.HasExited))
}
Add-Content $sum "tour end $(Get-Date -Format HH:mm:ss)"
Start-Sleep 5
if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force }
