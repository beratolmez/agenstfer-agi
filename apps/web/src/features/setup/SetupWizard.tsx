import { ArrowLeft, ArrowRight, Check, Database, Server, ShieldCheck, Sparkles } from "lucide-react";
import { useState } from "react";
import { api } from "../../api";

const steps = ["Yönetici", "Roller", "Yerel model", "Şirket hedefi", "Veri kaynağı", "Mapping", "OKF bundle", "Growth Diagnostic", "Taslak rapor", "Onay"];

export function SetupWizard({ onComplete }: { onComplete: () => void }) {
  const [step, setStep] = useState(0);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  async function next() {
    if (step === 6 && !result) {
      setRunning(true);
      try { setResult(await api.setupDemo()); } finally { setRunning(false); }
    }
    if (step === steps.length - 1) onComplete();
    else setStep((current) => current + 1);
  }
  const content = [
    { icon: ShieldCheck, title: "İlk yöneticiyi oluşturun", text: "Bootstrap token yalnız bir kez kullanılır. Demo modunda bu adım önizlemedir." },
    { icon: ShieldCheck, title: "Rol ayrımını doğrulayın", text: "Admin yapılandırır, Analyst inceler, Approver onaylar. İlk kullanıcı demo için üç role sahip olabilir." },
    { icon: Server, title: "Model profilini test edin", text: "local-balanced veya opt-in cloud-balanced structured-output probe. Model yoksa deterministic demo devam eder." },
    { icon: Sparkles, title: "90 günlük önceliği belirleyin", text: "Mevcut müşteri tabanından kârlı büyüme." },
    { icon: Database, title: "Veri kaynağını seçin", text: "Anka Endüstriyel Otomasyon sentetik CRM/ERP dataset'i read-only connector üzerinden yüklenecek." },
    { icon: Database, title: "Mapping önizlemesi", text: "Account, Contact, Opportunity, Product, Order ve Invoice canonical entity'lere eşlenir." },
    { icon: ShieldCheck, title: "OKF 0.1 bundle hazırlığı", text: "Reference concept, source hash, locator, index ve log üretilecek." },
    { icon: Sparkles, title: "Growth Diagnostic", text: "Dört agent sözleşmesi, deterministic metric ve evidence gate sırasıyla çalışır." },
    { icon: Sparkles, title: "Taslak raporu inceleyin", text: "Top-5 fırsat, kanıt kapsamı ve 30 günlük plan yayınlanmadan önce taslaktır." },
    { icon: Check, title: "OKF diff ve insan onayı", text: "Onaydan sonra candidate bilgi active bundle'a merge edilir." },
  ][step];
  const Icon = content.icon;
  return (
    <main className="setup-page">
      <div className="setup-progress">{steps.map((label, index) => <span className={index <= step ? "is-active" : ""} key={label}><i>{index < step ? <Check size={12} /> : index + 1}</i><small>{label}</small></span>)}</div>
      <section className="setup-panel">
        <Icon size={36} />
        <p>Adım {step + 1} / {steps.length}</p>
        <h1>{content.title}</h1>
        <p>{content.text}</p>
        {step === 0 ? <div className="setup-form"><label>Ad soyad<input defaultValue="Mehmet Kaya" /></label><label>Kurumsal e-posta<input defaultValue="admin@anka.local" /></label></div> : null}
        {step === 3 ? <div className="setup-form"><label>Şirket adı<input defaultValue="Anka Endüstriyel Otomasyon" /></label><label>90 günlük hedef<textarea defaultValue="Mevcut müşteri tabanından kârlı büyüme" /></label></div> : null}
        {result ? <div className="setup-success"><Check size={18} /><span><strong>Demo bundle hazır</strong><small>{String(result.company)} · OKF valid: {String(result.okf_valid)}</small></span></div> : null}
        <div className="setup-actions"><button type="button" disabled={step === 0} onClick={() => setStep((current) => current - 1)}><ArrowLeft size={17} /> Geri</button><button className="primary-button" type="button" onClick={next} disabled={running}>{running ? "Bundle hazırlanıyor…" : step === steps.length - 1 ? "Kurulumu tamamla" : "Devam et"}<ArrowRight size={17} /></button></div>
      </section>
    </main>
  );
}
