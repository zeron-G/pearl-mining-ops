#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ -f ../.env ]]; then
  set -a
  source ../.env
  set +a
fi

ADDRESS="${PEARL_ADDRESS:-}"
HOST="${PEARLHASH_HOST:-84.32.220.219:9000}"

if [[ -z "$ADDRESS" ]]; then
  echo "PEARL_ADDRESS is not set. Add it to .env."
  exit 2
fi

if [[ -f pearlhash-miner.pid ]] && kill -0 "$(cat pearlhash-miner.pid)" 2>/dev/null; then
  echo "PearlHash miner already running. PID: $(cat pearlhash-miner.pid)"
  exit 0
fi

nohup ./pearl-miner \
  --host "$HOST" \
  --user "$ADDRESS" \
  > pearlhash-miner.log 2>&1 &

echo "$!" > pearlhash-miner.pid
echo "PearlHash miner started. PID: $(cat pearlhash-miner.pid)"
echo "Log: pearlhash/pearlhash-miner.log"
