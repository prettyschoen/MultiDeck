#!/usr/bin/env python3
import asyncio
import json
import logging
import os
import sys
import threading
import time
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

PLUGIN_NAME = "MultiDeck"
HTTP_PORT = 8765

STATE_DIR = Path.home() / ".config/decky-plugins/displayvpnmusic"
STATE_DIR.mkdir(parents=True, exist_ok=True)

# ---------------- Logging ----------------

logger = logging.getLogger(PLUGIN_NAME)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
logger.addHandler(handler)

# ---------------- Async loop ----------------

async_loop = asyncio.new_event_loop()

def _start_async_loop():
    asyncio.set_event_loop(async_loop)
    async_loop.run_forever()

threading.Thread(target=_start_async_loop, daemon=True).start()

def run_async(coro):
    return asyncio.run_coroutine_threadsafe(coro, async_loop).result()

# ---------------- Display ----------------

def turn_off_display(fade_ms=0):
    def _work():
        try:
            if fade_ms > 0:
                time.sleep(fade_ms / 1000)

            # SteamOS-safe display off
            subprocess.run(
                ["xset", "dpms", "force", "off"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False
            )
            logger.info("Display turned off")
        except Exception as e:
            logger.error(f"Display off failed: {e}")

    threading.Thread(target=_work, daemon=True).start()

# ---------------- VPN helpers ----------------

def list_vpns():
    try:
        res = subprocess.run(
            ["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"],
            capture_output=True,
            text=True,
            check=True
        )
        return [
            name for name, typ in
            (line.split(":") for line in res.stdout.splitlines())
            if typ == "vpn"
        ]
    except Exception as e:
        logger.error(f"VPN list failed: {e}")
        return []

def get_active_vpn():
    try:
        res = subprocess.run(
            ["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show", "--active"],
            capture_output=True,
            text=True,
            check=True
        )
        for line in res.stdout.splitlines():
            name, typ = line.split(":")
            if typ == "vpn":
                return name
    except Exception as e:
        logger.error(f"VPN status check failed: {e}")
    return None

def activate_vpn(name):
    def _work():
        try:
            subprocess.run(
                ["nmcli", "connection", "up", name],
                check=True
            )
            logger.info(f"VPN activated: {name}")
        except Exception as e:
            logger.error(f"VPN activation failed: {e}")

    threading.Thread(target=_work, daemon=True).start()

def deactivate_vpn(name):
    def _work():
        try:
            subprocess.run(
                ["nmcli", "connection", "down", name],
                check=True
            )
            logger.info(f"VPN deactivated: {name}")
        except Exception as e:
            logger.error(f"VPN deactivation failed: {e}")

    threading.Thread(target=_work, daemon=True).start()

# ---------------- MPRIS (music metadata) ----------------

async def get_mpris_metadata():
    try:
        import dbus
        bus = dbus.SessionBus()
        for service in bus.list_names():
            if service.startswith("org.mpris.MediaPlayer2"):
                obj = bus.get_object(service, "/org/mpris/MediaPlayer2")
                iface = dbus.Interface(obj, "org.freedesktop.DBus.Properties")
                meta = iface.Get("org.mpris.MediaPlayer2.Player", "Metadata")
                return {
                    "title": str(meta.get("xesam:title", "")),
                    "artist": ", ".join(meta.get("xesam:artist", []))
                }
    except Exception:
        pass
    return {}

# ---------------- HTTP API ----------------

class APIHandler(BaseHTTPRequestHandler):
    def _json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        if self.path == "/display/off":
            turn_off_display(body.get("fade_ms", 0))
            self._json({"ok": True})

        elif self.path == "/vpn/list":
            self._json({"vpns": list_vpns()})

        elif self.path == "/vpn/status":
            self._json({"active": get_active_vpn()})

        elif self.path == "/vpn/on":
            activate_vpn(body.get("name"))
            self._json({"ok": True})

        elif self.path == "/vpn/off":
            deactivate_vpn(body.get("name"))
            self._json({"ok": True})

        elif self.path == "/music/metadata":
            meta = run_async(get_mpris_metadata())
            self._json(meta)

        else:
            self.send_error(404)

    def log_message(self, *_):
        pass  # silence default HTTP logging

# ---------------- Main ----------------

def main():
    logger.info("Starting MultiDeck backend")
    server = HTTPServer(("127.0.0.1", HTTP_PORT), APIHandler)
    server.serve_forever()

if __name__ == "__main__":
    main()
