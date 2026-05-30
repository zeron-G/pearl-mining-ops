$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$WslDistro = "Ubuntu"
$EnvFile = Join-Path $Root ".env"
if (Test-Path $EnvFile) {
  foreach ($Line in Get-Content $EnvFile) {
    if ($Line -match "^WSL_DISTRO=(.+)$") { $WslDistro = $Matches[1].Trim().Trim("'").Trim('"') }
  }
}
$AlphaDir = Join-Path $Root "alphapool"
$PearlHashDir = Join-Path $Root "pearlhash"

New-Item -ItemType Directory -Force -Path $AlphaDir, $PearlHashDir | Out-Null

$AlphaMiner = Join-Path $AlphaDir "alpha-miner"
$PearlHashMiner = Join-Path $PearlHashDir "pearl-miner"

Write-Host "Downloading AlphaPool miner..."
Invoke-WebRequest -Uri "https://pearl.alphapool.tech/downloads/alpha-miner" -OutFile $AlphaMiner

Write-Host "Downloading PearlHash miner..."
Invoke-WebRequest -Uri "https://pearlhash.xyz/downloads/pearl-miner-v10" -OutFile $PearlHashMiner

$AlphaWsl = (wsl.exe -d $WslDistro -- wslpath -a $AlphaMiner).Trim()
$PearlHashWsl = (wsl.exe -d $WslDistro -- wslpath -a $PearlHashMiner).Trim()
wsl.exe -d $WslDistro -- chmod +x $AlphaWsl $PearlHashWsl

Write-Host "Done."
Write-Host "AlphaPool miner: $AlphaMiner"
Write-Host "PearlHash miner: $PearlHashMiner"
