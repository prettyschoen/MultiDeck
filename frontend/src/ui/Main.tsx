import {
  Button,
  PanelSection,
  PanelSectionRow,
  Dropdown,
} from "@decky/ui";
import { useEffect, useState } from "react";

type VPNOption = {
  label: string;
  data: string | null;
};

export default function Main() {
  const [vpnOptions, setVpnOptions] = useState<VPNOption[]>([]);
  const [selectedVPN, setSelectedVPN] = useState<VPNOption | null>(null);

  useEffect(() => {
    // Placeholder until backend wiring
    const opts: VPNOption[] = [
      { label: "None", data: null },
      { label: "ExampleVPN", data: "example" },
    ];
    setVpnOptions(opts);
    setSelectedVPN(opts[0]);
  }, []);

  return (
    <PanelSection title="MultiDeck">
      <PanelSectionRow>
        <Button onClick={() => console.log("Display off requested")}>
          Display Off
        </Button>
      </PanelSectionRow>

      <PanelSectionRow>
        <div style={{ width: "100%" }}>
          <div style={{ marginBottom: "4px", fontSize: "12px", opacity: 0.7 }}>
            VPN Selection
          </div>
          <Dropdown
            rgOptions={vpnOptions}
            selectedOption={selectedVPN}
            onChange={(opt: VPNOption | null) => {
              setSelectedVPN(opt);
              console.log("VPN selected:", opt);
            }}
          />
        </div>
      </PanelSectionRow>
    </PanelSection>
  );
}
