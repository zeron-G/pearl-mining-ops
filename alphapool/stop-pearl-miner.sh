#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -f pearl-miner.pid ]]; then
  echo "No pearl-miner.pid found; miner is probably not running."
  exit 0
fi

PID="$(cat pearl-miner.pid)"
if kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
  rm -f pearl-miner.pid
  echo "Pearl miner stopped. PID was: $PID"
else
  rm -f pearl-miner.pid
  echo "Stale PID file removed; miner was not running."
fi
