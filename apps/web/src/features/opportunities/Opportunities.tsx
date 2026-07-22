import { ExternalLink, Search, ShieldCheck, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api } from "../../api";
import type { GrowthDiagnostic } from "../../types";

export function Opportunities() {
  const [diagnostic, setDiagnostic] = useState<GrowthDiagnostic | null>(null);
  const [query, setQuery] = useState("");
  const [evidence, setEvidence] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.dashboard().then(setDiagnostic).catch((reason: Error) => setError(reason.message));
  }, []);

  const items = useMemo(
    () => diagnostic?.opportunities.filter((item) =>
      `${item.title} ${item.subtitle}`.toLocaleLowerCase("tr-TR")
        .includes(query.toLocaleLowerCase("tr-TR"))) ?? [],
    [diagnostic, query],
  );

  async function openEvidence(evidenceId: string) {
    try {
      setEvidence(await api.evidence(evidenceId));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Evidence açılamadı");
    }
  }

  return (
    <main className="page opportunities-page">
      <header className="page-heading">
        <div>
          <p className="eyebrow">DETERMINISTIC PRIORITIZATION</p>
          <h1>Fırsatlar</h1>
          <p>Skorlar olasılık değil; persisted metric ve evidence temelli önceliklendirmedir.</p>
        </div>
        <label className="search-field">
          <Search size={17} />
          <input aria-label="Fırsat ara" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Fırsat ara…" />
        </label>
      </header>
      {error ? <div className="inline-alert inline-alert--error" role="alert">{error}</div> : null}
      <div className="opportunity-cards">
        {items.map((item) => (
          <article key={item.id}>
            <header><span className="score">{item.score}</span><span className="tag">{item.status}</span></header>
            <h2>{item.title}</h2>
            <p>{item.rationale}</p>
            <dl>
              <div><dt>Hedef uyumu</dt><dd>%{item.factors.goal_alignment}</dd></div>
              <div><dt>Etki</dt><dd>{item.impact}/10</dd></div>
              <div><dt>Evidence</dt><dd>%{item.factors.evidence_coverage}</dd></div>
            </dl>
            <footer>
              {item.evidence.map((ref) => (
                <button type="button" key={ref.id} onClick={() => openEvidence(ref.id)}>
                  <ShieldCheck size={15} /> {ref.source_id}
                </button>
              ))}
            </footer>
          </article>
        ))}
      </div>
      {evidence ? (
        <div className="diff-review evidence-review">
          <header>
            <h2 style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "16px" }}>
              <ShieldCheck size={18} style={{ color: "#0d9488" }} /> Doğrulanmış Kaynak Kanıtı (Locator)
            </h2>
            <button type="button" aria-label="Evidence kapat" onClick={() => setEvidence(null)}>
              <X size={18} />
            </button>
          </header>
          <div style={{ padding: "16px", display: "grid", gap: "12px", background: "#f8fafc", borderRadius: "8px", margin: "12px 0" }}>
            <div>
              <span style={{ fontSize: "11px", fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>Kanıt Kimliği (ID)</span>
              <div style={{ fontSize: "13px", fontWeight: 600, color: "#0f172a", fontFamily: "monospace" }}>{String(evidence.id ?? "-")}</div>
            </div>
            <div>
              <span style={{ fontSize: "11px", fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>Kaynak Bağlantısı (Source ID)</span>
              <div style={{ fontSize: "13px", fontWeight: 600, color: "#0284c7" }}>{String(evidence.source_id ?? "-")}</div>
            </div>
            {Boolean(evidence.excerpt) && (
              <div>
                <span style={{ fontSize: "11px", fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>Kanıt Metni / Alıntı (Excerpt)</span>
                <p style={{ fontSize: "13px", color: "#334155", background: "#ffffff", padding: "10px 12px", borderRadius: "6px", border: "1px solid #e2e8f0", margin: "4px 0 0 0" }}>
                  "{String(evidence.excerpt)}"
                </p>
              </div>
            )}
            {Boolean(evidence.created_at) && (
              <div>
                <span style={{ fontSize: "11px", fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>Oluşturulma Tarihi</span>
                <div style={{ fontSize: "12px", color: "#475569" }}>{new Date(String(evidence.created_at)).toLocaleString("tr-TR")}</div>
              </div>
            )}
          </div>
          <a href={`/api/evidence/${String(evidence.id ?? "")}`} target="_blank" rel="noreferrer" style={{ display: "inline-flex", alignItems: "center", gap: "6px", fontSize: "13px", fontWeight: 600, color: "#2563eb" }}>
            <ExternalLink size={15} /> Ham JSON Uç Noktasını Aç
          </a>
        </div>
      ) : null}
    </main>
  );
}
