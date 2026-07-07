#!/usr/bin/env bash
# shellcheck disable=SC2016
# Matsya: CLI wrapper — delegates to sm.py
# Usage:
#   export PATH="/root/sm:$PATH"    # add to PATH
#   sm.sh init test-app.db          # use directly
#   ln -s /root/sm/sm.sh ~/.local/bin/sm   # install as 'sm'

DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$DIR/sm.py" "$@"
