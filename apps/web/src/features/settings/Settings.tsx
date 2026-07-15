import { Bot, Braces, RefreshCw, Server, Settings2, UserPlus, Workflow } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { api } from "../../api";
import type { WorkflowRunDetail, WorkflowRunView } from "../../types";

export function Settings({ onSetup }: { onSetup: () => void }) {
  const [model, setModel] = useState<{ ready: boolean; profile: string; provider: string; model?: string; message: string } | null>(null);
  const [agents, setAgents] = useState<Array<Record<string, unknown>>>([]);
  const [capabilities, setCapabilities] = useState<Array<Record<string, unknown>>>([]);
  const [runs, setRuns] = useState<WorkflowRunView[]>([]);
  const [users, setUsers] = useState<Array<{ id: string; email: string; name: string; roles: string[]; active: boolean }>>([]);
  const [newUser, setNewUser] = useState({ name: "", email: "", password: "", roles: ["analyst"] });
  const [trace, setTrace] = useState<WorkflowRunDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => {
    try {
      const [modelResult, agentResult, capabilityResult, runResult, userResult] = await Promise.all([api.modelStatus(), api.agents(), api.capabilities(), api.runs(), api.users()]);
      setModel(modelResult); setAgents(agentResult.items); setCapabilities(capabilityResult.items); setRuns(runResult.items); setUsers(userResult.items); setError(null);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Ayarlar yüklenemedi"); }
  }, []);
  useEffect(() => { void load(); }, [load]);
  async function inspect(runId: string) {
    try { setTrace(await api.runDetail(runId)); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Run trace yüklenemedi"); }
  }
  async function addUser(event: React.FormEvent) {
    event.preventDefault();
    try { await api.createUser(newUser); setNewUser({ name: "", email: "", password: "", roles: ["analyst"] }); await load(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Kullanıcı oluşturulamadı"); }
  }
  return <main className="page settings-page">
    <header className="page-heading"><div><p className="eyebrow">CONTROL PLANE</p><h1>Ayarlar ve Registry</h1><p>Model, agent, capability ve immutable run sürümlerini denetleyin.</p></div><div><button type="button" onClick={onSetup}><Settings2 size={17} /> Kurulum sihirbazı</button><button type="button" onClick={load}><RefreshCw size={17} /> Yenile</button></div></header>
    {error ? <div className="inline-alert inline-alert--error" role="alert">{error}</div> : null}
    <div className="settings-grid"><section className="settings-card"><Server size={24} /><h2>Model profili</h2><strong>{model?.profile ?? "–"}</strong><p>{model?.provider} / {model?.model ?? "yapılandırılmadı"}</p><span className={`tag tag--${model?.ready ? "green" : "amber"}`}>{model?.ready ? "ready" : "not ready"}</span><small>{model?.message}</small><p>Cloud key UI veya veritabanında saklanmaz; host/Docker secret ile sağlanır.</p></section><section className="settings-card"><Bot size={24} /><h2>Agent Registry</h2><strong>{agents.length} sürüm</strong><ul>{agents.map((item) => <li key={`${item.id}-${item.version}`}>{String(item.name)} <span>v{String(item.version)} · {String(item.status)}</span></li>)}</ul></section><section className="settings-card"><Braces size={24} /><h2>Capability Registry</h2><strong>{capabilities.length} allowlisted capability</strong><ul>{capabilities.map((item) => <li key={`${item.id}-${item.version}`}>{String(item.id)} <span>code-defined</span></li>)}</ul></section><section className="settings-card"><UserPlus size={24} /><h2>Kullanıcılar ve roller</h2><strong>{users.length} kullanıcı</strong><ul>{users.map((item) => <li key={item.id}>{item.name}<span>{item.roles.join(" · ")}</span></li>)}</ul><form className="compact-form" onSubmit={addUser}><input aria-label="Yeni kullanıcı adı" placeholder="Ad soyad" value={newUser.name} minLength={2} onChange={(event) => setNewUser((current) => ({ ...current, name: event.target.value }))} required /><input aria-label="Yeni kullanıcı e-postası" type="email" placeholder="E-posta" value={newUser.email} onChange={(event) => setNewUser((current) => ({ ...current, email: event.target.value }))} required /><input aria-label="Yeni kullanıcı parolası" type="password" placeholder="En az 12 karakter" value={newUser.password} minLength={12} onChange={(event) => setNewUser((current) => ({ ...current, password: event.target.value }))} required /><select aria-label="Yeni kullanıcı rolü" value={newUser.roles[0]} onChange={(event) => setNewUser((current) => ({ ...current, roles: [event.target.value] }))}><option value="analyst">Analyst</option><option value="approver">Approver</option><option value="admin">Admin</option></select><button type="submit">Kullanıcı ekle</button></form></section></div>
    <section className="run-history"><h2><Workflow size={20} /> Run geçmişi</h2>{runs.length === 0 ? <p className="muted">Henüz run yok.</p> : runs.map((run) => <button className="run-row" type="button" key={run.id} onClick={() => inspect(run.id)}><span><strong>{run.workflow_id}</strong><small>v{run.workflow_version} · {new Date(run.started_at).toLocaleString("tr-TR")}</small></span><em className="tag">{run.status}</em><span>{run.current_step ?? "tamamlandı"}</span></button>)}</section>
    {trace ? <section className="trace-panel"><h2>Run trace</h2><pre>{JSON.stringify(trace, null, 2)}</pre></section> : null}
  </main>;
}
