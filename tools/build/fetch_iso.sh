#!/usr/bin/env bash
# Copy or download the user's own KimiKiss disc image to a directory outside
# the repo, unpack it if compressed, and verify it against tools/build/iso.sha1.
# The first successful run records the checksum; later runs must match it.
#
# Usage:  tools/build/fetch_iso.sh <url-or-local-path>
# Env:    KIMIKISS_PRIVATE_DIR  destination dir (default: <repo>/../kimikiss-private)
set -euo pipefail

repo_root="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
private_dir="$(realpath -m "${KIMIKISS_PRIVATE_DIR:-$(dirname "$repo_root")/kimikiss-private}")"
iso="$private_dir/kimikiss.iso"
download="$private_dir/download.part"
sha_file="$repo_root/tools/build/iso.sha1"

src="${1:?usage: $0 <url-or-local-path>}"

case "$private_dir/" in
  "$repo_root"/*) echo "error: $private_dir is inside the repo" >&2; exit 1 ;;
esac

mkdir -p "$private_dir"
chmod 700 "$private_dir"

if [[ -f "$src" ]]; then
  cp -- "$src" "$download"
else
  curl -fL --retry 4 --retry-delay 2 -C - -o "$download" -- "$src"
fi

case "$(head -c 6 "$download" | od -An -tx1 | tr -d ' \n')" in
  504b0304*)     unzip -p "$download" > "$iso.tmp" ;;
  1f8b*)         gzip -dc "$download" > "$iso.tmp" ;;
  fd377a585a00*) xz -dc "$download" > "$iso.tmp" ;;
  *)             mv "$download" "$iso.tmp" ;;
esac
rm -f "$download"

# ISO9660 primary volume descriptor: "CD001" at byte 32769 (sector 16 + 1).
if [[ "$(head -c 32774 "$iso.tmp" | tail -c 5 | od -An -tx1 | tr -d ' \n')" != 4344303031 ]]; then
  echo "error: not an ISO9660 image (zip must contain exactly one .iso)" >&2
  rm -f "$iso.tmp"
  exit 1
fi

sha="$(sha1sum "$iso.tmp" | cut -d' ' -f1)"
if [[ -f "$sha_file" ]]; then
  expected="$(tr -d ' \n' < "$sha_file")"
  if [[ "$sha" != "$expected" ]]; then
    echo "error: SHA-1 $sha does not match recorded $expected" >&2
    rm -f "$iso.tmp"
    exit 1
  fi
  echo "ok: matches recorded SHA-1 $sha"
else
  echo "$sha" > "$sha_file"
  echo "recorded: SHA-1 $sha -> $sha_file (commit this file)"
fi
mv -f "$iso.tmp" "$iso"
chmod 400 "$iso"
echo "iso: $iso ($(stat -c %s "$iso") bytes)"
