#!/usr/bin/env bash
set -euo pipefail

if [ $# -ne 2 ]; then
  echo "Usage: $0 <seconds> <file>" >&2
  exit 1
fi

sleep "$1"
touch "$2"
