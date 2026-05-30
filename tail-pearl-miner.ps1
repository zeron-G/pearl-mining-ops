$WslDistro = "Ubuntu"
$EnvFile = Join-Path $PSScriptRoot ".env"
if (Test-Path $EnvFile) {
  foreach ($Line in Get-Content $EnvFile) {
    if ($Line -match "^WSL_DISTRO=(.+)$") { $WslDistro = $Matches[1].Trim().Trim("'").Trim('"') }
  }
}
$Log = Join-Path $PSScriptRoot "alphapool\pearl-miner.log"
if ((Resolve-Path $Log).Path -match "^([A-Za-z]):\\(.*)$") {
  $WslLog = "/mnt/$($Matches[1].ToLower())/$($Matches[2] -replace '\\','/')"
}
wsl.exe -d $WslDistro -- tail -f $WslLog
