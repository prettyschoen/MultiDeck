#!/usr/bin/env bash
set -euo pipefail

LOGFILE="$(dirname "$0")/install_deps.log"
echo "=== DisplayVPNMusic dependency installation started: $(date) ===" >>"$LOGFILE"

# System packages required for backend functionality
SYSTEM_PACKAGES=(
  python3-pip
  python3-gi
  python3-dbus
  python3-setuptools
  dbus-user-session
  playerctl
  network-manager
)

MISSING=()
for pkg in "${SYSTEM_PACKAGES[@]}"; do
  if ! dpkg -s "$pkg" >/dev/null 2>&1; then
    MISSING+=("$pkg")
  fi
done

if [ ${#MISSING[@]} -ne 0 ]; then
  echo "Missing system packages: ${MISSING[*]}" | tee -a "$LOGFILE"
  sudo apt-get update >>"$LOGFILE" 2>&1
  sudo apt-get install -y "${MISSING[@]}" >>"$LOGFILE" 2>&1
else
  echo "All system packages are already installed." >>"$LOGFILE"
fi

# Python packages for backend
PYTHON_PACKAGES=(
  dbus-next
  psutil
  python-evdev
)

echo "Checking python packages..." >>"$LOGFILE"
for pkg in "${PYTHON_PACKAGES[@]}"; do
  python3 -c "import $pkg" 2>/dev/null || {
    echo "Installing python package: $pkg" | tee -a "$LOGFILE"
    python3 -m pip install --user "$pkg" >>"$LOGFILE" 2>&1
  }
done

echo "=== DisplayVPNMusic dependency installation complete: $(date) ===" >>"$LOGFILE"