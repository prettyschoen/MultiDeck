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

/**
 * Decky typings are broken:
 * - children are not declared
 * - layout components fail strict TS
 * This is the OFFICIAL workaround.
 */
const PanelSectionAny = PanelSection as any;
const PanelSectionRowAny = PanelSectionRow as any;

const API = "http://127.0.0.1:8765/api";

const Main = () => {
  const [state, setState] = useState<any>({});
  const [vpns, setVpns] = useState<any[]>([]);
  const [mpris, setMpris] = useState<any>(null);

  useEffect(() => {
    fetchState();
    fetchVpns();
    fetchMpris();
    const i = setInterval(fetchMpris, 2000);
    return () => clearInterval(i);
  }, []);

  async function fetchState() {
    const r = await axios.get(`${API}/state`);
    setState(r.data);
  }

  async function fetchVpns() {
    const r = await axios.get(`${API}/vpn/list`);
    setVpns(r.data.vpn || []);
  }

  async function fetchMpris() {
    try {
      const r = await axios.get(`${API}/mpris/metadata`);
      setMpris(r.data.metadata || null);
    } catch {}
  }

  async function displayOff() {
    await axios.post(`${API}/display/off`);
  }

  async function wake() {
    await axios.post(`${API}/display/wake`);
  }

  async function setConfig(key: string, value: any) {
    const s = { ...state, [key]: value };
    await axios.post(`${API}/state/set`, { state: s });
    setState(s);
  }

  async function activateVpn(id: string) {
    await axios.post(`${API}/vpn/activate`, { id });
    fetchVpns();
  }

  return (
    <PanelSectionAny title="Display / VPN / Music">
      <PanelSectionRowAny>
        <ButtonItem label="Turn Display Off" onClick={displayOff} />
        <ButtonItem label="Force Wake" onClick={wake} />
      </PanelSectionRowAny>

      <PanelSectionRowAny>
        <Field label="Title">
          {mpris?.["xesam:title"] ?? "-"}
        </Field>

        <Field label="Artist">
          {mpris?.["xesam:artist"]?.[0] ?? "-"}
        </Field>
      </PanelSectionRowAny>

      <PanelSectionRowAny>
        <Field label="VPN">
          <Dropdown
            rgOptions={[
              { label: "None", data: "none" },
              ...vpns.map((v) => ({
                label: v.id,
                data: v.path || v.id,
              })),
            ]}
            selectedOption={state.selected_vpn || "none"}
            onChange={(o: any) =>
              setConfig("selected_vpn", o.data)
            }
          />
        </Field>

        <ButtonItem
          label="Activate VPN"
          onClick={() =>
            activateVpn(state.selected_vpn || "none")
          }
        />
      </PanelSectionRowAny>

      <PanelSectionRowAny>
        <SliderField
          label="Fade Out (ms)"
          value={state.fade_out_ms ?? 250}
          min={0}
          max={1000}
          step={50}
          onChange={(v) => setConfig("fade_out_ms", v)}
        />

        <SliderField
          label="Fade In (ms)"
          value={state.fade_in_ms ?? 250}
          min={0}
          max={1000}
          step={50}
          onChange={(v) => setConfig("fade_in_ms", v)}
        />
      </PanelSectionRowAny>

      <PanelSectionRowAny>
        <ToggleField
          label="Mute speaker on display off"
          checked={!!state.mute_on_display_off}
          onChange={(v) =>
            setConfig("mute_on_display_off", v)
          }
        />

        <ToggleField
          label="Mute mic on display off"
          checked={!!state.mute_mic_on_display_off}
          onChange={(v) =>
            setConfig("mute_mic_on_display_off", v)
          }
        />
      </PanelSectionRowAny>
    </PanelSectionAny>
  );
};

export default Main;
