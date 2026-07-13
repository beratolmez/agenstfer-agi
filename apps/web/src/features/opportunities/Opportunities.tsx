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
          <header><h2>Exact source locator</h2><button type="button" aria-label="Evidence kapat" onClick={() => setEvidence(null)}><X size={18} /></button></header>
          <pre>{JSON.stringify(evidence, null, 2)}</pre>
          <a href={`/api/evidence/${String(evidence.id ?? "")}`} target="_blank" rel="noreferrer"><ExternalLink size={15} /> API kaydını aç</a>
        </div>
      ) : null}
    </main>
  );
}
