#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -f pearlhash-miner.pid ]]; then
  echo "No pearlhash-miner.pid found; PearlHash miner is probably not running."
  exit 0
fi

PID="$(cat pearlhash-miner.pid)"
exe=$(readlink "/proc/$PID/exe" || true)
if [[ -z $exe && -r /proc/$PID/cmdline ]]; then
  IFS= read -r -d '' exe < "/proc/$PID/cmdline" || true
fi
if [[ "$PID" =~ ^[0-9]+$ && -n "$exe" && ( "$exe" == "$(realpath ./pearl-miner)" || "$exe" == "$(realpath -m ../downloads/wildrig-0.52.3/wildrig-multi)" ) ]]; then
  kill "$PID"
  rm -f pearlhash-miner.pid
  echo "PearlHash miner stopped. PID was: $PID"
else
  rm -f pearlhash-miner.pid
  echo "Stale PID file removed; PearlHash miner was not running."
fi
