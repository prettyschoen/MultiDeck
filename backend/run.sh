#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$DIR/.venv"

exec "$VENV/bin/python" "$DIR/backend.py"
