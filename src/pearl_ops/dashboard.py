from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
from typing import Any

import requests

from .automation import build_cycle_plan
from .config import Settings, get_settings
from .explorer import PearlExplorer
from .miner import MinerManager
from .safetrade import SafeTradeClient


def _masked(value: str, keep: int = 4) -> str:
    if not value:
        return ""
    if len(value) <= keep * 2:
        return "*" * len(value)
    return f"{value[:keep]}...{value[-keep:]}"


def _safe_call(fn):
    try:
        return {"ok": True, "data": fn()}
    except Exception as exc:  # noqa: BLE001 - this feeds a local status panel.
        return {"ok": False, "error": str(exc)}


def _runtime_hours(process_output: str) -> float | None:
    match = re.search(r"\s((?:(\d+)-)?(\d{2}):(\d{2}):(\d{2}))\s+\./pearl-miner", process_output)
    if not match:
        return None
    days = int(match.group(2) or 0)
    hours = int(match.group(3))
    minutes = int(match.group(4))
    seconds = int(match.group(5))
    return days * 24 + hours + minutes / 60 + seconds / 3600


def _pool_economics(avg_hashrate_th_s: float | None) -> dict[str, Any]:
    if not avg_hashrate_th_s:
        return {"ok": False, "error": "No hashrate yet"}
    chain = requests.get("https://pearlhash.xyz/api/chain-info", timeout=10).json()
    txs = requests.get("https://pearlhash.xyz/api/pool-wallet-txs?page=1", timeout=10).json()
    first_tx = txs["transactions"][0]
    reward_prl = int(first_tx["vout"][0]["value"]) / 100_000_000
    network_th_s = float(chain["networkhashps"]) / 1_000_000_000_000
    blocks_per_hour = 3600 / float(chain["avg_block_time_s"])
    gross_prl_per_hour = avg_hashrate_th_s / network_th_s * blocks_per_hour * reward_prl
    net_prl_per_hour = gross_prl_per_hour * 0.97
    return {
        "ok": True,
        "network_th_s": round(network_th_s, 2),
        "block_reward_prl": round(reward_prl, 6),
        "blocks_per_hour": round(blocks_per_hour, 2),
        "gross_prl_per_hour": round(gross_prl_per_hour, 4),
        "net_prl_per_hour_after_pool_fee": round(net_prl_per_hour, 4),
    }


def _pearlhash_account(address: str) -> dict[str, Any]:
    if not address:
        return {"ok": False, "error": "No Pearl address configured"}
    return requests.get(
        f"https://pearlhash.xyz/api/account/{address}",
        timeout=10,
    ).json()


def collect_status(settings: Settings) -> dict[str, Any]:
    miner = MinerManager(settings)
    process = miner.process_status()
    pearlhash_log = miner.log_summary("pearlhash")
    runtime_hours = _runtime_hours(process.output)
    economics = _safe_call(lambda: _pool_economics(pearlhash_log["avg_hashrate_th_s"]))
    pearlhash_account = _safe_call(lambda: _pearlhash_account(settings.pearl_address))
    estimated_net = None
    if economics["ok"] and runtime_hours:
        estimated_net = round(
            economics["data"]["net_prl_per_hour_after_pool_fee"] * runtime_hours,
            4,
        )
    wallet = _safe_call(lambda: PearlExplorer().address(settings.pearl_address).__dict__)
    safetrade = _safe_call(lambda: SafeTradeClient(settings).diagnostics())
    public_ip = _safe_call(
        lambda: requests.get("https://api.ipify.org", timeout=5).text.strip()
    )
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config": {
            "default_pool": settings.default_pool,
            "pearl_address": settings.pearl_address,
            "safetrade_deposit": settings.safetrade_prl_deposit_address,
            "safetrade_base_url": settings.safetrade_base_url,
            "safetrade_market": settings.safetrade_prl_market,
            "safetrade_api_key": _masked(settings.safetrade_api_key),
            "safetrade_api_secret_configured": bool(settings.safetrade_api_secret),
            "dry_run": settings.dry_run,
            "live_trading_enabled": settings.live_trading_enabled,
            "withdrawals_enabled": settings.withdrawals_enabled,
            "trusted_ip": settings.trusted_ip,
            "pearlhash_host": settings.pearlhash_host,
        },
        "miner": {
            "running": process.running,
            "active_pool": process.active_pool,
            "runtime_hours": round(runtime_hours, 4) if runtime_hours else None,
            "process": process.output,
            "logs": {
                "alphapool": miner.log_summary("alphapool"),
                "pearlhash": pearlhash_log,
            },
            "gpu": miner.gpu_status(),
            "links": miner.dashboard_links(),
        },
        "economics": {
            "estimate": economics,
            "pearlhash_account": pearlhash_account,
            "estimated_net_prl_this_run": estimated_net,
        },
        "wallet": wallet,
        "safetrade": safetrade,
        "automation": build_cycle_plan(settings).__dict__,
        "network": public_ip,
    }


class DashboardHandler(BaseHTTPRequestHandler):
    settings: Settings

    def _send_json(self, payload: Any, status: int = 200) -> None:
        body = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_static(self, name: str, content_type: str) -> None:
        data = resources.files("pearl_ops.static").joinpath(name).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/":
            self._send_static("index.html", "text/html; charset=utf-8")
            return
        if self.path == "/styles.css":
            self._send_static("styles.css", "text/css; charset=utf-8")
            return
        if self.path == "/app.js":
            self._send_static("app.js", "application/javascript; charset=utf-8")
            return
        if self.path == "/api/status":
            self._send_json(collect_status(self.settings))
            return
        self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802
        manager = MinerManager(self.settings)
        if self.path == "/api/miner/start":
            self._send_json(manager.switch_to(self.settings.default_pool))
            return
        if self.path == "/api/miner/stop":
            self._send_json(manager.stop_all())
            return
        self.send_error(404)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        return


def serve_dashboard(host: str | None = None, port: int | None = None) -> None:
    settings = get_settings()
    host = host or settings.dashboard_host
    port = port or settings.dashboard_port
    DashboardHandler.settings = settings
    server = ThreadingHTTPServer((host, port), DashboardHandler)
    print(f"Pearl dashboard: http://{host}:{port}")
    server.serve_forever()
