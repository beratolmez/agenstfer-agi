import React from 'react';

const WebScrapingPanel: React.FC = () => {
  return (
    <div className="scraping-panel" style={{ maxWidth: "900px", margin: "0 auto", padding: "24px", background: "#ffffff", borderRadius: "12px", border: "1px solid #e2e8f0" }}>
      <header style={{ marginBottom: "20px", borderBottom: "1px solid #f1f5f9", paddingBottom: "16px" }}>
        <h2 style={{ fontSize: "20px", fontWeight: 700, color: "#0f172a", margin: 0 }}>
          🌐 Web Scraping & Data Fetching Control Panel
        </h2>
        <p style={{ fontSize: "14px", color: "#64748b", margin: "4px 0 0" }}>
          Ajan iş akışları tarafından çağrılan kod tanımlı <code>web.scrape</code> yetenek paneli.
        </p>
      </header>

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
            ⚙️ Runtime Capability Status
          </h3>
          <ul style={{ fontSize: "13px", color: "#1e3a8a", margin: 0, paddingLeft: "20px", lineHeight: 1.6 }}>
            <li>Capability ID: <code>web.scrape</code> (Allowlisted Read-Only Web Scraping)</li>
            <li>Execution Scope: İş akışı ajan adımları (Agent Run Nodes) tarafından tetiklenir.</li>
            <li>Security Constraint: Arbitrary URL polling ve arka plan istemci scraper servisleri politika gereği kapalıdır.</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default WebScrapingPanel;
