import { useEffect, useState } from "react";
import { Building2, LogOut, Server } from "lucide-react";
import { api } from "../api";
import type { UserView } from "../types";

export function Topbar({ user, onLogout }: { user: UserView; onLogout: () => Promise<void> }) {
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
      </button>
      <div className="topbar__right">
        <div className="model-status">
          <span className={`status-dot ${model?.ready ? "status-dot--green" : ""}`} />
          <span><strong>{label}: {model?.ready ? "Hazır" : "Kontrol bekliyor"}</strong><small>{model?.ready ? `${model.profile} · ${model.provider}` : (model?.message ?? "Bağlanıyor…")}</small></span>
        </div>
        <Server size={19} className="topbar__server" />
        <button className="user-menu" type="button" onClick={onLogout} title="Oturumu kapat">
          <span className="avatar">{user.name.split(" ").map((part) => part[0]).join("").slice(0, 2).toUpperCase()}</span>
          <span><strong>{user.name}</strong><small>{user.roles.join(" · ")}</small></span>
          <LogOut size={15} />
        </button>
      </div>
    </header>
  );
}
