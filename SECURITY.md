# Security Model

This repository must never contain:

- Pearl wallet seed phrases or private keys
- SafeTrade API keys or secrets
- Exchange withdrawal addresses that you do not want public
- Miner logs that reveal private operational details

Use `.env` for local configuration. It is ignored by git.

Live trading requires all of the following:

1. `DRY_RUN=false`
2. `ALLOW_LIVE_TRADING=true`
3. An explicit command such as `pearl-ops safetrade sell --confirm`

USDT withdrawals are additionally blocked unless `ALLOW_WITHDRAWALS=true` and
`SAFETRADE_WITHDRAW_ENDPOINT` is configured after you verify the current
SafeTrade API endpoint from your account/API documentation.

Important: if a wallet seed phrase has ever been pasted into chat, logs, notes,
or screenshots, treat that wallet as exposed. Use a fresh wallet for long-term
mining proceeds.
