#!/bin/bash
cd "$(dirname "$0")" || exit 1
export PATH="$PWD/.venv/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
exec "$PWD/.venv/bin/python" "$PWD/app.py"
