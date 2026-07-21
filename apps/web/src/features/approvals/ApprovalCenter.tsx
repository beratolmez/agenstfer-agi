import { Check, Download, GitCompare, RefreshCw, X, Bell } from "lucide-react";
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
  const [toast, setToast] = useState<{message: string, show: boolean}>({message: "", show: false});

  const load = useCallback(async () => {
    try {
      const [approvalResult, candidateResult] = await Promise.all([api.approvals(), api.okfCandidates()]);
      setApprovals(approvalResult.items);
      setCandidates(candidateResult.items);
      setError(null);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Onaylar yüklenemedi"); }
  }, []);
  useEffect(() => { void load(); }, [load]);

  // Mock real-time push notification
  useEffect(() => {
    const timer = setTimeout(() => {
      setToast({message: "Yeni bir ajan işlemi onay bekliyor: 'Rapor oluşturma'...", show: true});
      setTimeout(() => setToast(t => ({...t, show: false})), 5000);
    }, 4000);
    return () => clearTimeout(timer);
  }, []);

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
    <main className="page approvals-page" style={{ position: "relative" }}>
      {toast.show && (
        <div style={{ position: "absolute", top: 20, right: 38, background: "#10b981", color: "white", padding: "12px 16px", borderRadius: 6, display: "flex", alignItems: "center", gap: 10, zIndex: 100, boxShadow: "0 10px 15px -3px rgba(0,0,0,0.1)" }}>
          <Bell size={16} />
          <span style={{ fontSize: 13, fontWeight: 500 }}>{toast.message}</span>
        </div>
      )}
      <header className="page-heading">
        <div><p className="eyebrow">TRUST & POLICY</p><h1>Onay Merkezi</h1><p>Candidate knowledge değişiklikleri yalnız doğrulanmış insan kararıyla active olur.</p></div>
        <div><a className="secondary-button" href="/api/okf/export"><Download size={17} /> Active OKF export</a><button type="button" onClick={load} className="secondary-button"><RefreshCw size={17} /> Yenile</button></div>
      </header>
      {error ? <div className="inline-alert inline-alert--error" role="alert">{error}</div> : null}
      
      <section className="opportunity-section" style={{ maxWidth: 1180, margin: "0 auto 30px" }}>
        <h2>Workflow Onayları</h2>
        <div className="opportunity-table">
          <div className="opportunity-row opportunity-row--head">
            <span>Durum / İşlem</span>
            <span>Agent Rolü</span>
            <span>Run ID</span>
            <span>Son Tarih</span>
            <span>Aksiyonlar</span>
          </div>
          {approvals.length === 0 ? <div className="empty-panel">Workflow onayı yok</div> : approvals.map((item) => (
            <div className="opportunity-row" key={item.id}>
              <div className="opportunity-title">
                <span className={`tag tag--${item.status === "approved" ? "green" : "amber"}`}>{item.status}</span>
                <strong>{item.kind}</strong>
              </div>
              <div className="alignment">{item.requested_role}</div>
              <div className="impact" style={{ fontFamily: "monospace", fontSize: 11 }}>{item.run_id.slice(0, 8)}</div>
              <div className="score" style={{ color: "#64748b", fontWeight: 400 }}>{new Date(item.expires_at).toLocaleString("tr-TR")}</div>
              <div className="approval-actions" style={{ marginLeft: "auto" }}>
                {item.candidate_id ? <button type="button" onClick={() => showDiff(item.candidate_id!)}><GitCompare size={14} /> Diff</button> : null}
                {item.status === "pending" ? <>
                  <button type="button" disabled={busy} onClick={() => decideWorkflow(item, "rejected")} aria-label="Reddet"><X size={14} /></button>
                  <button className="primary-button" type="button" disabled={busy} onClick={() => decideWorkflow(item, "approved")} aria-label="Onayla" style={{ padding: "0 10px", minHeight: 32 }}><Check size={14} /></button>
                </> : null}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="opportunity-section" style={{ maxWidth: 1180, margin: "0 auto" }}>
        <h2>Bağımsız OKF Candidate'ları</h2>
        <div className="opportunity-table">
          <div className="opportunity-row opportunity-row--head">
            <span>Durum / ID</span>
            <span>Validation</span>
            <span style={{ gridColumn: "span 3" }}>Aksiyonlar</span>
          </div>
          {standalone.length === 0 ? <div className="empty-panel">Bağımsız candidate yok.</div> : standalone.map((item) => (
            <div className="opportunity-row" key={item.id}>
              <div className="opportunity-title">
                <span className="tag">{item.status}</span>
                <strong>{item.id}</strong>
              </div>
              <div className="alignment">{(item.validation_report.errors?.length ?? 0) === 0 ? "geçti" : "hatalı"}</div>
              <div className="approval-actions" style={{ gridColumn: "span 3", marginLeft: "auto" }}>
                <button type="button" onClick={() => showDiff(item.id)}><GitCompare size={14} /> Diff</button>
                {item.status === "pending" ? <>
                  <button type="button" onClick={() => decideCandidate(item, "rejected")} aria-label="Reddet"><X size={14} /></button>
                  <button className="primary-button" type="button" onClick={() => decideCandidate(item, "approved")} aria-label="Onayla" style={{ padding: "0 10px", minHeight: 32 }}><Check size={14} /></button>
                </> : null}
              </div>
            </div>
          ))}
        </div>
      </section>
      {selected ? <div className="diff-review"><header><div><h2>Candidate diff</h2><p>{selected}</p></div><button type="button" aria-label="Diff kapat" onClick={() => setSelected(null)}><X size={18} /></button></header><label>Karar gerekçesi<textarea value={reason} minLength={8} onChange={(event) => setReason(event.target.value)} /></label><pre>{diff || "Bu candidate dosya farkı içermiyor."}</pre></div> : null}
    </main>
  );
}
