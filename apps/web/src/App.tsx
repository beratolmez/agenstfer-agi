import { lazy, Suspense, useCallback, useEffect, useState } from "react";
import { Sidebar, type ViewId } from "./components/Sidebar";
import { Topbar } from "./components/Topbar";
import { Dashboard } from "./features/dashboard/Dashboard";
import { Knowledge } from "./features/knowledge/Knowledge";
import { SetupWizard } from "./features/setup/SetupWizard";

const WorkflowEditor = lazy(() => import("./features/workflow/WorkflowEditor"));

function initialView(): ViewId {
  const hash = window.location.hash.replace("#", "") as ViewId;
  return ["dashboard", "knowledge", "opportunities", "workflow", "approvals", "sources", "settings", "setup"].includes(hash)
    ? hash
    : "dashboard";
}

function Placeholder({ view, onSetup }: { view: ViewId; onSetup: () => void }) {
  const titles: Partial<Record<ViewId, string>> = {
    opportunities: "Fırsatlar",
    approvals: "Onay Merkezi",
    sources: "Veri Kaynakları",
    settings: "Ayarlar",
  };
  return (
    <main className="page page--placeholder">
      <h1>{titles[view]}</h1>
      <p>Bu yüzey API sözleşmesine bağlı MVP çalışma alanıdır.</p>
      {view === "approvals" ? (
        <div className="approval-list">
          <button type="button"><span>Predictive bakım iş vakası</span><strong>Onay bekliyor</strong></button>
          <button type="button"><span>OKF Growth Diagnostic diff</span><strong>Onay bekliyor</strong></button>
          <button type="button"><span>OEM ihracat kapsam güncellemesi</span><strong>Taslak</strong></button>
        </div>
      ) : null}
      {view === "settings" ? <button className="primary-button" onClick={onSetup}>Kurulum sihirbazını aç</button> : null}
    </main>
  );
}

export default function App() {
  const [view, setView] = useState<ViewId>(initialView);
  useEffect(() => {
    const handleHash = () => setView(initialView());
    window.addEventListener("hashchange", handleHash);
    return () => window.removeEventListener("hashchange", handleHash);
  }, []);
  const navigate = useCallback((id: ViewId) => {
    window.location.hash = id;
    setView(id);
  }, []);
  const showTopbar = view !== "workflow";
  return (
    <div className="app-shell">
      <Sidebar active={view} onNavigate={navigate} />
      <div className="app-main">
        {showTopbar ? <Topbar /> : null}
        {view === "dashboard" || view === "opportunities" ? <Dashboard /> : null}
        {view === "knowledge" ? <Knowledge /> : null}
        {view === "workflow" ? (
          <Suspense fallback={<div className="loading-state">Workflow editörü yükleniyor…</div>}>
            <WorkflowEditor />
          </Suspense>
        ) : null}
        {view === "setup" ? <SetupWizard onComplete={() => navigate("dashboard")} /> : null}
        {["approvals", "sources", "settings"].includes(view) ? <Placeholder view={view} onSetup={() => navigate("setup")} /> : null}
      </div>
    </div>
  );
}

