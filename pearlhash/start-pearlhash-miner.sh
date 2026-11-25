#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
grep -qx 'PEARLHASH_ENGINE=wildrig[[:space:]]*' ../.env || {
  echo 'Set PEARLHASH_ENGINE=wildrig in .env; the legacy v10 miner is unsupported.' >&2
  exit 2
}
exec bash ../scripts/trial-pearlhash.sh '' managed
