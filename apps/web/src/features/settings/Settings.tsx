import {
  Bot,
  Braces,
  Copy,
  Plus,
  RefreshCw,
  Save,
  Server,
  Settings2,
  ShieldCheck,
  Upload,
  UserPlus,
  Workflow,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api } from "../../api";
import type {
  AgentDefinitionView,
  CapabilityDefinitionView,
  ManagedUserView,
  ModelProfileView,
  WorkflowRunDetail,
  WorkflowRunView,
} from "../../types";

const outputTypes: AgentDefinitionView["output_type"][] = [
  "CompanyAnalysis",
  "OpportunityHypotheses",
  "EvidenceReview",
  "OKFChangeSet",
];
const classifications: AgentDefinitionView["data_classification"][] = [
  "public",
  "internal",
  "confidential",
  "restricted",
];
const risks: AgentDefinitionView["approval_risk"][] = ["low", "medium", "high"];
const roles = ["admin", "analyst", "approver"];

function newAgent(): AgentDefinitionView {
  return {
    id: "new-agent",
    name: "New Agent",
    version: 1,
    model_profile: "local-balanced",
    output_type: "CompanyAnalysis",
    capabilities: ["context.query"],
    timeout_seconds: 300,
    max_output_tokens: 900,
    data_classification: "internal",
    approval_risk: "medium",
    system_prompt: "Analyze only the supplied evidence and return the requested typed result.",
    status: "draft",
  };
}

