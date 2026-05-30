from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import requests


SATOSHIS_PER_PRL = Decimal("100000000")


@dataclass(frozen=True)
class AddressSummary:
    address: str
    balance_prl: Decimal
    total_received_prl: Decimal | None
    total_sent_prl: Decimal | None
    total_mined_prl: Decimal | None
    tx_count: int | None
    raw: dict[str, Any]


def validate_prl_address(address: str) -> None:
    if not address.startswith("prl1p"):
        raise ValueError("Pearl mainnet addresses should start with prl1p")
    if len(address) < 40:
        raise ValueError("Pearl address looks too short")


def _to_prl(value: Any) -> Decimal:
    if value is None or value == "":
        return Decimal("0")
    text = str(value)
    if "." in text:
        return Decimal(text)
    return Decimal(text) / SATOSHIS_PER_PRL


class PearlExplorer:
    def __init__(self, base_url: str = "https://pearlchain.live") -> None:
        self.base_url = base_url.rstrip("/")

    def address(self, address: str) -> AddressSummary:
        validate_prl_address(address)
        url = f"{self.base_url}/api/explorer/address/{address}"
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        data = response.json()
        return AddressSummary(
            address=data.get("address", address),
            balance_prl=_to_prl(data.get("balance") or data.get("balanceSat")),
            total_received_prl=(
                _to_prl(data.get("totalReceived"))
                if data.get("totalReceived") is not None
                else None
            ),
            total_sent_prl=(
                _to_prl(data.get("totalSent")) if data.get("totalSent") is not None else None
            ),
            total_mined_prl=(
                _to_prl(data.get("totalMined")) if data.get("totalMined") is not None else None
            ),
            tx_count=data.get("txCount"),
            raw=data,
        )
