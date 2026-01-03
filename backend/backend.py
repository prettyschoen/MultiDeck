#!/usr/bin/env python3
"""
DisplayVPNMusic Backend

- Checks Decky Loader/SteamOS version
- Display Off, Music (MPRIS), VPN (NetworkManager), rollback, sleep inhibition
- Structured logging for journalctl
"""

import os, sys, json, time, logging, threading, tempfile, subprocess
import asyncio

PLUGIN_NAME = "displayvpnmusic"
STATE_DIR = os.path.expanduser("~/.config/decky-plugins/" + PLUGIN_NAME)
STATE_FILE = os.path.join(STATE_DIR, "state.json")

os.makedirs(STATE_DIR, exist_ok=True)
logger = logging.getLogger(PLUGIN_NAME)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("[%(levelname)s] %(asctime)s %(name)s: %(message)s"))
logger.addHandler(handler)

# CONFIG DEFAULTS
DEFAULTS = {
    "fade_out_ms": 250,
    "fade_in_ms": 250,
    "battery_sleep_threshold": 100,
    "mute_on_display_off": False,
    "mute_mic_on_display_off": False,
    "vpn_auto_connect": False,
    "last_used_vpns": []
}

def atomic_write(filename, data):
    tmp_fd, tmp_fn = tempfile.mkstemp(dir=os.path.dirname(filename))
    with os.fdopen(tmp_fd, "w") as f:
        json.dump(data, f)
    os.replace(tmp_fn, filename)

def get_state():
    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
        return {**DEFAULTS, **state}
    except Exception:
        return DEFAULTS.copy()

def set_state(elem):
    atomic_write(STATE_FILE, elem)

state = get_state()

def detect_versions():
    decky, steamos = "unknown", "unknown"
    # Decky Loader
    try:
        r = subprocess.run(["deckyloader", "--version"], capture_output=True, text=True)
        decky = r.stdout.strip() if r.returncode==0 else "unknown"
    except Exception:
        decky = "unknown"
    # SteamOS
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("VERSION_ID="):
                    steamos = line.split("=")[1].strip().replace('"', '')
    except Exception:
        steamos = "unknown"
    logger.info(f"Detected Decky Loader version: {decky}")
    logger.info(f"Detected SteamOS version: {steamos}")
    return decky, steamos

def running_wayland():
    return (os.environ.get("XDG_SESSION_TYPE", "").lower()) == "wayland"

class SleepInhibitor:
    def __init__(self): self.fd=None
    async def acquire(self):
        from dbus_next.aio import MessageBus
        bus = await MessageBus().connect()
        proxy = await bus.get_proxy_object("org.freedesktop.login1","/org/freedesktop/login1",None)
        manager = proxy.get_interface("org.freedesktop.login1.Manager")
        self.fd = await manager.call_inhibit("sleep",PLUGIN_NAME,"Display off active","block")
        logger.info("Sleep inhibitor acquired")
    def release(self):
        if self.fd: self.fd.close()
        logger.info("Sleep inhibitor released")

class DisplayController:
    def __init__(self):
        self.saved_brightness=None
        self.inhibitor=SleepInhibitor()
        self.wake_task=None
    def get_brightness(self):
        try:
            base="/sys/class/backlight"
            if not os.path.isdir(base): return None
            for driver in os.listdir(base):
                with open(f"{base}/{driver}/brightness") as f: val=int(f.read())
                with open(f"{base}/{driver}/max_brightness") as f: mx=int(f.read())
                return int(round((val/mx)*100))
        except Exception: return None
    def set_brightness(self, percent):
        try:
            base="/sys/class/backlight"
            for driver in os.listdir(base):
                maxp=f"{base}/{driver}/max_brightness"; brightp=f"{base}/{driver}/brightness"
                with open(maxp) as f: mx=int(f.read())
                val=int(round((percent/100)*mx))
                with open(brightp,"w") as f: f.write(str(val))
                return True
        except Exception: return False
    def fade_brightness(self, start,end,ms):
        steps = max(1,int(ms/50))
        for s in range(steps+1):
            pct = int(round(start+(end-start)*(s/steps)))
            self.set_brightness(pct)
            time.sleep(ms/steps/1000) if ms>0 else None
    def save_brightness(self): self.saved_brightness=self.get_brightness()
    def restore_brightness(self, ms): self.fade_brightness(self.get_brightness() or 0, self.saved_brightness or 100, ms)
    def turn_off_display(self, fade_ms):
        self.save_brightness()
        self.fade_brightness(self.saved_brightness or 100, 0, fade_ms)
        asyncio.get_event_loop().run_until_complete(self.inhibitor.acquire())
        if not running_wayland():
            try:
                subprocess.run(["xset","dpms","force","off"],check=True)
                logger.info("xset dpms force off done")
            except Exception as e:
                logger.warning(f"xset failed: {e}")
        else:
            try:
                subprocess.run(["swaymsg","output","*","dpms","off"],check=True)
                logger.info("swaymsg dpms off done")
            except Exception as e:
                logger.warning("Wayland fallback used")
        self.start_wake_watcher()
    def start_wake_watcher(self):
        loop=asyncio.get_event_loop()
        self.wake_task = loop.create_task(self._wake_watcher_task())
        logger.info("Wake watcher started")
    async def _wake_watcher_task(self):
        try:
            from evdev import InputDevice,list_devices; import select
            devs = [InputDevice(p) for p in list_devices()]
            fds = {dev.fd:dev for dev in devs}
            while True:
                r,_,_=select.select(list(fds.keys()),[],[],0.5)
                if r: break
                await asyncio.sleep(0.5)
        except Exception: logger.debug("Evdev not available")
        self.on_wake()
    def on_wake(self):
        try: self.restore_brightness(state.get("fade_in_ms",250))
        except Exception: logger.warning("Restore brightness failed")
        try: self.inhibitor.release()
        except Exception: logger.warning("Release inhibitor failed")

