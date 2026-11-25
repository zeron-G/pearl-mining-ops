from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import Settings


@dataclass(frozen=True)
class MinerStatus:
    running: bool
    output: str
    active_pool: str | None = None


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )


class MinerManager:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def process_status(self) -> MinerStatus:
        result = _run(
            [
                "wsl.exe",
                "-d",
                self.settings.wsl_distro,
                "--",
                "bash",
                "-lc",
                "ps -C alpha-miner,pearl-miner,wildrig-multi -o pid=,etime=,comm= || true",
            ],
            self.settings.root,
        )
        output = result.stdout.strip()
        active_pool = None
        if "alpha-miner" in output:
            active_pool = "alphapool"
        if "pearl-miner" in output or "wildrig-multi" in output:
            active_pool = "pearlhash"
        return MinerStatus(running=bool(output), output=output, active_pool=active_pool)

    def log_paths(self) -> dict[str, Path]:
        return {
            "alphapool": self.settings.root / "alphapool" / "pearl-miner.log",
            "pearlhash": self.settings.root / "pearlhash" / "pearlhash-miner.log",
        }

    def dashboard_links(self) -> dict[str, str]:
        address = self.settings.pearl_address or "<PEARL_ADDRESS>"
        return {
            "alphapool": f"https://pearl.alphapool.tech/miners/{address}",
            "pearlhash": "https://pearlhash.xyz/#lookup",
        }

    def start(self, pool: str | None = None) -> subprocess.CompletedProcess[str]:
        pool = (pool or self.settings.default_pool).lower()
        script = {
            "alphapool": self.settings.root / "start-pearl-miner.ps1",
            "pearlhash": self.settings.root / "start-pearlhash-miner.ps1",
        }.get(pool)
        if script is None:
            raise ValueError(f"Unsupported pool: {pool}")
        return _run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)],
            self.settings.root,
        )

    def stop(self, pool: str | None = None) -> subprocess.CompletedProcess[str]:
        pool = (pool or self.settings.default_pool).lower()
        script = {
            "alphapool": self.settings.root / "stop-pearl-miner.ps1",
            "pearlhash": self.settings.root / "stop-pearlhash-miner.ps1",
        }.get(pool)
        if script is None:
            raise ValueError(f"Unsupported pool: {pool}")
        return _run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)],
            self.settings.root,
        )

    def stop_all(self) -> dict[str, dict[str, str | int]]:
        results = {}
        for pool in ("alphapool", "pearlhash"):
            result = self.stop(pool)
            results[pool] = {
                "returncode": result.returncode,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
            }
        return results

    def switch_to(self, pool: str | None = None) -> dict[str, Any]:
        target = (pool or self.settings.default_pool).lower()
        stopped = self.stop_all()
        started = self.start(target)
        return {
            "target": target,
            "stopped": stopped,
            "started": {
                "returncode": started.returncode,
                "stdout": started.stdout.strip(),
                "stderr": started.stderr.strip(),
            },
        }

    def log_tail(self, pool: str, lines: int = 80) -> list[str]:
        path = self.log_paths()[pool]
        if not path.exists():
            return []
        content = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return content[-lines:]

    def log_summary(self, pool: str) -> dict[str, Any]:
        path = self.log_paths()[pool]
        lines = self.log_tail(pool, lines=300)
        text = "\n".join(lines)
        hashrates = [
            float(value)
            for value in re.findall(r"hashrate_th_s=([0-9.]+)|([0-9.]+)\s*TH/s", text)
            for value in value
            if value
        ]
        submitted = len(re.findall(r"share submitted|accepted|Accepted", text, re.IGNORECASE))
        rejected = len(re.findall(r"reject|rejected|stale", text, re.IGNORECASE))
        if "WildRig/" in text or "[ver. 0.52." in text:
            hashrates = [float(v) for v in re.findall(r"^\s*10s:\s*([\d.]+) TH/s", text, re.M)]
            def last_counter(name: str) -> int:
                values = re.findall(rf"{name}:\s*(\d+|-)", text)
                return int(values[-1]) if values and values[-1].isdigit() else 0
            submitted = last_counter("Accepted")
            rejected = last_counter("Rejected")
        connected = bool(
            re.search(
                r"connected|login success|received new job|loaded new job|hashrate|workspace_ready|mining",
                text,
                re.IGNORECASE,
            )
        )
        age_seconds = None
        if path.exists():
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            age_seconds = round((datetime.now(timezone.utc) - mtime).total_seconds(), 1)
        return {
            "pool": pool,
            "log_path": str(path),
            "exists": path.exists(),
            "connected_hint": connected,
            "log_age_seconds": age_seconds,
            "last_hashrate_th_s": hashrates[-1] if hashrates else None,
            "avg_hashrate_th_s": round(sum(hashrates) / len(hashrates), 2) if hashrates else None,
            "accepted_or_submitted": submitted,
            "rejected_or_stale": rejected,
            "tail": lines[-40:],
        }

    def gpu_status(self) -> list[dict[str, str]]:
        result = _run(
            [
                "nvidia-smi",
                "--query-gpu=name,utilization.gpu,power.draw,temperature.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            self.settings.root,
        )
        if result.returncode != 0:
            return [{"error": result.stderr.strip() or result.stdout.strip()}]
        gpus = []
        for line in result.stdout.splitlines():
            parts = [part.strip() for part in line.split(",")]
            if len(parts) != 6:
                continue
            name, util, power, temp, mem_used, mem_total = parts
            gpus.append(
                {
                    "name": name,
                    "utilization_pct": util,
                    "power_w": power,
                    "temperature_c": temp,
                    "memory_used_mib": mem_used,
                    "memory_total_mib": mem_total,
                }
            )
        return gpus
