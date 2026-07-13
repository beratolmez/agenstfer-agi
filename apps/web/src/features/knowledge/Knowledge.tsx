import { BookOpen, FileText, Link2, Search, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../../api";

export function Knowledge() {
  const [items, setItems] = useState<Array<Record<string, unknown>>>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => { api.knowledge().then((result) => setItems(result.items)).finally(() => setLoading(false)); }, []);
  async function search() {
    setLoading(true);
    try { setItems((await api.knowledge(query)).items); } finally { setLoading(false); }
  }
  return (
    <main className="knowledge-page">
      <header><div><h1>Bilgi Bankası</h1><p>OKF 0.1 bundle içeriği, bağlantıları ve kanıt kaynakları.</p></div><button className="primary-button" type="button"><ShieldCheck size={17} /> Bundle doğrula</button></header>
      <form onSubmit={(event) => { event.preventDefault(); void search(); }}><Search size={18} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Concept, kaynak veya büyüme hipotezi ara…" /><button type="submit">Ara</button></form>
      <div className="knowledge-layout">
        <aside><h2><BookOpen size={17} /> Company bundle</h2>{["organization", "products", "accounts", "opportunities", "metrics", "playbooks", "decisions", "reports", "references"].map((group) => <button type="button" key={group}>{group}</button>)}</aside>
        <section className="concept-list">
          <div className="concept-list__head"><span>Concept</span><span>Type</span><span>Backlink</span></div>
          {loading ? <p className="loading-state">Bilgi indeksi okunuyor…</p> : items.map((item) => (
            <button type="button" className="concept-row" key={String(item.path)}>
              <FileText size={19} />
              <span><strong>{String(item.title)}</strong><small>{String(item.path)}</small></span>
              <em>{String(item.type ?? item.engine ?? "Concept")}</em>
              <span><Link2 size={14} /> {String(item.backlinks ?? 0)}</span>
            </button>
          ))}
        </section>
      </div>
    </main>
  );
}