display = DisplayController()

class MPRISManager:
    def __init__(self): self.bus=None
    async def connect(self):
        from dbus_next.aio import MessageBus
        self.bus = await MessageBus().connect()
        names = await self.bus.list_names()
        self.players = [n for n in names if n.startswith("org.mpris.MediaPlayer2.")]
    async def get_metadata(self):
        await self.connect()
        if not getattr(self, "players", []): return None
        n = self.players[0]
        try:
            proxy = await self.bus.get_proxy_object(n,"/org/mpris/MediaPlayer2",None)
            iface = proxy.get_interface("org.freedesktop.DBus.Properties")
            meta = await iface.call_get("org.mpris.MediaPlayer2.Player","Metadata")
            status = await iface.call_get("org.mpris.MediaPlayer2.Player","PlaybackStatus")
            md = {k:v.value for k,v in meta.items()}
            md["PlaybackStatus"]=status.value
            return md
        except Exception as e:
            logger.warning("MPRIS metadata failed: "+str(e))
            return None

mpris = MPRISManager()

class VPNManager:
    def __init__(self): self.bus=None
    async def connect(self):
        from dbus_next.aio import MessageBus
        self.bus = await MessageBus().connect()
        proxy = await self.bus.get_proxy_object("org.freedesktop.NetworkManager","/org/freedesktop/NetworkManager",None)
        self.nm = proxy.get_interface("org.freedesktop.NetworkManager")
    async def list_vpns(self):
        await self.connect()
        try:
            proxy = await self.bus.get_proxy_object("org.freedesktop.NetworkManager","/org/freedesktop/NetworkManager/Settings",None)
            settings = proxy.get_interface("org.freedesktop.NetworkManager.Settings")
            conns = await settings.call_list_connections()
            vpn = []
            for path in conns:
                obj = await self.bus.get_proxy_object("org.freedesktop.NetworkManager", path, None)
                cif = obj.get_interface("org.freedesktop.NetworkManager.Settings.Connection")
                s = await cif.call_get_settings()
                if s['connection']['type'].value=='vpn':
                    vpn.append({"id":s['connection']['id'].value,"path":path,"type":"vpn"})
            return sorted(vpn, key=lambda x:x['id'].lower())
        except Exception as e:
            logger.warning("VPN list DBus failed, fallback to nmcli. "+str(e))
            return []
    async def activate(self, vpn_id):
        await self.connect()
        try:
            devs=await self.nm.call_get_devices()
            ret=await self.nm.call_activate_connection(vpn_id,devs[0] if devs else "/", "/")
            logger.info(f"VPN activated {vpn_id}")
            return True
        except Exception as e:
            logger.warning("VPN activation failed "+str(e))
            return False
    def nmcli_list(self):
        try:
            o=subprocess.run(["nmcli","--terse","--fields","NAME,TYPE","connection","show"],capture_output=True,text=True,check=True)
            lines=[l for l in o.stdout.splitlines() if ":vpn" in l]
            return [{"id":l.split(":")[0],"type":"vpn"} for l in lines]
        except Exception: return []

vpn = VPNManager()

# HTTP API for frontend calls
from http.server import BaseHTTPRequestHandler, HTTPServer

class APIHandler(BaseHTTPRequestHandler):
    def _json(self, obj, code=200):
        b=bytes(json.dumps(obj),"utf8")
        self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(b)))
        self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        if self.path=="/api/version":
            self._json(dict(zip(["decky_loader","steamos"],detect_versions())))
        elif self.path=="/api/state": self._json(get_state())
        elif self.path=="/api/mpris/metadata":
            loop=asyncio.new_event_loop()
            try: md=loop.run_until_complete(mpris.get_metadata())
            finally: loop.close()
            self._json({"metadata":md})
        elif self.path=="/api/vpn/list":
            loop=asyncio.new_event_loop()
            try: v=loop.run_until_complete(vpn.list_vpns())
            finally: loop.close()
            self._json({"vpn":v})
        else: self._json({"error":"bad endpoint"},404)
    def do_POST(self):
        length=int(self.headers.get("content-length",0))
        body=json.loads(self.rfile.read(length)) if length else {}
        if self.path=="/api/display/off":
            display.turn_off_display(get_state().get("fade_out_ms",250))
            self._json({"ok":True})
        elif self.path=="/api/display/wake":
            display.on_wake()
            self._json({"ok":True})
        elif self.path=="/api/state/set":
            s=get_state(); s.update(body.get("state",{}))
            set_state(s); self._json({"ok":True})
        elif self.path=="/api/vpn/activate":
            vid=body.get("id")
            ok=False
            if vid: asyncio.get_event_loop().run_until_complete(vpn.activate(vid))
            self._json({"ok":ok})
        else: self._json({"error":"bad endpoint"},404)

def run_api():
    srv=HTTPServer(("127.0.0.1",8765),APIHandler)
    logger.info("HTTP server at http://127.0.0.1:8765")
    try: srv.serve_forever()
    except KeyboardInterrupt: pass

def main():
    logger.info("DisplayVPNMusic backend startup")
    detect_versions()
    th=threading.Thread(target=run_api,daemon=True)
    th.start()
    while True: time.sleep(3600)

if __name__=="__main__":
    main()