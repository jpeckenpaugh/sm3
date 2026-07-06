#!/usr/bin/env bash
set -euo pipefail

if [ $# -ne 3 ]; then
  echo "Usage: $0 <seconds> <probability> <file>" >&2
  exit 1
fi

sleep "$1"

if awk -v r=$RANDOM -v p=$2 'BEGIN { exit (r >= p * 32768) }'; then
  touch "$3"
fi
