import React, { useEffect, useState } from 'react';
import { api } from '../../api';
import { CapabilityDefinitionView } from '../../types';

const WebScrapingPanel: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [webScrapeCap, setWebScrapeCap] = useState<CapabilityDefinitionView | null>(null);

  useEffect(() => {
    let isMounted = true;
    api.capabilities()
      .then((res) => {
        if (isMounted) {
          const found = res.items.find((item) => item.id === "web.scrape");
          setWebScrapeCap(found ?? null);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Capabilities yüklenirken hata oluştu");
          setLoading(false);
        }
      });
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="scraping-panel" style={{ maxWidth: "900px", margin: "0 auto", padding: "24px", background: "#ffffff", borderRadius: "12px", border: "1px solid #e2e8f0" }}>
      <header style={{ marginBottom: "20px", borderBottom: "1px solid #f1f5f9", paddingBottom: "16px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h2 style={{ fontSize: "20px", fontWeight: 700, color: "#0f172a", margin: 0 }}>
            🌐 Web Scraping & Data Fetching Control Panel
          </h2>
          <p style={{ fontSize: "14px", color: "#64748b", margin: "4px 0 0" }}>
            Ajan iş akışları tarafından çağrılan kod tanımlı <code>web.scrape</code> yetenek paneli.
          </p>
        </div>
        <div>
          {loading ? (
            <span style={{ fontSize: "12px", background: "#f1f5f9", color: "#64748b", padding: "4px 10px", borderRadius: "12px" }}>
              Yükleniyor...
            </span>
          ) : webScrapeCap ? (
            <span style={{ fontSize: "12px", fontWeight: 600, background: webScrapeCap.status === "published" || webScrapeCap.status === "available" ? "#dcfce7" : "#fef3c7", color: webScrapeCap.status === "published" || webScrapeCap.status === "available" ? "#15803d" : "#b45309", padding: "4px 10px", borderRadius: "12px" }}>
              Status: {webScrapeCap.status}
            </span>
          ) : (
            <span style={{ fontSize: "12px", background: "#fee2e2", color: "#b91c1c", padding: "4px 10px", borderRadius: "12px" }}>
              Kayıt Bulunamadı
            </span>
          )}
        </div>
      </header>

      {error && (
        <div style={{ padding: "12px", marginBottom: "16px", background: "#fef2f2", border: "1px solid #fca5a5", borderRadius: "6px", color: "#991b1b", fontSize: "13px" }}>
          ⚠️ API Hatası: {error}
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        <div style={{ padding: "16px", background: "#f8fafc", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
          <h3 style={{ fontSize: "15px", fontWeight: 600, color: "#1e293b", margin: "0 0 8px 0" }}>
            🛡️ Bounded Web Scraping Architecture Policy
          </h3>
          <p style={{ fontSize: "13px", color: "#475569", lineHeight: 1.6, margin: 0 }}>
            Web Kazıma (Web Scraping) yeteneği, bağımsız bir otomatik arka plan tarayıcısı olarak değil; onaylı ajan iş akışları içerisinde kod tanımlı <code>web.scrape</code> capability handler'ı üzerinden yürütülür. Sistem kontrol düzlemi tarafından belirlenen adresler salt-okunur olarak taranır ve içerikler kanıt süzgecinden (Evidence Gate) geçirilerek işlenir.
          </p>
        </div>

        <div style={{ padding: "16px", background: "#eff6ff", borderRadius: "8px", border: "1px solid #bfdbfe" }}>
          <h3 style={{ fontSize: "14px", fontWeight: 600, color: "#1e40af", margin: "0 0 6px 0" }}>
            ⚙️ Live Capability Registry Status
          </h3>
          <ul style={{ fontSize: "13px", color: "#1e3a8a", margin: 0, paddingLeft: "20px", lineHeight: 1.6 }}>
            <li>Capability ID: <code>{webScrapeCap?.id || "web.scrape"}</code></li>
            <li>Registry Name: {webScrapeCap?.name || "Authorized Web Scraping"}</li>
            <li>Implementation: <code>{String(webScrapeCap?.definition?.implementation || "code-defined")}</code></li>
            <li>Allowlisted: <code>{String(webScrapeCap?.definition?.allowlisted ?? true)}</code></li>
            <li>Execution Scope: İş akışı ajan adımları (Agent Run Nodes) tarafından tetiklenir.</li>
            <li>Security Constraint: Arbitrary URL polling ve arka plan istemci scraper servisleri politika gereği kapalıdır.</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default WebScrapingPanel;
