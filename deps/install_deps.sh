#!/usr/bin/env bash
set -euo pipefail

PLUGIN_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PLUGIN_DIR/backend"
VENV_DIR="$BACKEND_DIR/.venv"
LOGFILE="$PLUGIN_DIR/install_deps.log"

echo "=== DisplayVPNMusic dependency installer started: $(date) ===" | tee -a "$LOGFILE"
echo

# --- SteamOS readonly handling -----------------------------------------------

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

# --- system dependencies -----------------------------------------------------

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

if [ "${#MISSING_PKGS[@]}" -ne 0 ]; then
  enable_rw
  sudo pacman -Sy --needed --noconfirm "${MISSING_PKGS[@]}" >>"$LOGFILE" 2>&1
fi

# --- python virtual environment ----------------------------------------------

echo
echo "Setting up Python virtual environment..." | tee -a "$LOGFILE"

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR" >>"$LOGFILE" 2>&1
fi

source "$VENV_DIR/bin/activate"

PYTHON_PACKAGES=(
  dbus-next
  psutil
  evdev
)

for pkg in "${PYTHON_PACKAGES[@]}"; do
  if python - <<EOF 2>/dev/null
import $pkg
EOF
  then
    echo "✔ Python package already installed: $pkg" | tee -a "$LOGFILE"
  else
    echo "Installing Python package in venv: $pkg" | tee -a "$LOGFILE"
    pip install "$pkg" >>"$LOGFILE" 2>&1
  fi
done

deactivate

echo
echo "=== Dependency installation complete: $(date) ===" | tee -a "$LOGFILE"
echo "Virtual environment: $VENV_DIR"
echo "Log file: $LOGFILE"
echo
