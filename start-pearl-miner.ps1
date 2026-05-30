$WslDistro = "Ubuntu"
$EnvFile = Join-Path $PSScriptRoot ".env"
if (Test-Path $EnvFile) {
  foreach ($Line in Get-Content $EnvFile) {
    if ($Line -match "^WSL_DISTRO=(.+)$") { $WslDistro = $Matches[1].Trim().Trim("'").Trim('"') }
  }
}
$Script = Join-Path $PSScriptRoot "alphapool\start-pearl-miner.sh"
if ((Resolve-Path $Script).Path -match "^([A-Za-z]):\\(.*)$") {
  $WslScript = "/mnt/$($Matches[1].ToLower())/$($Matches[2] -replace '\\','/')"
}
wsl.exe -d $WslDistro -- bash $WslScript
