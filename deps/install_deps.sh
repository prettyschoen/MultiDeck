#!/usr/bin/env bash
set -euo pipefail

PLUGIN_DIR="$(cd "$(dirname "$0")" && pwd)"
LOGFILE="$PLUGIN_DIR/install_deps.log"

echo "=== DisplayVPNMusic dependency installer started: $(date) ===" | tee -a "$LOGFILE"
echo

# --- helper functions --------------------------------------------------------

enable_rw() {
  echo "Disabling SteamOS read-only filesystem..." | tee -a "$LOGFILE"
  sudo steamos-readonly disable >>"$LOGFILE" 2>&1
}

enable_ro() {
  echo "Re-enabling SteamOS read-only filesystem..." | tee -a "$LOGFILE"
  sudo steamos-readonly enable >>"$LOGFILE" 2>&1
}

cleanup() {
  enable_ro
}
trap cleanup EXIT

# --- required system packages ------------------------------------------------

declare -A SYSTEM_PACKAGES=(
  [python]="python"
  [pip]="python-pip"
  [dbus-send]="dbus"
  [nmcli]="networkmanager"
  [playerctl]="playerctl"
)

MISSING_PKGS=()

echo "Checking required system commands..." | tee -a "$LOGFILE"

for cmd in "${!SYSTEM_PACKAGES[@]}"; do
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "✔ Found command: $cmd" | tee -a "$LOGFILE"
  else
    echo "✖ Missing command: $cmd" | tee -a "$LOGFILE"
    MISSING_PKGS+=("${SYSTEM_PACKAGES[$cmd]}")
  fi
done

#
