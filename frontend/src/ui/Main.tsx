import { useEffect, useState } from "react";
import {
  PanelSection,
  PanelSectionRow,
  Button,
  Dropdown
} from "@decky/ui";

/* ---------------- API helper ---------------- */

async function api(path: string, body?: any) {
  const res = await fetch(`http://127.0.0.1:8765${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  return res.json();
}

/* ---------------- Main component ---------------- */

export default function Main() {
  const [vpns, setVpns] = useState<string[]>([]);
  const [activeVpn, setActiveVpn] = useState<string | null>(null);
  const [backendOk, setBackendOk] = useState(true);

  /* -------- Initial VPN list -------- */

  async function refreshVpns() {
    try {
      const data = await api("/vpn/list");
      setVpns(data.vpns ?? []);
      setBackendOk(true);
    } catch {
      setBackendOk(false);
    }
  }

  /* -------- Live VPN status polling -------- */

  useEffect(() => {
    refreshVpns();

    const id = setInterval(async () => {
      try {
        const data = await api("/vpn/status");
        setActiveVpn(data.active ?? null);
        setBackendOk(true);
      } catch {
        setBackendOk(false);
      }
    }, 1500);

    return () => clearInterval(id);
  }, []);

  /* ---------------- UI ---------------- */

  return (
    <>
      {/* ---------- Display ---------- */}
      <PanelSection title="Display" />

      <PanelSectionRow>
        <Button onClick={() => api("/display/off", { fade_ms: 500 })}>
          Turn Display Off
        </Button>
      </PanelSectionRow>

      {/* ---------- VPN ---------- */}
      <PanelSection title="VPN" />

      <PanelSectionRow>
        <div style={{ fontSize: "0.9em", opacity: 0.8 }}>
          Select VPN
        </div>
      </PanelSectionRow>

      <PanelSectionRow>
        <Dropdown
          rgOptions={vpns.map(v => ({
            label: v,
            data: v,
          }))}
          selectedOption={activeVpn}
          onChange={async (opt) => {
            await api("/vpn/on", { name: opt.data });
          }}
        />
      </PanelSectionRow>

      <PanelSectionRow>
        <Button
          onClick={() => {
            if (activeVpn) {
              api("/vpn/off", { name: activeVpn });
            }
          }}
          disabled={!activeVpn}
        >
          Disconnect VPN
        </Button>
      </PanelSectionRow>

      {/* ---------- Status ---------- */}
      <PanelSectionRow>
        <div style={{ opacity: 0.8 }}>
          {activeVpn
            ? `🔒 VPN Connected: ${activeVpn}`
            : "🔓 VPN Disconnected"}
        </div>
      </PanelSectionRow>

      {!backendOk && (
        <PanelSectionRow>
          <div style={{ color: "red" }}>
            Backend not responding
          </div>
        </PanelSectionRow>
      )}
    </>
  );
}
