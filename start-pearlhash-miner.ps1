$WslDistro = "Ubuntu"
$EnvFile = Join-Path $PSScriptRoot ".env"
if (Test-Path $EnvFile) {
  foreach ($Line in Get-Content $EnvFile) {
    if ($Line -match "^WSL_DISTRO=(.+)$") { $WslDistro = $Matches[1].Trim().Trim("'").Trim('"') }
  }
}
$Script = Join-Path $PSScriptRoot "pearlhash\start-pearlhash-miner.sh"
if ((Resolve-Path $Script).Path -match "^([A-Za-z]):\\(.*)$") {
  $WslScript = "/mnt/$($Matches[1].ToLower())/$($Matches[2] -replace '\\','/')"
}
if ((Test-Path $EnvFile) -and (Select-String -Quiet -Path $EnvFile -Pattern '^PEARLHASH_ENGINE=wildrig\s*$')) {
  $runDir = Join-Path $PSScriptRoot 'downloads\wildrig-0.52.3'
  if ($WslDistro -notmatch '^[a-zA-Z0-9_.-]+$') { throw 'Unsupported WSL distro name for trial' }
  $p = Start-Process -FilePath 'wsl.exe' -WorkingDirectory $PSScriptRoot -ArgumentList @('-d', $WslDistro, '--', 'bash', 'pearlhash/start-pearlhash-miner.sh') -RedirectStandardOutput (Join-Path $runDir 'launch-out.log') -RedirectStandardError (Join-Path $runDir 'launch-err.log') -WindowStyle Hidden -PassThru
  if ($p.WaitForExit(2200)) { throw "Trial ended during startup (exit $($p.ExitCode)). Check for another miner and review the log." }
  Write-Host "PearlHash trial launched. Use stop-miner.ps1 to stop."
} else {
  wsl.exe -d $WslDistro -- bash $WslScript
}
