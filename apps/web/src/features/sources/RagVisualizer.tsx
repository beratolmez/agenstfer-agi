import { Activity, CheckCircle2, ChevronRight, Cpu, FileText } from "lucide-react";
import { useEffect, useState } from "react";

export function RagVisualizer() {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress((p) => (p < 100 ? p + 5 : 0));
    }, 500);
    return () => clearInterval(interval);
  }, []);

  return (
    <section className="mapping-card" style={{ marginTop: "1rem", marginBottom: "1rem" }}>
      <header style={{ marginBottom: "1rem" }}>
        <div>
          <small>PROCESSING PIPELINE</small>
          <h2 style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginTop: "0.25rem" }}>
            <Activity size={18} /> RAG Vectorization
          </h2>
        </div>
      </header>

      <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <FileText size={20} />
          <div style={{ flex: 1 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
              <span style={{ fontSize: "0.875rem", fontWeight: 500 }}>Document Chunking</span>
              <span style={{ fontSize: "0.875rem" }}>{Math.min(100, progress * 2)}%</span>
            </div>
            <div style={{ height: "4px", background: "#e2e8f0", borderRadius: "2px", overflow: "hidden" }}>
              <div style={{ height: "100%", width: `${Math.min(100, progress * 2)}%`, background: "#3b82f6", transition: "width 0.3s" }} />
            </div>
          </div>
          {progress >= 50 ? <CheckCircle2 size={16} color="#10b981" /> : <ChevronRight size={16} />}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <Cpu size={20} />
          <div style={{ flex: 1 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
              <span style={{ fontSize: "0.875rem", fontWeight: 500 }}>Embedding Generation</span>
              <span style={{ fontSize: "0.875rem" }}>{Math.max(0, Math.min(100, (progress - 50) * 2))}%</span>
            </div>
            <div style={{ height: "4px", background: "#e2e8f0", borderRadius: "2px", overflow: "hidden" }}>
              <div style={{ height: "100%", width: `${Math.max(0, Math.min(100, (progress - 50) * 2))}%`, background: "#8b5cf6", transition: "width 0.3s" }} />
            </div>
          </div>
          {progress >= 100 ? <CheckCircle2 size={16} color="#10b981" /> : <ChevronRight size={16} />}
        </div>
      </div>
    </section>
  );
}
