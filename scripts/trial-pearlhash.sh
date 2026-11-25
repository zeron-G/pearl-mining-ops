#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
while IFS='=' read -r key value; do
  case "$key" in
    PEARL_ADDRESS|PEARLHASH_URL|PEARL_TRIAL_TEMP|PEARL_TRIAL_SECONDS|MINER_WORKER)
      printf -v "$key" '%s' "${value%$'\r'}" ;;
  esac
done < .env
root=$PWD
seconds=${1:-${PEARL_TRIAL_SECONDS:-120}}
[[ $seconds =~ ^[1-9][0-9]{0,4}$ ]] || exit 2
printf '%s\n' "${PEARL_ADDRESS:-}" | python3 src/pearl_ops/address.py
temp=${PEARL_TRIAL_TEMP:-75}
[[ $temp =~ ^[0-9]{2}$ ]] && (( temp > 60 && temp <= 85 )) || { echo 'Set PEARL_TRIAL_TEMP between 61 and 85.' >&2; exit 2; }
threads=()
case ${2:-auto} in
  auto|managed) ;;
  1|2) threads=(--gpu-threads "$2");;
  *) exit 2;;
esac
cd downloads/wildrig-0.52.3
exec 9>trial.lock
flock -n 9 || { echo 'Trial already running'; exit 3; }
if pgrep -x 'wildrig-multi|alpha-miner|pearl-miner' >/dev/null; then
  echo 'Another miner is running'; exit 3
fi
ulimit -c 0
log="live-trial-${2:-auto}.log"
pidfile=/dev/null
if [[ ${2:-} == managed ]]; then
  log="$root/pearlhash/pearlhash-miner.log"
  pidfile="$root/pearlhash/pearlhash-miner.pid"
  if [[ -s $log ]]; then cp -- "$log" "$log.$(date +%s).log"; fi
fi
exec timeout -k 5 "$seconds" bash -c 'echo "$$" > "$1"; shift; exec "$@"' bash "$pidfile" "$PWD/wildrig-multi" --algo pearlhash \
  --url "${PEARLHASH_URL:?}" --user "${PEARL_ADDRESS:?}" --worker "${MINER_WORKER:-worker01}" \
  --gpu-temp-limit "$temp" --gpu-temp-resume 60 \
  "${threads[@]}" --print-time 10 --no-color --api-port 0 >"$log" 2>&1
