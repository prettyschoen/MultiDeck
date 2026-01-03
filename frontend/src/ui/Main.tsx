import { useEffect, useState } from "react";
import {
  PanelSection,
  PanelSectionRow,
  ButtonItem,
  ToggleField,
  SliderField,
  Dropdown,
  Field,
} from "decky-frontend-lib";
import axios from "axios";

const API = "http://127.0.0.1:8765/api";

export function Main() {
  const [state, setState] = useState<any>({});
  const [vpns, setVpns] = useState<any[]>([]);
  const [mpris, setMpris] = useState<any>(null);

  useEffect(() => {
    fetchState();
    fetchVpns();
    fetchMpris();
    const intv = setInterval(() => fetchMpris(), 2000);
    return () => clearInterval(intv);
  }, []);

  async function fetchState() {
    try {
      const r = await axios.get(`${API}/state`);
      setState(r.data);
    } catch (e) {}
  }
  async function fetchVpns() {
    try {
      const r = await axios.get(`${API}/vpn/list`);
      setVpns(r.data.vpn || []);
    } catch (e) {}
  }
  async function fetchMpris() {
    try {
      const r = await axios.get(`${API}/mpris/metadata`);
      setMpris(r.data.metadata || null);
    } catch (e) {}
  }
  async function displayOff() {
    await axios.post(`${API}/display/off`);
  }
  async function wake() {
    await axios.post(`${API}/display/wake`);
  }
  async function setConfig(k: string, v: any) {
    const s = { ...state, [k]: v };
    await axios.post(`${API}/state/set`, { state: s });
    setState(s);
  }
  async function activateVpn(id: string) {
    await axios.post(`${API}/vpn/activate`, { id });
    fetchVpns();
  }

  return (
    <PanelSection>
      <PanelSectionRow>
        <ButtonItem label="Turn Display Off" onClick={displayOff} layout="inline" />
        <ButtonItem label="Force Wake" onClick={wake} layout="inline" />
      </PanelSectionRow>
      <PanelSectionRow>
        <Field label="Title">{mpris?.["xesam:title"] ?? "-"}</Field>
        <Field label="Artist">{mpris?.["xesam:artist"] ? mpris["xesam:artist"][0] : "-"}</Field>
      </PanelSectionRow>
      <PanelSectionRow>
        <Dropdown
          label="VPN"
          rgOptions={[
            { label: "None", data: "none" },
            ...vpns.map((v: any) => ({
              label: v.id,
              data: v.path || v.id,
            })),
          ]}
          selectedOption={state.selected_vpn || "none"}
          onChange={(opt: any) => setConfig("selected_vpn", opt.data)}
        />
        <ButtonItem label="Activate VPN" onClick={() => activateVpn(state.selected_vpn || "none")} layout="inline" />
      </PanelSectionRow>
      <PanelSectionRow>
        <SliderField label="Fade Out (ms)" value={state.fade_out_ms || 250} min={0} max={1000} step={50}
          onChange={v => setConfig("fade_out_ms", v)} />
        <SliderField label="Fade In (ms)" value={state.fade_in_ms || 250} min={0} max={1000} step={50}
          onChange={v => setConfig("fade_in_ms", v)} />
      </PanelSectionRow>
      <PanelSectionRow>
        <ToggleField
          label="Mute speaker on display off"
          checked={!!state.mute_on_display_off}
          onChange={v => setConfig("mute_on_display_off", v)}
        />
        <ToggleField
          label="Mute mic on display off"
          checked={!!state.mute_mic_on_display_off}
          onChange={v => setConfig("mute_mic_on_display_off", v)}
        />
      </PanelSectionRow>
    </PanelSection>
  );
}

export default Main;