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

# --- install system packages -------------------------------------------------

if [ "${#MISSING_PKGS[@]}" -ne 0 ]; then
  echo
  echo "Installing missing system packages:" | tee -a "$LOGFILE"
  printf '  - %s\n' "${MISSING_PKGS[@]}" | tee -a "$LOGFILE"
  echo

  enable_rw

  sudo pacman -Sy --needed --noconfirm "${MISSING_PKGS[@]}" >>"$LOGFILE" 2>&1
else
  echo "All required system packages are already installed." | tee -a "$LOGFILE"
fi

# --- python packages ----------------------------------------------------------

echo
echo "Checking Python packages (user install)..." | tee -a "$LOGFILE"

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
echo "=== Dependency installation complete: $(date) ===" | tee -a "$LOGFILE"
echo "Log file: $LOGFILE"
echo
