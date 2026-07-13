import { lazy, Suspense, useCallback, useEffect, useState } from "react";
import { api, ApiError } from "./api";
import { Brand } from "./components/Brand";
import { Sidebar, type ViewId } from "./components/Sidebar";
import { Topbar } from "./components/Topbar";
import { Dashboard } from "./features/dashboard/Dashboard";
import { Knowledge } from "./features/knowledge/Knowledge";
import { SetupWizard } from "./features/setup/SetupWizard";
import type { SetupStatus, UserView } from "./types";

const WorkflowEditor = lazy(() => import("./features/workflow/WorkflowEditor"));

function initialView(): ViewId {
  const hash = window.location.hash.replace("#", "") as ViewId;
  return ["dashboard", "knowledge", "opportunities", "workflow", "approvals", "sources", "settings", "setup"].includes(hash)
    ? hash
    : "dashboard";
}

function AuthGate({ status, onAuthenticated }: { status: SetupStatus; onAuthenticated: (user: UserView) => void }) {
  const [mode, setMode] = useState<"bootstrap" | "login">(status.bootstrap_required ? "bootstrap" : "login");
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const session = mode === "bootstrap"
        ? await api.bootstrap({ token, email, name, password })
        : await api.login({ email, password });
      if (session.user) onAuthenticated(session.user);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Kimlik doğrulama tamamlanamadı");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card">
        <Brand />
        <div className="auth-card__body">
          <p className="auth-eyebrow">Self-hosted control plane</p>
          <h1>{mode === "bootstrap" ? "İlk yöneticiyi oluşturun" : "Oturum açın"}</h1>
          <p>{mode === "bootstrap" ? "Bootstrap token yalnız ilk hesap için geçerlidir." : "Şirket çalışma alanına güvenli oturumla devam edin."}</p>
          <form onSubmit={submit}>
            {mode === "bootstrap" ? <label>Bootstrap token<input type="password" value={token} onChange={(event) => setToken(event.target.value)} required /></label> : null}
            {mode === "bootstrap" ? <label>Ad soyad<input value={name} onChange={(event) => setName(event.target.value)} minLength={2} required /></label> : null}
            <label>Kurumsal e-posta<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
            <label>Parola<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} minLength={12} required /></label>
            {error ? <div className="auth-error" role="alert">{error}</div> : null}
            <button className="primary-button" disabled={submitting} type="submit">{submitting ? "Kontrol ediliyor…" : mode === "bootstrap" ? "Yönetici oluştur" : "Oturum aç"}</button>
          </form>
          {!status.bootstrap_required ? <button className="auth-mode" type="button" onClick={() => setMode("login")}>Mevcut hesapla oturum aç</button> : null}
        </div>
      </section>
    </main>
  );
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
      <p>Bu yüzey henüz tamamlanmamış MVP çalışma alanıdır.</p>
      {view === "settings" ? <button className="primary-button" onClick={onSetup}>Kurulum sihirbazını aç</button> : null}
    </main>
  );
}

export default function App() {
  const [view, setView] = useState<ViewId>(initialView);
  const [setupStatus, setSetupStatus] = useState<SetupStatus | null>(null);
  const [user, setUser] = useState<UserView | null>(null);
  const [authReady, setAuthReady] = useState(false);

  useEffect(() => {
    api.setupStatus().then(async (status) => {
      setSetupStatus(status);
      if (!status.auth_enabled) {
        setUser({ id: "demo", email: "demo@local", name: "Demo Kullanıcı", roles: ["admin", "analyst", "approver"] });
      } else if (!status.bootstrap_required) {
        try {
          const session = await api.me();
          setUser(session.user);
        } catch {
          setUser(null);
        }
      }
      setAuthReady(true);
    }).catch(() => setAuthReady(true));
  }, []);

  useEffect(() => {
    const handleHash = () => setView(initialView());
    window.addEventListener("hashchange", handleHash);
    return () => window.removeEventListener("hashchange", handleHash);
  }, []);

  const navigate = useCallback((id: ViewId) => {
    window.location.hash = id;
    setView(id);
  }, []);

  if (!authReady) return <div className="loading-state">Güvenli oturum kontrol ediliyor…</div>;
  if (!setupStatus) return <main className="auth-page"><div className="auth-error">API bağlantısı kurulamadı.</div></main>;
  if (setupStatus.auth_enabled && !user) return <AuthGate status={setupStatus} onAuthenticated={setUser} />;

  const showTopbar = view !== "workflow";
  return (
    <div className="app-shell">
      <Sidebar active={view} onNavigate={navigate} />
      <div className="app-main">
        {showTopbar && user ? <Topbar user={user} onLogout={async () => { await api.logout(); setUser(null); }} /> : null}
        {view === "dashboard" || view === "opportunities" ? <Dashboard /> : null}
        {view === "knowledge" ? <Knowledge /> : null}
        {view === "workflow" ? (
          <Suspense fallback={<div className="loading-state">Workflow editörü yükleniyor…</div>}>
            <WorkflowEditor />
          </Suspense>
        ) : null}
        {view === "setup" ? <SetupWizard onComplete={() => navigate("dashboard")} /> : null}
        {(["approvals", "sources", "settings"] as ViewId[]).includes(view) ? <Placeholder view={view} onSetup={() => navigate("setup")} /> : null}
      </div>
    </div>
  );
}
