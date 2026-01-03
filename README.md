# MultiDeck Decky Loader Plugin

## Overview
Decky Loader plugin for Steam Deck:
- **Display Off** with fade, state persistence, sleep inhibition, and wake detection.
- **Music Control** (MPRIS via DBus, playerctl fallback): artwork, track, controls.
- **VPN Management** (NetworkManager DBus preferred, nmcli fallback): select/connect VPNs, validation & rollback.
- Native SteamOS UX, controller-friendly, atomic state/write, safe rollbacks.
- **Tested & Verified:** Decky Loader v3.2.1, SteamOS v3.7.17.

---

## Feature List

- **Display Off**
  - Detect X11/Wayland; use `xset dpms force off` for X11, compositor/DBus for Wayland.
  - Fade to black before display off, restore brightness after wake.
  - Sleep inhibition via `org.freedesktop.login1.Inhibit` (no lockfiles).
  - Wake watcher via DBus (fall back: input events).
  - Optionally mute speaker/mic; restore state after wake.
  - Settings: fade times, mute toggles, battery sleep threshold.

- **Music Control**
  - MPRIS via DBus (preferred); fallback to playerctl with visible warning.
  - Show artwork, title, artist.
  - Controls: Previous, Play/Pause, Next.

- **VPN Management**
  - NetworkManager DBus APIs; fallback: nmcli with warning.
  - System-wide VPN selection/activation; “None” option.
  - Show last 5 used VPNs, expand for all.
  - Auto-connect option; KDE settings sync.
  - State reflected on startup; active VPN underlined in green.

- **VPN Connectivity Validation & Rollback**
  - Validate after activation: DBus state, routing, optional reachability.
  - Timeout/failure: rollback, restore state, notify user.

---

## Supported Versions

- **Decky Loader:** 3.2.1
- **SteamOS:** 3.7.17

**Any version mismatches are logged and shown in this README.** Logs accessible via `journalctl -u plugin-displayvpnmusic`.

---

## Installation

1. **Clone repo:**
   ```
   git clone https://github.com/YOUR_ORG/displayvpnmusic.git
   cd displayvpnmusic
   ```
2. **Dependencies:**  
   Run the script (may require `sudo`):
   ```
   sudo ./deps/install_deps.sh
   ```
3. **Frontend build:**
   ```
   cd frontend
   npm install
   npm run build
   ```
4. **Deploy plugin:**  
   Place repo in Decky Loader's plugins folder (see [Decky docs](https://github.com/SteamDeckHomebrew/decky-plugin-template)).  
   Ensure backend executable permissions:  
   ```
   chmod +x backend/backend.py
   ```
5. **Start backend (systemd recommended for logging):**  
   Use `plugin-displayvpnmusic.service` or run backend manually for debug:
   ```
   python3 backend/backend.py
   ```

---

## Usage

- Open Decky Loader, go to the plugin tab.
- **Display Off:** Press button, display fades to black, sleep inhibited, restored on wake.
- **Music:** See player info/artwork, control playback, get warnings if using `playerctl`.
- **VPN:** Pick VPN; last 5 shown, option to expand. Select and activate. See error/warning states.
- **Settings:** Configure fade timings, mute toggles, battery policy, VPN auto-connect.

---

## Known Limitations

- **Wayland support:**  
  Compositor-specific handling—fallback to fade if unable to modify display.  
  See logs for which method was used or if your compositor requires adjustment.
- **Input event watching:**  
  May require extra permissions; DBus preferred.  
  Audio mute/restore uses system commands (Pulse/pipewire); may need tweaking for your setup.
- **Fallbacks:**  
  - Playerctl and nmcli used **only if** DBus APIs are unavailable; plugin gives a visible UI warning.
  - VPN validation/rollback may require customization for networking configs.

---

## Development setup

- Frontend: TypeScript/React (`frontend/src`)
- Backend: Python (`backend/`)
- Build: see `frontend/package.json` and `webpack.config.js`.
- UI: [decky-frontend-lib](https://github.com/SteamDeckHomebrew/decky-frontend-lib)

---

## Logging & Debugging

- Structured backend logs: DEBUG/INFO/WARNING/ERROR.  
  View logs:
  ```
  journalctl -u plugin-displayvpnmusic
  ```
  Startup logs include detected Decky Loader/SteamOS versions, backend state, and compatibility warnings.

---

## License

MIT (see LICENSE file).

---

## Contributing

PRs and issues welcome! See [plugin repo](https://github.com/YOUR_ORG/displayvpnmusic).
