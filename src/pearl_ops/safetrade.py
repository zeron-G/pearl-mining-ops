from __future__ import annotations

import binascii
import hmac
import hashlib
import time
from dataclasses import dataclass
from typing import Any

import requests

from .config import Settings


class SafeTradeError(RuntimeError):
    pass


@dataclass(frozen=True)
class OrderRequest:
    market: str
    side: str
    amount: str
    price: str | None = None

    def payload(self) -> dict[str, str]:
        data = {
            "market": self.market.lower(),
            "side": self.side,
            "amount": self.amount,
            "type": "limit" if self.price is not None else "market",
        }
        if self.price is not None:
            data["price"] = self.price
        return data


class SafeTradeClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _signature(self, nonce: str) -> str:
        digest = hmac.new(
            self.settings.safetrade_api_secret.encode(),
            digestmod=hashlib.sha256,
        )
        digest.update((nonce + self.settings.safetrade_api_key).encode())
        return binascii.hexlify(digest.digest()).decode()

    def auth_headers(self) -> dict[str, str]:
        if not self.settings.safetrade_api_key or not self.settings.safetrade_api_secret:
            raise SafeTradeError("SafeTrade API key/secret are not configured")
        nonce = str(int(time.time() * 1000))
        return {
            "X-Auth-Apikey": self.settings.safetrade_api_key,
            "X-Auth-Nonce": nonce,
            "X-Auth-Signature": self._signature(nonce),
            "Content-Type": "application/json;charset=utf-8",
        }

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return self.settings.safetrade_base_url + path

    def get(self, path: str, params: dict[str, Any] | None = None, auth: bool = True) -> Any:
        headers = self.auth_headers() if auth else {}
        response = requests.get(self._url(path), params=params, headers=headers, timeout=30)
        if response.status_code >= 400:
            raise SafeTradeError(
                f"SafeTrade GET {path} failed: HTTP {response.status_code} {response.text[:300]}"
            )
        return response.json()

    def post(self, path: str, payload: dict[str, Any] | None = None, auth: bool = True) -> Any:
        headers = self.auth_headers() if auth else {}
        response = requests.post(self._url(path), json=payload or {}, headers=headers, timeout=30)
        if response.status_code >= 400:
            raise SafeTradeError(
                f"SafeTrade POST {path} failed: HTTP {response.status_code} {response.text[:300]}"
            )
        return response.json()

    def member_me(self) -> Any:
        return self.get("/trade/account/members/me")

    def spot_balances(self) -> Any:
        return self.get("/trade/account/balances/spot")

    def diagnostics(self) -> dict[str, Any]:
        results: dict[str, Any] = {}
        for name, path in {
            "member_me": "/trade/account/members/me",
            "spot_balances": "/trade/account/balances/spot",
        }.items():
            try:
                results[name] = {"ok": True, "data": self.get(path)}
            except Exception as exc:  # noqa: BLE001 - status diagnostics.
                results[name] = {"ok": False, "error": str(exc)}
        return results

    def orders(self, state: str | None = None) -> Any:
        params = {"state": state} if state else None
        return self.get("/trade/market/orders", params=params)

    def create_order(self, order: OrderRequest, *, confirm: bool = False) -> Any:
        if not self.settings.live_trading_enabled or not confirm:
            return {
                "dry_run": True,
                "reason": "Set DRY_RUN=false, ALLOW_LIVE_TRADING=true, and pass --confirm to place a real order.",
                "payload": order.payload(),
            }
        return self.post("/trade/market/orders", order.payload())

    def withdraw_usdt(self, amount: str, *, confirm: bool = False) -> Any:
        if not self.settings.withdrawals_enabled or not confirm:
            return {
                "dry_run": True,
                "reason": "Withdrawals require live trading, ALLOW_WITHDRAWALS=true, a configured endpoint, and --confirm.",
                "amount": amount,
                "network": self.settings.usdt_withdraw_network,
                "address": self.settings.usdt_withdraw_address,
            }
        if not self.settings.safetrade_withdraw_endpoint:
            raise SafeTradeError("SAFETRADE_WITHDRAW_ENDPOINT is not configured")
        if not self.settings.usdt_withdraw_address:
            raise SafeTradeError("USDT_WITHDRAW_ADDRESS is not configured")
        payload = {
            "currency": "usdt",
            "amount": amount,
            "address": self.settings.usdt_withdraw_address,
        }
        if self.settings.usdt_withdraw_network:
            payload["network"] = self.settings.usdt_withdraw_network
        return self.post(self.settings.safetrade_withdraw_endpoint, payload)
