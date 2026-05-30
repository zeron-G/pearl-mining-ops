#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -f pearlhash-miner.pid ]]; then
  echo "No pearlhash-miner.pid found; PearlHash miner is probably not running."
  exit 0
fi

PID="$(cat pearlhash-miner.pid)"
if kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
  rm -f pearlhash-miner.pid
  echo "PearlHash miner stopped. PID was: $PID"
else
  rm -f pearlhash-miner.pid
  echo "Stale PID file removed; PearlHash miner was not running."
fi