export function Settings({
  onSetup,
  userRoles,
}: {
  onSetup: () => void;
  userRoles: string[];
}) {
  const isAdmin = userRoles.includes("admin");
  const [model, setModel] = useState<{
    ready: boolean;
    profile: string;
    provider: string;
    model?: string;
    message: string;
  } | null>(null);
  const [modelProfiles, setModelProfiles] = useState<ModelProfileView[]>([]);
  const [agents, setAgents] = useState<AgentDefinitionView[]>([]);
  const [capabilities, setCapabilities] = useState<CapabilityDefinitionView[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<AgentDefinitionView | null>(null);
  const [runs, setRuns] = useState<WorkflowRunView[]>([]);
  const [users, setUsers] = useState<ManagedUserView[]>([]);
  const [newUser, setNewUser] = useState({
    name: "",
    email: "",
    password: "",
    roles: ["analyst"],
  });
  const [trace, setTrace] = useState<WorkflowRunDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const selectionRevision = useRef(0);

  const load = useCallback(async (preferred?: AgentDefinitionView) => {
    const selectionAtStart = selectionRevision.current;
    try {
      const [modelResult, profileResult, agentResult, capabilityResult, runResult] =
        await Promise.all([
          api.modelStatus(),
          api.modelProfiles(),
          api.agents(),
          api.capabilities(),
          api.runs(),
        ]);
      setModel(modelResult);
      setModelProfiles(profileResult.items);
      setAgents(agentResult.items);
      setCapabilities(capabilityResult.items);
      setRuns(runResult.items);
      if (isAdmin) setUsers((await api.users()).items);

      const summary = preferred ?? agentResult.items[0] ?? null;
      const detail = summary && isAdmin
        ? await api.agentVersion(summary.id, summary.version)
        : summary;
      if (selectionRevision.current === selectionAtStart) {
        setSelectedAgent(detail);
      }
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Ayarlar yüklenemedi");
    }
  }, [isAdmin]);

  useEffect(() => { void load(); }, [load]);

  async function inspect(runId: string) {
    try { setTrace(await api.runDetail(runId)); }
    catch (reason) {
      setError(reason instanceof Error ? reason.message : "Run trace yüklenemedi");
    }
  }

  async function selectAgent(agent: AgentDefinitionView) {
    const revision = selectionRevision.current + 1;
    selectionRevision.current = revision;
    setError(null);
    try {
      const detail = isAdmin ? await api.agentVersion(agent.id, agent.version) : agent;
      if (selectionRevision.current === revision) setSelectedAgent(detail);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Agent sürümü yüklenemedi");
    }
  }

  async function saveAgent() {
    if (!selectedAgent) return;
    setBusy(true);
    setError(null);
    try {
      const saved = await api.saveAgent(selectedAgent);
      setNotice(`${saved.id} v${saved.version} taslağı kaydedildi.`);
      await load(saved);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Agent taslağı kaydedilemedi");
    } finally { setBusy(false); }
  }

  async function cloneAgent() {
    if (!selectedAgent) return;
    setBusy(true);
    setError(null);
    try {
      const draft = await api.cloneAgent(selectedAgent);
      setNotice(`${draft.id} v${draft.version} düzenlenebilir taslak olarak oluşturuldu.`);
      await load(draft);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Agent sürümü klonlanamadı");
    } finally { setBusy(false); }
  }

  async function publishAgent() {
    if (!selectedAgent) return;
    setBusy(true);
    setError(null);
    try {
      const saved = await api.saveAgent(selectedAgent);
      const published = await api.publishAgent(saved);
      setNotice(`${published.id} v${published.version} immutable olarak yayınlandı.`);
      await load(published);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Agent sürümü yayınlanamadı");
    } finally { setBusy(false); }
  }

  async function addUser(event: React.FormEvent) {
    event.preventDefault();
    try {
      await api.createUser(newUser);
      setNewUser({ name: "", email: "", password: "", roles: ["analyst"] });
      setNotice("Kullanıcı oluşturuldu.");
      await load(selectedAgent ?? undefined);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Kullanıcı oluşturulamadı");
    }
  }

  async function updateUser(user: ManagedUserView, nextRoles: string[], active = user.active) {
    if (nextRoles.length === 0) return;
    setError(null);
    try {
      await api.updateUserRoles(user.id, nextRoles, active);
      setNotice(`${user.name} rolleri güncellendi.`);
      await load(selectedAgent ?? undefined);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Kullanıcı rolleri güncellenemedi");
    }
  }

  function updateAgent<K extends keyof AgentDefinitionView>(
    field: K,
    value: AgentDefinitionView[K],
  ) {
    setSelectedAgent((current) => current ? { ...current, [field]: value } : current);
  }

  const selectedExists = useMemo(
    () => Boolean(selectedAgent && agents.some(
      (item) => item.id === selectedAgent.id && item.version === selectedAgent.version,
    )),
    [agents, selectedAgent],
  );

  function beginNewAgent() {
    selectionRevision.current += 1;
    setSelectedAgent(newAgent());
  }

  return <main className="page settings-page">
    <header className="page-heading">
      <div>
        <p className="eyebrow">CONTROL PLANE</p>
        <h1>Ayarlar ve Registry</h1>
        <p>Model, agent, capability ve immutable run sürümlerini denetleyin.</p>
      </div>
      <div>
        <button type="button" onClick={onSetup}><Settings2 size={17} /> Kurulum sihirbazı</button>
        <button type="button" onClick={() => load(selectedAgent ?? undefined)}>
          <RefreshCw size={17} /> Yenile
        </button>
      </div>
    </header>
    {error ? <div className="inline-alert inline-alert--error" role="alert">{error}</div> : null}
    {notice ? <div className="inline-alert inline-alert--success" role="status">{notice}</div> : null}

    <div className="settings-grid">
      <section className="settings-card">
        <Server size={24} />
        <h2>Model profili</h2>
        <strong>{model?.profile ?? "–"}</strong>
        <p>{model?.provider} / {model?.model ?? "yapılandırılmadı"}</p>
        <span className={`tag tag--${model?.ready ? "green" : "amber"}`}>
          {model?.ready ? "ready" : "not ready"}
        </span>
        <small>{model?.message}</small>
        <button
          type="button"
          onClick={async () => {
            setBusy(true);
            try {
              await api.probeModel(model?.profile || "cloud-balanced");
              const updatedStatus = await api.modelStatus();
              setModel(updatedStatus);
              setNotice("Model Gateway probe testi başarıyla tamamlandı!");
            } catch (err: any) {
              setError(err.message || "Model probe testi başarısız");
            } finally {
              setBusy(false);
            }
          }}
          disabled={busy}
          style={{
            marginTop: "12px",
            padding: "6px 12px",
            borderRadius: "6px",
            border: "1px solid #cbd5e1",
            background: "#ffffff",
            fontSize: "12px",
            fontWeight: 600,
            color: "#0f172a",
            cursor: "pointer",
          }}
        >
          🔌 Model Gateway Test Et
        </button>
        <p style={{ marginTop: "8px", fontSize: "11px", color: "#64748b" }}>
          Cloud key host/Docker secret ile sağlanır.
        </p>
      </section>
      <section className="settings-card">
        <Braces size={24} />
        <h2>Capability Registry</h2>
        <strong>{capabilities.length} allowlisted capability</strong>
        <ul>{capabilities.map((item) => <li key={`${item.id}-${item.version}`}>
          {item.name}<span>{item.id} · code-defined</span>
        </li>)}</ul>
      </section>
      <section className="settings-card">
        <ShieldCheck size={24} />
        <h2>Registry politikası</h2>
        <strong>Fail-closed</strong>
        <p>Published sürümler immutable’dır. Capability’ler kod allowlist’inden gelir.</p>
        <p>Agent prompt’u düzenlenebilir; kaynakları untrusted data sayan control-plane policy değiştirilemez.</p>
      </section>
    </div>

    <section className="registry-workspace">
      <aside className="registry-list">
        <header>
          <div><Bot size={18} /><h2>Agent sürümleri</h2></div>
          {isAdmin ? <button type="button" onClick={beginNewAgent}>
            <Plus size={15} /> Yeni
          </button> : null}
        </header>
        {agents.map((item) => <button
          className={selectedAgent?.id === item.id && selectedAgent.version === item.version
            ? "registry-version is-selected" : "registry-version"}
          key={`${item.id}-${item.version}`}
          onClick={() => selectAgent(item)}
          type="button"
        >
          <span><strong>{item.name}</strong><small>{item.id}</small></span>
          <em className="tag">v{item.version} · {item.status}</em>
        </button>)}
      </aside>

      <section className="registry-editor">
        {!selectedAgent ? <p className="muted">Agent sürümü seçin.</p> : <>
          <header>
            <div>
              <p className="eyebrow">{selectedAgent.status.toUpperCase()}</p>
              <h2>{selectedAgent.id} · v{selectedAgent.version}</h2>
            </div>
            {isAdmin ? <div className="registry-actions">
              {selectedAgent.status === "published" ? <button disabled={busy} onClick={cloneAgent} type="button">
                <Copy size={15} /> Taslak klonla
              </button> : <>
                <button disabled={busy} onClick={saveAgent} type="button"><Save size={15} /> Kaydet</button>
                <button className="primary-button" disabled={busy} onClick={publishAgent} type="button">
                  <Upload size={15} /> Yayınla
                </button>
              </>}
            </div> : null}
          </header>
          <fieldset disabled={!isAdmin || selectedAgent.status === "published"}>
            <div className="registry-form-grid">
              <label>Agent ID<input
                pattern="[a-z][a-z0-9_-]{2,79}"
                value={selectedAgent.id}
                disabled={selectedExists}
                onChange={(event) => updateAgent("id", event.target.value)}
              /></label>
              <label>Ad<input value={selectedAgent.name} onChange={(event) => updateAgent("name", event.target.value)} /></label>
              <label>Model profili<select
                value={selectedAgent.model_profile}
                onChange={(event) => updateAgent("model_profile", event.target.value as AgentDefinitionView["model_profile"])}
              >{modelProfiles.map((profile) => <option disabled={!profile.enabled} key={profile.id} value={profile.id}>
                {profile.id}{profile.available ? " · erişilebilir" : " · erişilebilir değil"}
              </option>)}</select></label>
              <label>Typed output<select
                value={selectedAgent.output_type}
                onChange={(event) => updateAgent("output_type", event.target.value as AgentDefinitionView["output_type"])}
              >{outputTypes.map((item) => <option key={item}>{item}</option>)}</select></label>
              <label>Data classification<select
                value={selectedAgent.data_classification}
                onChange={(event) => updateAgent("data_classification", event.target.value as AgentDefinitionView["data_classification"])}
              >{classifications.map((item) => <option key={item}>{item}</option>)}</select></label>
              <label>Approval risk<select
                value={selectedAgent.approval_risk}
                onChange={(event) => updateAgent("approval_risk", event.target.value as AgentDefinitionView["approval_risk"])}
              >{risks.map((item) => <option key={item}>{item}</option>)}</select></label>
              <label>Timeout (s)<input type="number" min={1} max={600} value={selectedAgent.timeout_seconds} onChange={(event) => updateAgent("timeout_seconds", Number(event.target.value))} /></label>
              <label>Max output token<input type="number" min={1} max={32768} value={selectedAgent.max_output_tokens} onChange={(event) => updateAgent("max_output_tokens", Number(event.target.value))} /></label>
            </div>
            <div className="capability-picker">
              <span>Capability eşleşmesi</span>
              {capabilities.map((capability) => <label key={capability.id}><input
                checked={selectedAgent.capabilities.includes(capability.id)}
                type="checkbox"
                onChange={(event) => updateAgent(
                  "capabilities",
                  event.target.checked
                    ? [...selectedAgent.capabilities, capability.id]
                    : selectedAgent.capabilities.filter((id) => id !== capability.id),
                )}
              />{capability.id}</label>)}
            </div>
            {isAdmin ? <label className="prompt-editor">Versioned agent instruction<textarea
              minLength={20}
              maxLength={8000}
              value={selectedAgent.system_prompt ?? ""}
              onChange={(event) => updateAgent("system_prompt", event.target.value)}
            /></label> : null}
          </fieldset>
        </>}
      </section>
    </section>

    {isAdmin ? <section className="user-management">
      <header><UserPlus size={18} /><h2>Kullanıcılar ve roller</h2></header>
      <div className="user-list">{users.map((item) => <article key={item.id}>
        <div><strong>{item.name}</strong><small>{item.email}</small></div>
        <div className="role-picker">{roles.map((role) => <button
          className={item.roles.includes(role) ? "is-selected" : ""}
          disabled={item.roles.length === 1 && item.roles.includes(role)}
          key={role}
          onClick={() => updateUser(
            item,
            item.roles.includes(role)
              ? item.roles.filter((current) => current !== role)
              : [...item.roles, role],
          )}
          type="button"
        >{role}</button>)}<button
          className={item.active ? "is-selected" : ""}
          onClick={() => updateUser(item, item.roles, !item.active)}
          type="button"
        >{item.active ? "active" : "disabled"}</button></div>
      </article>)}</div>
      <form className="compact-form" onSubmit={addUser}>
        <input aria-label="Yeni kullanıcı adı" placeholder="Ad soyad" value={newUser.name} minLength={2} onChange={(event) => setNewUser((current) => ({ ...current, name: event.target.value }))} required />
        <input aria-label="Yeni kullanıcı e-postası" type="email" placeholder="E-posta" value={newUser.email} onChange={(event) => setNewUser((current) => ({ ...current, email: event.target.value }))} required />
        <input aria-label="Yeni kullanıcı parolası" type="password" placeholder="En az 12 karakter" value={newUser.password} minLength={12} onChange={(event) => setNewUser((current) => ({ ...current, password: event.target.value }))} required />
        <select aria-label="Yeni kullanıcı rolü" value={newUser.roles[0]} onChange={(event) => setNewUser((current) => ({ ...current, roles: [event.target.value] }))}>
          <option value="analyst">Analyst</option><option value="approver">Approver</option><option value="admin">Admin</option>
        </select>
        <button type="submit">Kullanıcı ekle</button>
      </form>
    </section> : null}

    <section className="run-history">
      <h2><Workflow size={20} /> Run geçmişi</h2>
      {runs.length === 0 ? <p className="muted">Henüz run yok.</p> : runs.map((run) => <button className="run-row" type="button" key={run.id} onClick={() => inspect(run.id)}>
        <span><strong>{run.workflow_id}</strong><small>v{run.workflow_version} · {new Date(run.started_at).toLocaleString("tr-TR")}</small></span>
        <em className="tag">{run.status}</em><span>{run.current_step ?? "tamamlandı"}</span>
      </button>)}
    </section>
    {trace ? <section className="trace-panel"><h2>Run trace</h2><pre>{JSON.stringify(trace, null, 2)}</pre></section> : null}
  </main>;
}
