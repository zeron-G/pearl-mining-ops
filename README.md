# Pearl Mining Ops

Pearl Mining Ops is a local operations toolkit for running Pearl miners,
watching pool/account status, checking Pearl addresses, and preparing guarded
SafeTrade automation. It is designed for a Windows + WSL setup with an NVIDIA
GPU, but the Python CLI is intentionally small and portable.

The project is safe by default:

- real API keys, wallet addresses, logs, PIDs, screenshots, and miner binaries stay out of git
- live trading is disabled unless explicitly enabled
- withdrawals are disabled unless an endpoint is verified and explicitly enabled
- SafeTrade calls support dry-run diagnostics before any order is placed

## Features

- Start, stop, and tail AlphaPool or PearlHash miners.
- Use `.env` as the single local configuration file.
- Monitor miner process, GPU load, logs, PearlHash account pending rewards, and Pearl explorer balance.
- Check SafeTrade API authentication using both the official `members/me` endpoint and the community `balances/spot` endpoint.
- Prepare guarded PRL sell orders and USDT withdrawal adapters.
- Serve a local browser dashboard at `http://127.0.0.1:8787`.

## Repository Layout

```text
.
├── alphapool/                 # AlphaPool launch scripts
├── pearlhash/                 # PearlHash launch scripts
├── scripts/                   # Setup/download helpers
├── src/pearl_ops/             # Python package and dashboard server
├── src/pearl_ops/static/      # Local dashboard UI
├── .env.example               # Public config template
├── SECURITY.md                # Safety rules for secrets and live actions
└── pyproject.toml             # Python package metadata
```

Ignored local files include `.env`, `*.log`, `*.pid`, miner binaries, screenshots,
virtual environments, and Python caches.

## Requirements

- Windows PowerShell
- WSL2 with an Ubuntu distro
- NVIDIA driver visible to WSL
- Python 3.10+
- Git
- Optional: GitHub CLI for publishing

Check WSL GPU visibility:

```powershell
wsl.exe -d Ubuntu -- nvidia-smi
```

## Setup

Clone the repository and install the CLI:

```powershell
git clone <repo-url>
cd pearl-mining-ops
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

Create local config:

```powershell
Copy-Item .env.example .env
notepad .env
```

Minimum useful values:

```text
PEARL_ADDRESS=prl1p...
DEFAULT_POOL=pearlhash
WSL_DISTRO=Ubuntu
DRY_RUN=true
```

SafeTrade values are optional until you want exchange diagnostics:

```text
SAFETRADE_API_KEY=
SAFETRADE_API_SECRET=
SAFETRADE_PRL_MARKET=prlusdt
```

Keep `DRY_RUN=true` while testing.

## Download Miners

Miner binaries are intentionally not committed. Download them locally:

```powershell
.\scripts\download-miners.ps1
```

This fetches:

- AlphaPool miner into `alphapool/alpha-miner`
- PearlHash miner into `pearlhash/pearl-miner`

## Miner Commands

Start the default pool from `.env`:

```powershell
.\start-miner.ps1
```

Stop the default pool:

```powershell
.\stop-miner.ps1
```

Tail the default pool log:

```powershell
.\tail-miner.ps1
```

Pool-specific controls:

```powershell
.\start-pearlhash-miner.ps1
.\stop-pearlhash-miner.ps1
.\tail-pearlhash-miner.ps1

.\start-pearl-miner.ps1
.\stop-pearl-miner.ps1
.\tail-pearl-miner.ps1
```

CLI equivalents:

```powershell
pearl-ops miner status
pearl-ops miner start
pearl-ops miner stop --all
```

## Local Dashboard

Start the dashboard:

```powershell
.\start-dashboard.ps1
```

Open:

```text
http://127.0.0.1:8787
```

The dashboard shows:

- current miner process and active pool
- local hashrate from miner logs
- GPU utilization, power, temperature, and memory
- PearlHash account data from `/api/account/<address>`
- Pearl explorer balance for the configured address
- SafeTrade API diagnostics
- dry-run/live-trading/withdrawal guard status

The dashboard has local Start/Stop buttons for the configured default miner.

## PearlHash Account Data

PearlHash account status is read from:

```text
https://pearlhash.xyz/api/account/<PEARL_ADDRESS>
```

The dashboard uses that endpoint to display connected workers, pool-side
hashrate, pending rewards, and balance transactions when available.

## Wallet And Explorer Checks

Check the configured address:

```powershell
pearl-ops wallet check
```

Prepare a dry-run transfer plan from a self-custody wallet to a SafeTrade PRL
deposit address:

```powershell
pearl-ops wallet send-to-safetrade --amount 1
```

Wallet sends are disabled unless `ALLOW_WALLET_SENDS=true`, a verified Pearl CLI
path is configured, and the command is run with `--confirm`.

## SafeTrade Automation

SafeTrade authentication follows the official example client:

```text
base URL: https://safe.trade/api/v2
signature: HMAC_SHA256(secret, nonce + api_key)
headers: X-Auth-Apikey, X-Auth-Nonce, X-Auth-Signature
```

Diagnostics:

```powershell
pearl-ops safetrade me
```

Dry-run PRL sell order:

```powershell
pearl-ops safetrade sell --amount 1 --price 1.20
```

Live order placement requires all of the following:

```text
DRY_RUN=false
ALLOW_LIVE_TRADING=true
```

and the command must include `--confirm`.

USDT withdrawals are additionally disabled unless:

```text
ALLOW_WITHDRAWALS=true
SAFETRADE_WITHDRAW_ENDPOINT=<verified endpoint>
USDT_WITHDRAW_ADDRESS=<your exchange wallet>
```

The withdrawal endpoint is intentionally not guessed because the public
SafeTrade example client documents authentication and orders, but not a stable
withdrawal API.

## Security Checklist Before Publishing

Before committing or pushing, run:

```powershell
git status --short --ignored
rg "YOUR_REAL_ADDRESS|YOUR_REAL_API_KEY|YOUR_REAL_SECRET" -n --hidden
```

Expected behavior:

- `.env` appears under ignored files
- miner binaries appear under ignored files
- logs and PID files appear under ignored files
- no real wallet address or API secret appears in tracked files

If a wallet seed phrase was ever pasted into chat, screenshots, logs, or notes,
treat that wallet as exposed and create a fresh wallet for long-term funds.

## Sources

- Pearl explorer API: https://pearlchain.live/api-docs
- PearlHash: https://pearlhash.xyz/
- AlphaPool: https://pearl.alphapool.tech/
- SafeTrade official example client: https://github.com/safetrade-exchange/example-client
- PRL market reference: https://www.hashrate.no/coins/PRL/markets

## Disclaimer

This tool automates local operations around mining and exchange APIs. Mining,
trading, and withdrawals can lose money or expose funds if configured
incorrectly. Review configuration, permissions, addresses, and dry-run output
before enabling live actions.
