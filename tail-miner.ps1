$EnvFile = Join-Path $PSScriptRoot ".env"
$DefaultPool = "pearlhash"

if (Test-Path $EnvFile) {
  foreach ($Line in Get-Content $EnvFile) {
    if ($Line -match "^DEFAULT_POOL=(.+)$") {
      $DefaultPool = $Matches[1].Trim()
    }
  }
}

switch ($DefaultPool.ToLowerInvariant()) {
  "pearlhash" { & (Join-Path $PSScriptRoot "tail-pearlhash-miner.ps1") }
  "alphapool" { & (Join-Path $PSScriptRoot "tail-pearl-miner.ps1") }
  default { throw "Unsupported DEFAULT_POOL: $DefaultPool" }
}
