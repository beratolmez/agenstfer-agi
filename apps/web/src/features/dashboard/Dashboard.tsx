import {
  ArrowRight,
  Check,
  ChevronRight,
  ClipboardCheck,
  Database,
  ExternalLink,
  FileSpreadsheet,
  FileText,
  PlayCircle,
  ShieldCheck,
  Target,
  X,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api } from "../../api";
import type { ViewId } from "../../components/Sidebar";
import type { EvidenceRef, GrowthDiagnostic, Opportunity } from "../../types";

function Metric({ icon: Icon, label, value, helper, tone }: { icon: typeof Database; label: string; value: number; helper: string; tone: string }) {
  return (
    <div className={`metric metric--${tone}`}>
      <Icon size={38} strokeWidth={1.65} />
      <span><small>{label}</small><strong>{value}{label === "Açık onay" ? "" : "%"}</strong><em>{helper}</em></span>
    </div>
  );
}

function OpportunityTable({ items, onEvidence, onAll }: { items: Opportunity[]; onEvidence: (evidence: EvidenceRef) => void; onAll: () => void }) {
  const [selected, setSelected] = useState(items[0]?.id);
  return (
    <section className="opportunity-section">
      <h2>Öncelikli fırsatlar</h2>
      <div className="opportunity-table" role="table" aria-label="Öncelikli fırsatlar">
        <div className="opportunity-row opportunity-row--head" role="row">
          <span>Fırsat</span><span>Hedef uyumu</span><span>Etki</span><span>Kanıt</span><span>Skor</span><span />
        </div>
        {items.map((item, index) => (
          <div
            className={`opportunity-row ${selected === item.id ? "is-selected" : ""}`}
            key={item.id}
            onClick={() => setSelected(item.id)}
            role="row"
          >
            <span className="opportunity-title">
              <b>{index + 1}</b>
              <span><strong>{item.title}</strong><small>{item.subtitle}</small></span>
            </span>
            <span className="alignment"><Target size={17} />{item.target_alignment}</span>
            <span className="impact">{item.impact.toFixed(1)}/10</span>
            <span className="evidence-cell">
              <button className="evidence-link" type="button" onClick={(event) => { event.stopPropagation(); onEvidence(item.evidence[0]); }}>
                %{Math.round(item.factors.evidence_coverage)}
              </button>
              <i><i style={{ width: `${item.factors.evidence_coverage}%` }} /></i>
            </span>
            <span className="score">{item.score}</span>
            <ChevronRight size={17} />
          </div>
        ))}
        <button className="table-more" type="button" onClick={onAll}>Tüm fırsatları gör <ArrowRight size={17} /></button>
      </div>
    </section>
  );
}

