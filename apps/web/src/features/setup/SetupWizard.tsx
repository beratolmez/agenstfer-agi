import { ArrowLeft, ArrowRight, Check, Database, Server, ShieldCheck, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../../api";
import type { GrowthDiagnostic, ModelProfileView, SetupProgress } from "../../types";

const steps = ["Yönetici", "Roller", "Model", "Şirket hedefi", "Veri kaynağı", "Mapping", "OKF bundle", "Growth Diagnostic", "Taslak rapor", "Onay"];
const defaultConfiguration = {
  company_name: "Anka Endüstriyel Otomasyon",
  objective: "Mevcut müşteri tabanından kârlı büyüme",
  model_profile: "local-balanced",
  source_mode: "synthetic-demo",
  locale: "tr-TR",
};

export function SetupWizard({ onComplete }: { onComplete: () => void }) {
  const [step, setStep] = useState(0);
  const [completed, setCompleted] = useState<number[]>([]);
  const [configuration, setConfiguration] = useState<Record<string, string | boolean | number>>(defaultConfiguration);
  const [running, setRunning] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [sourceResult, setSourceResult] = useState<{ total_records: number; sources: Array<{ source_id: string; records: number }> } | null>(null);
  const [diagnostic, setDiagnostic] = useState<GrowthDiagnostic | null>(null);
  const [modelResult, setModelResult] = useState<string | null>(null);
  const [modelProfiles, setModelProfiles] = useState<ModelProfileView[]>([]);
  const [okfResult, setOkfResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [approvalReason, setApprovalReason] = useState("Kanıtlar, rapor ve OKF diff kurulum sırasında incelendi.");

  useEffect(() => {
    Promise.all([api.setupProgress(), api.modelProfiles()]).then(([progress, profiles]) => {
      setStep(progress.current_step);
      setCompleted(progress.completed_steps);
      setConfiguration({ ...defaultConfiguration, ...progress.configuration });
      setModelProfiles(profiles.items);
      setLoaded(true);
    }).catch((reason: Error) => { setError(reason.message); setLoaded(true); });
  }, []);

  async function persist(nextStep: number, nextCompleted: number[], status: SetupProgress["status"] = "in_progress") {
    const saved = await api.saveSetupProgress({
      current_step: nextStep,
      completed_steps: nextCompleted,
      configuration,
      status,
    });
    setStep(saved.current_step);
    setCompleted(saved.completed_steps);
  }

  async function probeModel() {
    const probe = await api.probeModel(String(configuration.model_profile));
    setModelResult(`${probe.provider} / ${probe.model} · structured output doğrulandı`);
  }

  async function runPersistedDiagnostic() {
    const profile = String(configuration.model_profile);
    const workflow = await api.prepareDiagnosticWorkflow(profile);
    const started = await api.runDiagnostic(workflow);
    setDiagnostic(await api.waitForDiagnostic(started.run_id));
  }

  async function approveLatestCandidate() {
    const candidates = await api.okfCandidates();
    const pending = candidates.items.find((item) => item.status === "pending");
    if (pending) {
      await api.decideCandidate(pending.id, "approved", approvalReason);
      return;
    }
    if (!candidates.items.some((item) => item.status === "approved")) {
      throw new Error("Onaylanabilir OKF candidate bulunamadı");
    }
  }

  async function next() {
    setRunning(true);
    setError(null);
    try {
      if (step === 2) await probeModel();
      if (step === 4 && !sourceResult) setSourceResult(await api.syncDemoSource());
      if (step === 6) {
        const result = await api.validateOkf();
        if (!result.valid) throw new Error("Active OKF bundle doğrulaması başarısız");
        setOkfResult(`OKF 0.1 conformant · ${result.warnings.length} uyarı`);
      }
      if (step === 7 && !diagnostic) await runPersistedDiagnostic();
      if (step === 9) await approveLatestCandidate();
      const nextCompleted = [...new Set([...completed, step])].sort((a, b) => a - b);
      if (step === steps.length - 1) {
        await persist(step, nextCompleted, "completed");
        onComplete();
      } else {
        await persist(step + 1, nextCompleted);
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Kurulum adımı tamamlanamadı");
    } finally {
      setRunning(false);
    }
  }

  async function back() {
    const target = Math.max(0, step - 1);
    setRunning(true);
    try { await persist(target, completed); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Adım kaydedilemedi"); }
    finally { setRunning(false); }
  }

  const content = [
    { icon: ShieldCheck, title: "İlk yönetici hazır", text: "Güvenli bootstrap tamamlandı; kurulum değişiklikleri audit kaydına yazılır." },
    { icon: ShieldCheck, title: "Rol ayrımını doğrulayın", text: "Admin yapılandırır, Analyst çalıştırır, Approver candidate diff'i onaylar." },
    { icon: Server, title: "Model profilini test edin", text: "Seçili profil gerçek structured-output probe'dan geçmelidir. Otomatik provider fallback uygulanmaz." },
    { icon: Sparkles, title: "90 günlük önceliği belirleyin", text: "Şirket adı ve hedef sonraki diagnostic run'larında kurulum bağlamı olarak saklanır." },
    { icon: Database, title: "Veri kaynağını seçin", text: "Anka sentetik CRM/ERP verisi gerçek read-only connector hattından geçirilecek." },
    { icon: Database, title: "Mapping sonucunu doğrulayın", text: "Account, Contact, Opportunity, Product, Order ve Activity canonical entity'lere eşlendi." },
    { icon: ShieldCheck, title: "OKF 0.1 bundle doğrulaması", text: "Active bundle, source hash, locator, index ve log kurallarıyla doğrulanır." },
    { icon: Sparkles, title: "Growth Diagnostic çalıştırın", text: "Persisted metrikler, dört typed agent ve Evidence Reviewer sırasıyla çalışır." },
    { icon: Sparkles, title: "Taslak raporu inceleyin", text: "Top-5 fırsat, evidence coverage ve 30 günlük plan candidate olarak kalır." },
    { icon: Check, title: "OKF diff ve insan onayı", text: "Yalnız onaydan sonra candidate active knowledge main revision'ına merge edilir." },
  ][step];
  const Icon = content.icon;
  if (!loaded) return <main className="setup-page loading-state">Kurulum durumu yükleniyor…</main>;
  return (
    <main className="setup-page">
      <div className="setup-progress">{steps.map((label, index) => <span className={index <= step ? "is-active" : ""} key={label}><i>{completed.includes(index) ? <Check size={12} /> : index + 1}</i><small>{label}</small></span>)}</div>
      <section className="setup-panel">
        <Icon size={36} />
        <p>Adım {step + 1} / {steps.length}</p>
        <h1>{content.title}</h1>
        <p>{content.text}</p>
        {step === 2 ? <div className="setup-form"><label>Model profili<select value={String(configuration.model_profile)} onChange={(event) => { setConfiguration((current) => ({ ...current, model_profile: event.target.value })); setModelResult(null); }}>{modelProfiles.map((profile) => <option disabled={!profile.enabled} key={profile.id} value={profile.id}>{profile.id} · {profile.provider ?? "yapılandırılmadı"} / {profile.model ?? "model yok"}{profile.available ? " · erişilebilir" : " · erişilebilir değil"}</option>)}</select></label></div> : null}
        {step === 2 && modelResult ? <p className="setup-success"><Check size={18} />{modelResult}</p> : null}
        {step === 3 ? <div className="setup-form"><label>Şirket adı<input value={String(configuration.company_name)} onChange={(event) => setConfiguration((current) => ({ ...current, company_name: event.target.value }))} /></label><label>90 günlük hedef<textarea value={String(configuration.objective)} onChange={(event) => setConfiguration((current) => ({ ...current, objective: event.target.value }))} /></label></div> : null}
        {sourceResult ? <div className="setup-success"><Check size={18} /><span><strong>Kaynaklar kalıcılaştırıldı</strong><small>{sourceResult.total_records} kayıt · {sourceResult.sources.length} kaynak</small></span></div> : null}
        {step === 6 && okfResult ? <p className="setup-success"><Check size={18} />{okfResult}</p> : null}
        {step >= 8 && diagnostic ? <div className="setup-success"><Check size={18} /><span><strong>{diagnostic.company} taslak raporu</strong><small>{diagnostic.opportunities.length} fırsat · %{diagnostic.evidence_coverage} evidence</small></span></div> : null}
        {step === 9 ? <div className="setup-form"><label>Onay gerekçesi<textarea value={approvalReason} minLength={8} onChange={(event) => setApprovalReason(event.target.value)} /></label></div> : null}
        {error ? <p className="inline-alert inline-alert--error" role="alert">{error}</p> : null}
        <div className="setup-actions"><button type="button" disabled={step === 0 || running} onClick={back}><ArrowLeft size={17} /> Geri</button><button className="primary-button" type="button" onClick={next} disabled={running}>{running ? "Adım çalışıyor…" : step === steps.length - 1 ? "Onayla ve kurulumu tamamla" : step === 2 ? "Modeli test et ve devam et" : step === 7 ? "Tanıyı çalıştır ve devam et" : "Kaydet ve devam et"}<ArrowRight size={17} /></button></div>
      </section>
    </main>
  );
}
