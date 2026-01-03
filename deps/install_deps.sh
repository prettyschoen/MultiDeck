#!/usr/bin/env bash
set -euo pipefail

PLUGIN_DIR="$(cd "$(dirname "$0")" && pwd)"
LOGFILE="$PLUGIN_DIR/install_deps.log"

echo "=== DisplayVPNMusic dependency check started: $(date) ===" | tee -a "$LOGFILE"

echo
echo "SteamOS / Arch Linux detected"
echo "System package installation is NOT automatic on SteamOS."
echo "Checking required commands instead..."
echo | tee -a "$LOGFILE"

# Commands that should already exist on SteamOS
REQUIRED_COMMANDS=(
  python3
  pip
  dbus-send
  nmcli
  playerctl
)

MISSING_COMMANDS=()

for cmd in "${REQUIRED_COMMANDS[@]}"; do
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "✔ Found command: $cmd" | tee -a "$LOGFILE"
  else
    echo "✖ Missing command: $cmd" | tee -a "$LOGFILE"
    MISSING_COMMANDS+=("$cmd")
  fi
done

if [ "${#MISSING_COMMANDS[@]}" -ne 0 ]; then
  echo
  echo "⚠ WARNING: Missing system commands:" | tee -a "$LOGFILE"
  for cmd in "${MISSING_COMMANDS[@]}"; do
    echo "  - $cmd" | tee -a "$LOGFILE"
  done
  echo
  echo "SteamOS root filesystem is read-only."
  echo "If something is missing, install it manually with:"
  echo
  echo "  sudo steamos-readonly disable"
  echo "  sudo pacman -S <package>"
  echo "  sudo steamos-readonly enable"
  echo
fi

echo
echo "Checking Python packages (user-local install)..."
echo | tee -a "$LOGFILE"

PYTHON_PACKAGES=(
  dbus-next
  psutil
  evdev
)

for pkg in "${PYTHON_PACKAGES[@]}"; do
  if python3 - <<EOF 2>/dev/null
import $pkg
EOF
  then
    echo "✔ Python package already installed: $pkg" | tee -a "$LOGFILE"
  else
    echo "Installing Python package (user): $pkg" | tee -a "$LOGFILE"
    python3 -m pip install --user "$pkg" >>"$LOGFILE" 2>&1
  fi
done

echo
echo "=== DisplayVPNMusic dependency check complete: $(date) ===" | tee -a "$LOGFILE"
echo
echo "If the plugin fails at runtime, check:"
echo "  $LOGFILE"
echo
