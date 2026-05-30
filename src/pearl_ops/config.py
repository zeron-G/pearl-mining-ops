from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_env(root: Path = ROOT) -> dict[str, str]:
    values: dict[str, str] = {}
    for name in (".env",):
        values.update(_parse_env_file(root / name))
    merged = {**values, **os.environ}
    return {k: v for k, v in merged.items() if v is not None}


def as_bool(value: str | None, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    root: Path
    pearl_address: str
    default_pool: str
    wsl_distro: str
    dry_run: bool
    safetrade_base_url: str
    safetrade_api_key: str
    safetrade_api_secret: str
    safetrade_prl_market: str
    pearlhash_host: str
    alphapool_pool: str
    miner_worker: str
    alphapool_password: str
    dashboard_host: str
    dashboard_port: int
    trusted_ip: str
    allow_live_trading: bool
    max_prl_sell_per_run: str
    min_usdt_to_withdraw: str
    allow_withdrawals: bool
    safetrade_withdraw_endpoint: str
    usdt_withdraw_network: str
    usdt_withdraw_address: str
    allow_wallet_sends: bool
    pearl_cli_path: str
    safetrade_prl_deposit_address: str
    pearl_send_command_template: str

    @property
    def live_trading_enabled(self) -> bool:
        return (not self.dry_run) and self.allow_live_trading

    @property
    def withdrawals_enabled(self) -> bool:
        return self.live_trading_enabled and self.allow_withdrawals


def get_settings(root: Path = ROOT) -> Settings:
    env = load_env(root)
    return Settings(
        root=root,
        pearl_address=env.get("PEARL_ADDRESS", ""),
        default_pool=env.get("DEFAULT_POOL", "alphapool"),
        wsl_distro=env.get("WSL_DISTRO", "Ubuntu"),
        dry_run=as_bool(env.get("DRY_RUN"), default=True),
        safetrade_base_url=env.get("SAFETRADE_BASE_URL", "https://safe.trade/api/v2").rstrip("/"),
        safetrade_api_key=env.get("SAFETRADE_API_KEY", ""),
        safetrade_api_secret=env.get("SAFETRADE_API_SECRET", ""),
        safetrade_prl_market=env.get("SAFETRADE_PRL_MARKET", "prlusdt").lower(),
        pearlhash_host=env.get("PEARLHASH_HOST", "84.32.220.219:9000"),
        alphapool_pool=env.get("ALPHAPOOL_POOL", "stratum+tcp://us2.alphapool.tech:5566"),
        miner_worker=env.get("MINER_WORKER", "desktop5090"),
        alphapool_password=env.get("ALPHAPOOL_PASSWORD", "x;d=1048576"),
        dashboard_host=env.get("DASHBOARD_HOST", "127.0.0.1"),
        dashboard_port=int(env.get("DASHBOARD_PORT", "8787")),
        trusted_ip=env.get("TRUSTED_IP", ""),
        allow_live_trading=as_bool(env.get("ALLOW_LIVE_TRADING"), default=False),
        max_prl_sell_per_run=env.get("MAX_PRL_SELL_PER_RUN", "10"),
        min_usdt_to_withdraw=env.get("MIN_USDT_TO_WITHDRAW", "25"),
        allow_withdrawals=as_bool(env.get("ALLOW_WITHDRAWALS"), default=False),
        safetrade_withdraw_endpoint=env.get("SAFETRADE_WITHDRAW_ENDPOINT", ""),
        usdt_withdraw_network=env.get("USDT_WITHDRAW_NETWORK", ""),
        usdt_withdraw_address=env.get("USDT_WITHDRAW_ADDRESS", ""),
        allow_wallet_sends=as_bool(env.get("ALLOW_WALLET_SENDS"), default=False),
        pearl_cli_path=env.get("PEARL_CLI_PATH", ""),
        safetrade_prl_deposit_address=env.get("SAFETRADE_PRL_DEPOSIT_ADDRESS", ""),
        pearl_send_command_template=env.get("PEARL_SEND_COMMAND_TEMPLATE", ""),
    )
