import { useEffect, useState } from "react";
import {
  PanelSection,
  PanelSectionRow,
  Button,
  Dropdown,
  Toggle
} from "@decky/ui";

/* ---------------- API helper ---------------- */

async function api(path: string, body?: any) {
  const res = await fetch(`http://127.0.0.1:8765${path}`, {
    method: body ? "POST" : "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  return res.json();
}

/* ---------------- Main component ---------------- */

export default function Main() {
  const [vpns, setVpns] = useState<string[]>([]);
  const [selectedVpn, setSelectedVpn] = useState<string | null>(null);
  const [backendOk, setBackendOk] = useState(true);

  /* -------- Load VPN list -------- */

  async function refreshVpns() {
    try {
      const data = await api("/vpn/list");
      setVpns(data.vpns ?? []);
      setBackendOk(true);
    } catch {
      setBackendOk(false);
    }
  }

  useEffect(() => {
    refreshVpns();
  }, []);

  /* ---------------- UI ---------------- */

  return (
    <>
      {/* ---------- Display ---------- */}
      <PanelSection title="Display" />

      <PanelSectionRow>
        <Button
          onClick={() => api("/display/off", { fade_ms: 500 })}
        >
          Turn Display Off
        </Button>
      </PanelSectionRow>

      {/* ---------- VPN ---------- */}
      <PanelSection title="VPN" />

      {/* Label as SEPARATE TEXT (correct way) */}
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
          selectedOption={selectedVpn}
          onChange={async (opt) => {
            setSelectedVpn(opt.data);
            await api("/vpn/on", { name: opt.data });
          }}
        />
      </PanelSectionRow>

      <PanelSectionRow>
        <Button
          onClick={() => {
            if (selectedVpn) {
              api("/vpn/off", { name: selectedVpn });
            }
          }}
          disabled={!selectedVpn}
        >
          Disconnect VPN
        </Button>
      </PanelSectionRow>

      {/* ---------- Music ---------- */}
      <PanelSection title="Music" />

      <PanelSectionRow>
        <Button
          onClick={() => api("/music/metadata")}
        >
          Refresh Track Info
        </Button>
      </PanelSectionRow>

      {/* ---------- Backend status ---------- */}
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
