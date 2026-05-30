from __future__ import annotations

import argparse
import json
import sys

from .automation import build_cycle_plan
from .config import get_settings
from .dashboard import serve_dashboard
from .explorer import PearlExplorer
from .miner import MinerManager
from .safetrade import OrderRequest, SafeTradeClient, SafeTradeError
from .wallet import build_send_to_safetrade_plan


def print_json(data: object) -> None:
    print(json.dumps(data, indent=2, sort_keys=True, default=str))


def cmd_config(_: argparse.Namespace) -> int:
    settings = get_settings()
    print_json(
        {
            "root": settings.root,
            "pearl_address_configured": bool(settings.pearl_address),
            "default_pool": settings.default_pool,
            "dry_run": settings.dry_run,
            "safetrade_base_url": settings.safetrade_base_url,
            "safetrade_market": settings.safetrade_prl_market,
            "live_trading_enabled": settings.live_trading_enabled,
            "withdrawals_enabled": settings.withdrawals_enabled,
        }
    )
    return 0


def cmd_wallet_check(_: argparse.Namespace) -> int:
    settings = get_settings()
    if not settings.pearl_address:
        print("PEARL_ADDRESS is not configured.")
        return 2
    summary = PearlExplorer().address(settings.pearl_address)
    print_json(
        {
            "address": summary.address,
            "balance_prl": summary.balance_prl,
            "total_received_prl": summary.total_received_prl,
            "total_sent_prl": summary.total_sent_prl,
            "total_mined_prl": summary.total_mined_prl,
            "tx_count": summary.tx_count,
        }
    )
    return 0


def cmd_wallet_send(args: argparse.Namespace) -> int:
    plan = build_send_to_safetrade_plan(
        get_settings(),
        args.amount,
        confirm=args.confirm,
    )
    print_json(plan.__dict__)
    return 0


def cmd_miner_status(_: argparse.Namespace) -> int:
    manager = MinerManager(get_settings())
    status = manager.process_status()
    print("running:", status.running)
    if status.output:
        print(status.output)
    return 0


def cmd_miner_start(args: argparse.Namespace) -> int:
    manager = MinerManager(get_settings())
    result = manager.switch_to(args.pool)
    print_json(result)
    return 0


def cmd_miner_stop(args: argparse.Namespace) -> int:
    manager = MinerManager(get_settings())
    if args.all:
        print_json(manager.stop_all())
    else:
        result = manager.stop(args.pool)
        print_json(
            {
                "returncode": result.returncode,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
            }
        )
    return 0


def cmd_pool_links(_: argparse.Namespace) -> int:
    print_json(MinerManager(get_settings()).dashboard_links())
    return 0


def cmd_safetrade_me(_: argparse.Namespace) -> int:
    print_json(SafeTradeClient(get_settings()).member_me())
    return 0


def cmd_safetrade_sell(args: argparse.Namespace) -> int:
    settings = get_settings()
    order = OrderRequest(
        market=args.market or settings.safetrade_prl_market,
        side="sell",
        amount=args.amount,
        price=args.price,
    )
    result = SafeTradeClient(settings).create_order(order, confirm=args.confirm)
    print_json(result)
    return 0


def cmd_safetrade_withdraw(args: argparse.Namespace) -> int:
    result = SafeTradeClient(get_settings()).withdraw_usdt(args.amount, confirm=args.confirm)
    print_json(result)
    return 0


def cmd_run_cycle(_: argparse.Namespace) -> int:
    settings = get_settings()
    plan = build_cycle_plan(settings)
    print_json(plan.__dict__)
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    serve_dashboard(host=args.host, port=args.port)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pearl-ops")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("config").set_defaults(func=cmd_config)

    wallet = sub.add_parser("wallet")
    wallet_sub = wallet.add_subparsers(dest="wallet_command", required=True)
    wallet_sub.add_parser("check").set_defaults(func=cmd_wallet_check)
    wallet_send = wallet_sub.add_parser("send-to-safetrade")
    wallet_send.add_argument("--amount", required=True)
    wallet_send.add_argument("--confirm", action="store_true")
    wallet_send.set_defaults(func=cmd_wallet_send)

    miner = sub.add_parser("miner")
    miner_sub = miner.add_subparsers(dest="miner_command", required=True)
    miner_sub.add_parser("status").set_defaults(func=cmd_miner_status)
    miner_start = miner_sub.add_parser("start")
    miner_start.add_argument("--pool")
    miner_start.set_defaults(func=cmd_miner_start)
    miner_stop = miner_sub.add_parser("stop")
    miner_stop.add_argument("--pool")
    miner_stop.add_argument("--all", action="store_true")
    miner_stop.set_defaults(func=cmd_miner_stop)

    pools = sub.add_parser("pools")
    pools_sub = pools.add_subparsers(dest="pools_command", required=True)
    pools_sub.add_parser("links").set_defaults(func=cmd_pool_links)

    safetrade = sub.add_parser("safetrade")
    safe_sub = safetrade.add_subparsers(dest="safetrade_command", required=True)
    safe_sub.add_parser("me").set_defaults(func=cmd_safetrade_me)
    sell = safe_sub.add_parser("sell")
    sell.add_argument("--amount", required=True)
    sell.add_argument("--price")
    sell.add_argument("--market")
    sell.add_argument("--confirm", action="store_true")
    sell.set_defaults(func=cmd_safetrade_sell)
    withdraw = safe_sub.add_parser("withdraw-usdt")
    withdraw.add_argument("--amount", required=True)
    withdraw.add_argument("--confirm", action="store_true")
    withdraw.set_defaults(func=cmd_safetrade_withdraw)

    sub.add_parser("run-cycle").set_defaults(func=cmd_run_cycle)
    dashboard = sub.add_parser("dashboard")
    dashboard.add_argument("--host")
    dashboard.add_argument("--port", type=int)
    dashboard.set_defaults(func=cmd_dashboard)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (SafeTradeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
