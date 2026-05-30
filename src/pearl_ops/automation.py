from __future__ import annotations

from dataclasses import dataclass

from .config import Settings
from .safetrade import OrderRequest, SafeTradeClient


@dataclass(frozen=True)
class CyclePlan:
    dry_run: bool
    steps: list[str]


def build_cycle_plan(settings: Settings) -> CyclePlan:
    steps = [
        "Check miner process and logs.",
        "Check Pearl address balance through explorer.",
        "Check SafeTrade API authentication.",
        f"Prepare PRL sell order on {settings.safetrade_prl_market}.",
    ]
    if settings.withdrawals_enabled:
        steps.append("Withdraw USDT through configured SafeTrade withdrawal endpoint.")
    else:
        steps.append("Skip USDT withdrawal because withdrawals are disabled.")
    return CyclePlan(dry_run=settings.dry_run, steps=steps)


def dry_run_sell(settings: Settings, amount: str, price: str | None) -> dict:
    client = SafeTradeClient(settings)
    order = OrderRequest(
        market=settings.safetrade_prl_market,
        side="sell",
        amount=amount,
        price=price,
    )
    return client.create_order(order, confirm=False)
