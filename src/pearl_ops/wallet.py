from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass

from .config import Settings
from .explorer import validate_prl_address


@dataclass(frozen=True)
class WalletSendPlan:
    dry_run: bool
    amount: str
    destination: str
    command: str | None
    reason: str | None = None


def build_send_to_safetrade_plan(
    settings: Settings,
    amount: str,
    *,
    confirm: bool = False,
) -> WalletSendPlan:
    destination = settings.safetrade_prl_deposit_address
    if destination:
        validate_prl_address(destination)

    if not destination:
        return WalletSendPlan(
            dry_run=True,
            amount=amount,
            destination="",
            command=None,
            reason="SAFETRADE_PRL_DEPOSIT_ADDRESS is not configured.",
        )
    if not settings.pearl_cli_path or not settings.pearl_send_command_template:
        return WalletSendPlan(
            dry_run=True,
            amount=amount,
            destination=destination,
            command=None,
            reason="PEARL_CLI_PATH and PEARL_SEND_COMMAND_TEMPLATE must be configured after verifying the Pearl CLI.",
        )

    command = settings.pearl_send_command_template.format(
        cli=shlex.quote(settings.pearl_cli_path),
        address=shlex.quote(destination),
        amount=shlex.quote(amount),
    )
    if not confirm or not settings.allow_wallet_sends:
        return WalletSendPlan(
            dry_run=True,
            amount=amount,
            destination=destination,
            command=command,
            reason="Set ALLOW_WALLET_SENDS=true and pass --confirm to execute.",
        )

    subprocess.run(command, shell=True, check=True)
    return WalletSendPlan(
        dry_run=False,
        amount=amount,
        destination=destination,
        command=command,
    )
