#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
dir=downloads/wildrig-0.52.3
file=wildrig-multi
archive_hash=7308c95f7c8c4c0d82aade61bb4ab3366decae2b9d04ac47b8c1dc6d1bdd2c44
binary_hash=002cd29c6b890a4159b5933260e7db57d8808e540804466b3b7b80814083011b
verify() { printf '%s  %s\n' "$1" "$2" | sha256sum --check --status; }
if [[ -x $dir/$file ]] && verify "$binary_hash" "$dir/$file"; then
  echo 'Verified WildRig 0.52.3 (already installed).'
  exit 0
fi
mkdir -p "$dir"
tmp=$(mktemp -d "$dir/.install-XXXXXXXX")
trap 'rm -f "$tmp/archive" "$tmp/$file"; rmdir "$tmp"' EXIT
if [[ -f $dir/release.tar.gz ]] && verify "$archive_hash" "$dir/release.tar.gz"; then
  archive=$dir/release.tar.gz
else
  archive=$tmp/archive
  curl --fail --location --proto '=https' --proto-redir '=https' --max-time 180 \
    -o "$archive" https://github.com/andru-kun/wildrig-multi/releases/download/0.52.3/wildrig-multi-linux-0.52.3.tar.gz
fi
verify "$archive_hash" "$archive" || { echo 'Archive checksum mismatch' >&2; exit 1; }
tar -xzOf "$archive" wildrig-multi > "$tmp/$file"
verify "$binary_hash" "$tmp/$file" || { echo 'Executable checksum mismatch' >&2; exit 1; }
chmod 755 "$tmp/$file"
mv -f "$tmp/$file" "$dir/$file"
echo 'Installed verified WildRig 0.52.3.'
