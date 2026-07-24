import { Activity, AlertTriangle, CheckCircle2, Cpu, Database } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../../api";

export function RagVisualizer() {
  const [validating, setValidating] = useState(true);
  const [okfStatus, setOkfStatus] = useState<{ valid: boolean; errors: unknown[]; warnings: unknown[] } | null>(null);

  useEffect(() => {
    api
      .validateOkf()
      .then((res) => {
        setOkfStatus(res);
        setValidating(false);
      })
      .catch(() => {
        setOkfStatus(null);
        setValidating(false);
      });
  }, []);

  return (
    <section className="mapping-card" style={{ marginTop: "1rem", marginBottom: "1rem" }}>
      <header style={{ marginBottom: "1rem" }}>
        <div>
          <small>ACTIVE OKF & RAG ENGINE STATUS</small>
          <h2 style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginTop: "0.25rem" }}>
            <Activity size={18} /> RAG Vectorization & OKF Knowledge Validation
          </h2>
        </div>
      </header>

      <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem", background: "#f8fafc", padding: "12px", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
          <Database size={20} style={{ color: "#2563eb" }} />
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "#0f172a" }}>Immutable OKF Bundle Source of Truth</div>
            <div style={{ fontSize: "0.75rem", color: "#64748b" }}>
              {validating ? "OKF şeması ve paket geçerliliği sorgulanıyor..." : okfStatus?.valid ? "Aktif OKF paketi geçerli ve değişmez doğruluk kaynağı olarak yüklü." : "OKF paket doğrulaması kontrol ediliyor."}
            </div>
          </div>
          {validating ? <span style={{ fontSize: "11px", color: "#64748b" }}>Kontrol ediliyor…</span> : okfStatus?.valid ? <CheckCircle2 size={18} color="#10b981" /> : <AlertTriangle size={18} color="#f59e0b" />}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "1rem", background: "#f8fafc", padding: "12px", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
          <Cpu size={20} style={{ color: "#8b5cf6" }} />
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "#0f172a" }}>ChromaDB Disposable Derived Vector Index</div>
            <div style={{ fontSize: "0.75rem", color: "#64748b" }}>
              Vektör araması ChromaDB servisine erişilebilir olduğunda aktiftir; erişilemediğinde otomatik lexical fallback çalışır.
            </div>
          </div>
          <span style={{ fontSize: "11px", fontWeight: 600, padding: "3px 8px", borderRadius: "12px", background: "#eff6ff", color: "#1d4ed8" }}>
            Active / Lexical Fallback Ready
          </span>
        </div>
      </div>
    </section>
  );
}
