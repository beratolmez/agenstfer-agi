import { Check, Download, GitCompare, RefreshCw, ShieldCheck, X } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../../api";
import type { ApprovalView, OKFCandidateView } from "../../types";

export function ApprovalCenter() {
  const [approvals, setApprovals] = useState<ApprovalView[]>([]);
  const [candidates, setCandidates] = useState<OKFCandidateView[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [diff, setDiff] = useState("");
  const [reason, setReason] = useState("Kanıtlar ve OKF diff insan tarafından incelendi.");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => {
    try {
      const [approvalResult, candidateResult] = await Promise.all([api.approvals(), api.okfCandidates()]);
      setApprovals(approvalResult.items);
      setCandidates(candidateResult.items);
      setError(null);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Onaylar yüklenemedi"); }
  }, []);
  useEffect(() => { void load(); }, [load]);
  const linked = useMemo(() => new Set(approvals.map((item) => item.candidate_id).filter(Boolean)), [approvals]);
  const standalone = candidates.filter((item) => !linked.has(item.id));

  async function showDiff(candidateId: string) {
    setBusy(true);
    try { const result = await api.candidateDiff(candidateId); setSelected(candidateId); setDiff(result.diff); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Diff yüklenemedi"); }
    finally { setBusy(false); }
  }
  async function decideWorkflow(item: ApprovalView, decision: "approved" | "rejected") {
    setBusy(true);
    try { await api.decideApproval(item.id, decision, reason); await load(); setSelected(null); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Karar kaydedilemedi"); }
    finally { setBusy(false); }
  }
  async function decideCandidate(item: OKFCandidateView, decision: "approved" | "rejected") {
    setBusy(true);
    try { await api.decideCandidate(item.id, decision, reason); await load(); setSelected(null); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Karar kaydedilemedi"); }
    finally { setBusy(false); }
  }
  return (
    <main className="page approvals-page">
      <header className="page-heading"><div><p className="eyebrow">TRUST & POLICY</p><h1>Onay Merkezi</h1><p>Candidate knowledge değişiklikleri yalnız doğrulanmış insan kararıyla active olur.</p></div><div><a className="secondary-button" href="/api/okf/export"><Download size={17} /> Active OKF export</a><button type="button" onClick={load}><RefreshCw size={17} /> Yenile</button></div></header>
      {error ? <div className="inline-alert inline-alert--error" role="alert">{error}</div> : null}
      <section className="approval-list">
        <h2>Workflow onayları</h2>
        {approvals.length === 0 ? <div className="empty-panel"><ShieldCheck size={28} /><h3>Workflow onayı yok</h3><p>Evidence-reviewed bir run approval adımına geldiğinde burada görünür.</p></div> : approvals.map((item) => (
          <article className="approval-card" key={item.id}>
            <div><span className={`tag tag--${item.status === "approved" ? "green" : "amber"}`}>{item.status}</span><h3>{item.kind}</h3><p>Run {item.run_id.slice(0, 8)} · {item.requested_role}</p><small>Son tarih: {new Date(item.expires_at).toLocaleString("tr-TR")}</small></div>
            <div className="approval-actions">{item.candidate_id ? <button type="button" onClick={() => showDiff(item.candidate_id!)}><GitCompare size={16} /> Diff</button> : null}{item.status === "pending" ? <><button type="button" disabled={busy} onClick={() => decideWorkflow(item, "rejected")}><X size={16} /> Reddet</button><button className="primary-button" type="button" disabled={busy} onClick={() => decideWorkflow(item, "approved")}><Check size={16} /> Onayla</button></> : null}</div>
          </article>
        ))}
      </section>
      <section className="approval-list">
        <h2>Bağımsız OKF candidate'ları</h2>
        {standalone.length === 0 ? <p className="muted">Bağımsız candidate yok.</p> : standalone.map((item) => <article className="approval-card" key={item.id}><div><span className="tag">{item.status}</span><h3>{item.id}</h3><p>Validation: {(item.validation_report.errors?.length ?? 0) === 0 ? "geçti" : "hatalı"}</p></div><div className="approval-actions"><button type="button" onClick={() => showDiff(item.id)}><GitCompare size={16} /> Diff</button>{item.status === "pending" ? <><button type="button" onClick={() => decideCandidate(item, "rejected")}><X size={16} /> Reddet</button><button className="primary-button" type="button" onClick={() => decideCandidate(item, "approved")}><Check size={16} /> Onayla</button></> : null}</div></article>)}
      </section>
      {selected ? <div className="diff-review"><header><div><h2>Candidate diff</h2><p>{selected}</p></div><button type="button" aria-label="Diff kapat" onClick={() => setSelected(null)}><X size={18} /></button></header><label>Karar gerekçesi<textarea value={reason} minLength={8} onChange={(event) => setReason(event.target.value)} /></label><pre>{diff || "Bu candidate dosya farkı içermiyor."}</pre></div> : null}
    </main>
  );
}