function PlanRail({ plan }: { plan: GrowthDiagnostic["plan"] }) {
  return (
    <aside className="plan-rail">
      <h2>30 günlük plan</h2>
      <div className="timeline">
        {plan.map((item) => (
          <div className="timeline__item" key={item.week}>
            <i />
            <div>
              <strong>Hafta {item.week} <span>({item.range})</span></strong>
              <h3>{item.title}</h3>
              <ul>
                {item.actions.map((action, index) => (
                  <li className={item.week === 1 && index < 2 ? "is-done" : ""} key={action}>
                    <span>{item.week === 1 && index < 2 ? <Check size={12} /> : null}</span>{action}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}

function EvidenceDrawer({ evidence, onClose }: { evidence: EvidenceRef; onClose: () => void }) {
  return (
    <div className="drawer-backdrop" role="presentation" onMouseDown={onClose}>
      <aside className="evidence-drawer" role="dialog" aria-modal="true" aria-label="Kanıt ayrıntısı" onMouseDown={(event) => event.stopPropagation()}>
        <button className="drawer-close" type="button" onClick={onClose} aria-label="Kapat"><X size={20} /></button>
        <ShieldCheck size={34} className="drawer-icon" />
        <h2>Kanıt ayrıntısı</h2>
        <p>{evidence.label}</p>
        <dl>
          <div><dt>Source ID</dt><dd>{evidence.source_id}</dd></div>
          <div><dt>Konum</dt><dd>{String(evidence.locator.sheet)} · satır {String(evidence.locator.row)}</dd></div>
          <div><dt>Snapshot</dt><dd>{evidence.snapshot_sha256.slice(0, 18)}…</dd></div>
          <div><dt>Kapsam</dt><dd>%{Math.round(evidence.coverage * 100)}</dd></div>
        </dl>
        <div className="source-preview">
          <small>HAM KAYNAK KONUMU</small>
          <code>{JSON.stringify(evidence.locator, null, 2)}</code>
        </div>
        <a className="primary-button" href={`/api/evidence/${encodeURIComponent(evidence.id)}`} target="_blank" rel="noreferrer">Kaynak satırını aç <ExternalLink size={16} /></a>
      </aside>
    </div>
  );
}

function LowerActivity({ diagnostic, onEvidence, onNavigate }: { diagnostic: GrowthDiagnostic; onEvidence: (item: EvidenceRef) => void; onNavigate: (id: ViewId) => void }) {
  const evidence = diagnostic.opportunities.flatMap((item) => item.evidence).slice(0, 4);
  return (
    <div className="lower-activity">
      <section>
        <header><h2>Kanıt ve kaynaklar</h2><button type="button" onClick={() => onNavigate("knowledge")}>Tümünü gör</button></header>
        {evidence.map((item, index) => (
          <button className="source-row" key={item.id} onClick={() => onEvidence(item)} type="button">
            {index % 2 ? <FileSpreadsheet size={21} /> : <FileText size={21} />}
            <span><strong>{item.label}</strong><small>Kaynak: {item.source_id}</small></span>
            <em><ShieldCheck size={14} /> Doğrulandı</em>
            <i><i style={{ width: `${item.coverage * 100}%` }} /></i>
          </button>
        ))}
      </section>
      <section>
        <header><h2>Onay durumu</h2><button type="button" onClick={() => onNavigate("approvals")}>Onay merkezini aç</button></header>
        <div className="activity-row"><ClipboardCheck size={21} /><span><strong>{diagnostic.open_approvals ? `${diagnostic.open_approvals} açık onay isteği` : "Açık onay isteği yok"}</strong><small>Yalnız persisted ApprovalRequest kayıtları gösterilir.</small></span><em className={diagnostic.open_approvals ? "tag tag--amber" : "tag tag--green"}>{diagnostic.open_approvals ? "Onay bekliyor" : "Güncel"}</em></div>
      </section>
    </div>
  );
}

export function Dashboard({ onNavigate }: { onNavigate: (id: ViewId) => void }) {
  const [diagnostic, setDiagnostic] = useState<GrowthDiagnostic | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceRef | null>(null);
  useEffect(() => {
    api.dashboard()
      .then(setDiagnostic)
      .catch((reason: Error) => setLoadError(reason.message))
      .finally(() => setLoaded(true));
  }, []);
  const updated = useMemo(
    () => diagnostic ? new Intl.DateTimeFormat("tr-TR", { dateStyle: "medium", timeStyle: "short" }).format(new Date(diagnostic.generated_at)) : "",
    [diagnostic],
  );
  async function rerun() {
    setRunning(true);
    setRunError(null);
    try {
      const setup = await api.setupProgress();
      const profile = String(setup.configuration.model_profile ?? "local-balanced");
      const workflow = await api.prepareDiagnosticWorkflow(profile);
      const started = await api.runDiagnostic(workflow);
      setDiagnostic(await api.waitForDiagnostic(started.run_id));
    }
    catch (reason) { setRunError(reason instanceof Error ? reason.message : "Tanı çalıştırılamadı"); }
    finally { setRunning(false); }
  }
  if (!loaded) return <main className="page loading-state">Büyüme özeti hazırlanıyor…</main>;
  if (loadError) return <main className="page error-state"><h1>API bağlantısı kurulamadı</h1><p>{loadError}</p><button className="primary-button" onClick={() => window.location.reload()}>Yeniden dene</button></main>;
  if (!diagnostic) return (
    <main className="page dashboard-empty">
      <Database size={42} strokeWidth={1.5} />
      <h1>Henüz Growth Diagnostic yok</h1>
      <p>Dashboard yalnız başarıyla tamamlanmış ve evidence review kapısından geçmiş model run’larını gösterir. Sentetik preview, agent sonucu gibi sunulmaz.</p>
      {runError ? <div className="inline-alert inline-alert--error" role="alert"><strong>Tanı çalıştırılamadı.</strong> {runError}</div> : null}
      <button className="primary-button" type="button" onClick={rerun} disabled={running}><PlayCircle size={18} />{running ? "Tanı çalışıyor…" : "İlk tanıyı çalıştır"}</button>
    </main>
  );
  return (
    <main className="dashboard-page">
      <div className="dashboard-heading">
        <div><h1>Büyüme Özeti</h1><p>{diagnostic.summary}</p></div>
        <button className="primary-button" type="button" onClick={rerun} disabled={running}>
          <PlayCircle size={18} />{running ? "Tanı çalışıyor…" : "Tanıyı yeniden çalıştır"}
        </button>
      </div>
      {runError ? (
        <div className="inline-alert inline-alert--error" role="alert">
          <strong>Tanı çalıştırılamadı.</strong> {runError} Model profilini Kurulum ekranında
          test edin; sistem başka bir provider'a otomatik geçmez.
        </div>
      ) : null}
      <div className="dashboard-grid">
        <div className="metrics-strip">
          <Metric icon={Database} label="Veri hazırlığı" value={diagnostic.data_readiness} helper="İyi durumda" tone="teal" />
          <Metric icon={ShieldCheck} label="Kanıt kapsamı" value={diagnostic.evidence_coverage} helper="Yeterli" tone="green" />
          <Metric icon={ClipboardCheck} label="Açık onay" value={diagnostic.open_approvals} helper="Onay bekliyor" tone="amber" />
        </div>
        <OpportunityTable items={diagnostic.opportunities} onEvidence={setSelectedEvidence} onAll={() => onNavigate("opportunities")} />
        <PlanRail plan={diagnostic.plan} />
      </div>
      <LowerActivity diagnostic={diagnostic} onEvidence={setSelectedEvidence} onNavigate={onNavigate} />
      <footer className="dashboard-footer"><span>Son güncelleme: {updated}</span><span>Skor: deterministic-v1 · anlatı: yapılandırılmış model profili</span><span>{diagnostic.disclaimer}</span></footer>
      {selectedEvidence ? <EvidenceDrawer evidence={selectedEvidence} onClose={() => setSelectedEvidence(null)} /> : null}
    </main>
  );
}
