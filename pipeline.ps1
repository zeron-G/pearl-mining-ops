param(
  [Parameter(Mandatory=$true,Position=0)]
  [ValidateSet('setup','start','status','logs','stop')]
  [string]$Action
)
$ErrorActionPreference = 'Stop'
$cfg = @{}
$path = Join-Path $PSScriptRoot '.env'
if ($Action -eq 'setup' -and !(Test-Path $path)) {
  [IO.File]::Copy((Join-Path $PSScriptRoot '.env.example'), $path, $false)
}
foreach ($line in Get-Content -LiteralPath $path) {
  if ($line -match '^(WSL_DISTRO|DEFAULT_POOL|PEARLHASH_ENGINE|PEARL_ADDRESS)=(.*)$') {
    $cfg[$Matches[1]] = $Matches[2].Trim()
  }
}
$distro = $cfg.WSL_DISTRO
if (!$distro -or $distro -notmatch '^[a-zA-Z0-9_.-]+$') { throw 'Set WSL_DISTRO in .env.' }
function Run-Wsl([string[]]$Arguments) {
  & wsl.exe -d $distro --cd $PSScriptRoot -- @Arguments
  if ($LASTEXITCODE -ne 0) { throw "WSL step failed ($LASTEXITCODE)." }
}
switch ($Action) {
  setup { Run-Wsl @('bash','scripts/install-wildrig.sh') }
  start {
    if ($cfg.DEFAULT_POOL -ne 'pearlhash' -or $cfg.PEARLHASH_ENGINE -ne 'wildrig') {
      throw 'Set DEFAULT_POOL=pearlhash and PEARLHASH_ENGINE=wildrig in .env.'
    }
    Run-Wsl @('bash','scripts/install-wildrig.sh')
    Run-Wsl @('nvidia-smi','-L')
    & (Join-Path $PSScriptRoot 'start-pearlhash-miner.ps1')
  }
  stop { Run-Wsl @('bash','pearlhash/stop-pearlhash-miner.sh') }
  logs { Run-Wsl @('tail','-n','30','-F','pearlhash/pearlhash-miner.log') }
  status {
    Run-Wsl @('bash','-c','ps -C wildrig-multi,alpha-miner,pearl-miner -o pid,etime,comm || true')
    if ($cfg.PEARL_ADDRESS -notmatch '^prl1p[a-z0-9]{58}$') { Write-Host 'Pool status: no configured address.'; return }
    try {
      $pool = Invoke-RestMethod ("https://pearlhash.xyz/api/account/" + $cfg.PEARL_ADDRESS) -TimeoutSec 8
      Write-Host "Pool workers: $(@($pool.connected_workers | Where-Object { $_ }).Count); balance entries: $(@($pool.balance_transactions | Where-Object { $_ }).Count). Exchange credit is not verified."
    } catch { Write-Warning 'Pool status unavailable; check network or wait for the first accepted share.' }
  }
}
