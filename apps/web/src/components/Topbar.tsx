import { useEffect, useState } from "react";
import { Building2, ChevronDown, Server } from "lucide-react";
import { api } from "../api";

export function Topbar() {
  const [model, setModel] = useState<{ ready: boolean; profile: string; provider: string; model?: string; local?: boolean; message: string } | null>(null);
  useEffect(() => {
    api.modelStatus().then(setModel).catch(() => setModel({ ready: false, profile: "unknown", provider: "unknown", message: "Model durumu alınamadı" }));
  }, []);
  const label = model?.local ? "Yerel model" : model?.provider === "unknown" ? "Model" : "Cloud model";
  return (
    <header className="topbar">
      <button className="topbar__company" type="button">
        <Building2 size={18} />
        <span>Anka Endüstriyel Otomasyon</span>
        <ChevronDown size={16} />
      </button>
      <div className="topbar__right">
        <div className="model-status">
          <span className={`status-dot ${model?.ready ? "status-dot--green" : ""}`} />
          <span><strong>{label}: {model?.ready ? "Hazır" : "Kontrol bekliyor"}</strong><small>{model?.ready ? `${model.profile} · ${model.provider}` : (model?.message ?? "Bağlanıyor…")}</small></span>
        </div>
        <Server size={19} className="topbar__server" />
        <button className="user-menu" type="button">
          <span className="avatar">MK</span>
          <span><strong>Mehmet Kaya</strong><small>Yönetici</small></span>
          <ChevronDown size={15} />
        </button>
      </div>
    </header>
  );
}
