import {
  BookOpen,
  CheckSquare,
  CircleGauge,
  Database,
  GitBranch,
  Settings,
  Target,
} from "lucide-react";
import type { ComponentType } from "react";
import { Brand } from "./Brand";

export type ViewId = "dashboard" | "scraping" | "knowledge" | "opportunities" | "workflow" | "approvals" | "sources" | "events" | "settings" | "setup";

const items: Array<{ id: ViewId; label: string; icon: ComponentType<{ size?: number; strokeWidth?: number }> }> = [
  { id: "dashboard", label: "Genel Bakış", icon: CircleGauge },
  { id: "scraping", label: "Veri Kazıma", icon: Target },
  { id: "knowledge", label: "Bilgi Bankası", icon: BookOpen },
  { id: "opportunities", label: "Fırsatlar", icon: Target },
  { id: "workflow", label: "İş Akışları", icon: GitBranch },
  { id: "approvals", label: "Onay Merkezi", icon: CheckSquare },
  { id: "sources", label: "Veri Kaynakları", icon: Database },
  { id: "events", label: "Olaylar & Webhook", icon: GitBranch },
  { id: "settings", label: "Ayarlar", icon: Settings },
];

interface SidebarProps {
  active: ViewId;
  onNavigate: (id: ViewId) => void;
}

export function Sidebar({ active, onNavigate }: SidebarProps) {
  return (
    <aside className="sidebar">
      <Brand />
      <nav className="sidebar__nav" aria-label="Ana menü">
        {items.map(({ id, label, icon: Icon }) => (
          <button
            className={`sidebar__item ${active === id ? "is-active" : ""}`}
            key={id}
            onClick={() => onNavigate(id)}
            type="button"
          >
            <Icon size={21} strokeWidth={1.8} />
            <span>{label}</span>
          </button>
        ))}
      </nav>
      <div className="sidebar__status">
        <span className="status-dot" />
        <span><strong>Sistem durumu</strong><small>Tüm yerel servisler</small></span>
      </div>
    </aside>
  );
}

