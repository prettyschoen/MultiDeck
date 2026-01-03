#!/usr/bin/env python3

import json
import logging
import os
import signal
import sys
import threading
from pathlib import Path
from typing import Optional

import dbus

# ----------------------------
# Constants
# ----------------------------

PLUGIN_NAME = "MultiDeck"

TARGET_STEAMOS_VERSION = "3.7.17"
TARGET_DECKY_VERSION = "3.2.1"

BASE_DIR = Path(__file__).resolve().parent
STATE_FILE = BASE_DIR / "state.json"

# ----------------------------
# Logging setup
# ----------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] MultiDeck: %(message)s",
)

log = logging.getLogger(__name__)

# ----------------------------
# State Manager (atomic)
# ----------------------------

class StateManager:
    def __init__(self, path: Path):
        self.path = path
        self.lock = threading.Lock()
        self.state = self._load()

    def _default_state(self):
        return {
            "display": {
                "brightness": None,
                "inhibited": False,
            },
            "audio": {
                "speaker_muted": False,
                "mic_muted": False,
            },
            "vpn": {
                "previous": None,
                "current": None,
            },
        }

    def _load(self):
        if not self.path.exists():
            return self._default_state()

        try:
            with self.path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log.error("Failed to load state file, resetting: %s", e)
            return self._default_state()

    def save(self):
        with self.lock:
            tmp = self.path.with_suffix(".tmp")
            with tmp.open("w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            tmp.replace(self.path)

    def update(self, updater):
        with self.lock:
            updater(self.state)
            self.save()

state = StateManager(STATE_FILE)

# ----------------------------
# Version detection
# ----------------------------

def detect_steamos_version():
    info = {}
    try:
        with open("/etc/os-release", "r") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    info[k] = v.strip('"')
    except Exception as e:
        log.error("Failed to read /etc/os-release: %s", e)

    return info

def detect_decky_version():
    # Decky exposes version via env in recent releases
    return os.environ.get("DECKY_VERSION") or "unknown"

def log_versions():
    os_info = detect_steamos_version()
    steamos_version = os_info.get("VERSION_ID", "unknown")
    pretty = os_info.get("PRETTY_NAME", "unknown")
    decky_version = detect_decky_version()

    log.info("SteamOS detected: %s (%s)", steamos_version, pretty)
    log.info("Decky Loader detected: %s", decky_version)

    if steamos_version != TARGET_STEAMOS_VERSION:
        log.warning(
            "SteamOS version mismatch (expected %s, got %s)",
            TARGET_STEAMOS_VERSION,
            steamos_version,
        )

    if decky_version != TARGET_DECKY_VERSION:
        log.warning(
            "Decky Loader version mismatch (expected %s, got %s)",
            TARGET_DECKY_VERSION,
            decky_version,
        )

# ----------------------------
# login1 Sleep Inhibition
# ----------------------------

class SleepInhibitor:
    def __init__(self):
        self.bus = None
        self.fd = None

    def acquire(self, reason: str):
        if self.fd is not None:
            log.debug("Sleep already inhibited")
            return

        try:
            self.bus = dbus.SystemBus()
            proxy = self.bus.get_object(
                "org.freedesktop.login1",
                "/org/freedesktop/login1",
            )
            iface = dbus.Interface(proxy, "org.freedesktop.login1.Manager")

            self.fd = iface.Inhibit(
                "sleep",
                PLUGIN_NAME,
                reason,
                "block",
                dbus_interface="org.freedesktop.login1.Manager",
            )

            state.update(lambda s: s["display"].update({"inhibited": True}))
            log.info("Sleep inhibited (%s)", reason)

        except Exception as e:
            log.error("Failed to acquire sleep inhibition: %s", e)

    def release(self):
        if self.fd is None:
            return

        try:
            self.fd.close()
            log.info("Sleep inhibition released")
        except Exception as e:
            log.error("Failed to release inhibition: %s", e)
        finally:
            self.fd = None
            state.update(lambda s: s["display"].update({"inhibited": False}))

sleep_inhibitor = SleepInhibitor()

# ----------------------------
# Cleanup handling
# ----------------------------

def shutdown_handler(*_):
    log.info("Backend shutting down, cleaning up")
    sleep_inhibitor.release()
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

# ----------------------------
# Backend entry
# ----------------------------

def main():
    log.info("Starting MultiDeck backend")
    log_versions()
    log.info("Initial state loaded: %s", state.state)

    # Backend event loop placeholder
    signal.pause()

if __name__ == "__main__":
    main()
