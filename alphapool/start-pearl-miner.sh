#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ -f ../.env ]]; then
  set -a
  source ../.env
  set +a
fi

ADDRESS="${PEARL_ADDRESS:-}"
POOL="${ALPHAPOOL_POOL:-stratum+tcp://us2.alphapool.tech:5566}"
WORKER="${MINER_WORKER:-desktop5090}"
PASSWORD="${ALPHAPOOL_PASSWORD:-x;d=1048576}"
if [[ -z "$ADDRESS" ]]; then
  echo "PEARL_ADDRESS is not set. Add it to .env."
  exit 2
fi

if [[ -f pearl-miner.pid ]] && kill -0 "$(cat pearl-miner.pid)" 2>/dev/null; then
  echo "Pearl miner already running. PID: $(cat pearl-miner.pid)"
  exit 0
fi

nohup stdbuf -oL -eL ./alpha-miner \
  --pool "$POOL" \
  --address "$ADDRESS" \
  --worker "$WORKER" \
  --password "$PASSWORD" \
  --devices 0 \
  --color never \
  --status-interval 60 \
  > pearl-miner.log 2>&1 &

echo "$!" > pearl-miner.pid
echo "Pearl miner started. PID: $(cat pearl-miner.pid)"
echo "Log: alphapool/pearl-miner.log"
