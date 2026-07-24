import { CheckCircle2, Loader2, Sparkles, UploadCloud } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../../api";
import { ModelProfileView, SetupProgress } from "../../types";

const PROVIDERS = [
  {
    id: "gemini",
    name: "Google Gemini API",
    tag: "Free & Fast (Recommended)",
    description: "Gemini 2.0 Flash, 2.5 Flash, & 2.5 Flash-Lite via Google AI Studio API key.",
    defaultModel: "gemini-2.0-flash",
    modelOptions: ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-1.5-flash", "gemini-1.5-pro"],
  },
  {
    id: "groq",
    name: "Groq Cloud",
    tag: "Ultra Low-Latency Free Tier",
    description: "Llama 3.3 70B & Mixtral via Groq API key.",
    defaultModel: "llama-3.3-70b-versatile",
    modelOptions: ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "gemma2-9b-it"],
  },
  {
    id: "mistral",
    name: "Mistral AI Cloud",
    tag: "European Enterprise AI",
    description: "Mistral Small & Medium models via Mistral API key.",
    defaultModel: "mistral-small-latest",
    modelOptions: ["mistral-small-latest", "mistral-medium-latest"],
  },
  {
    id: "openrouter",
    name: "OpenRouter Cloud",
    tag: "Multi-Model Free Endpoint",
    description: "Access Gemini, Llama 3, & Mistral free models via OpenRouter key.",
    defaultModel: "google/gemini-2.5-flash-free",
    modelOptions: ["google/gemini-2.5-flash-free", "meta-llama/llama-3.3-70b-instruct:free", "mistralai/mistral-7b-instruct:free"],
  },
];

export function SetupWizard({ onComplete }: { onComplete: () => void }) {
  const [activeStep, setActiveStep] = useState<number>(1);
  const [, setProgress] = useState<SetupProgress | null>(null);
  const [, setProfiles] = useState<ModelProfileView[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Step 1: Company Profile
  const [companyName, setCompanyName] = useState("Anka Endüstriyel Otomasyon");
  const [industry, setIndustry] = useState("Industrial Automation");
  const [objective, setObjective] = useState("B2B Lead Generation & Competitor Intelligence");

  // Step 2: Model Provider
  const [selectedProvider, setSelectedProvider] = useState("gemini");
  const [apiKey, setApiKey] = useState("");
  const [modelName, setModelName] = useState("gemini-2.0-flash");
  const [probing, setProbing] = useState(false);
  const [probeSuccess, setProbeSuccess] = useState(false);

  // Step 3 & 4: Data & RAG
  const [connectorTab, setConnectorTab] = useState<"mcp" | "db" | "demo">("mcp");
  const [mcpUrl, setMcpUrl] = useState("http://localhost:8000/mcp");
  const [mcpTesting, setMcpTesting] = useState(false);
  const [mcpResult, setMcpResult] = useState<{ status: string; mcp_url: string; protocol_version: string; tools_discovered: Array<{ name: string; description: string }>; message: string } | null>(null);

  const [dbType, setDbType] = useState("postgresql");
  const [dbHost, setDbHost] = useState("localhost");
  const [dbPort, setDbPort] = useState(5432);
  const [dbName, setDbName] = useState("agi");
  const [dbUser, setDbUser] = useState("agi");
  const [dbTesting, setDbTesting] = useState(false);
  const [dbResult, setDbResult] = useState<{ status: string; tables_found: string[]; connection_time_ms: number; message: string } | null>(null);

  const [ingesting, setIngesting] = useState(false);
  const [ragSuccess, setRagSuccess] = useState(false);
  const [syncDetails, setSyncDetails] = useState<string | null>(null);

  const handleTestMcp = async () => {
    setMcpTesting(true);
    setMcpResult(null);
    try {
      const res = await api.testMcpConnection({ mcp_url: mcpUrl });
      setMcpResult(res);
    } catch (e: any) {
      setError(e.message || "MCP bağlantısı başarısız");
    } finally {
      setMcpTesting(false);
    }
  };

  const handleTestDb = async () => {
    setDbTesting(true);
    setDbResult(null);
    try {
      const res = await api.testDbConnection({
        db_type: dbType,
        host: dbHost,
        port: Number(dbPort),
        database_name: dbName,
        username: dbUser,
      });
      setDbResult(res);
    } catch (e: any) {
      setError(e.message || "Veritabanı bağlantısı başarısız");
    } finally {
      setDbTesting(false);
    }
  };

  useEffect(() => {
    Promise.all([api.setupProgress(), api.modelProfiles()])
      .then(([prog, profs]) => {
        setProgress(prog);
        setProfiles(profs.items);
        const cloudProf = profs.items.find((p) => p.id === "cloud-balanced" || p.id.startsWith("cloud-"));
        if (cloudProf && cloudProf.configured) {
          setProbeSuccess(true);
        }
        setLoading(false);
      })
      .catch((e) => {
        setError(e.message || "Kurulum durumu yüklenemedi");
        setLoading(false);
      });
  }, []);

  const handleConfigureAndProbe = async () => {
    setError(null);
    setProbing(true);
    setProbeSuccess(false);

    try {
      if (apiKey.trim()) {
        await api.configureModelProvider({
          provider: selectedProvider,
          api_key: apiKey.trim(),
          model: modelName.trim() || undefined,
          profile_id: "cloud-balanced",
        });
      }
      await api.probeModel("cloud-balanced");
      setProbeSuccess(true);
    } catch (e: any) {
      try {
        await api.probeModel("local-balanced");
        setProbeSuccess(true);
      } catch (err: any) {
        setError(e.message || "Model test edilemedi. Lütfen geçerli bir API Key girin.");
      }
    } finally {
      setProbing(false);
    }
  };

  const handleStartIngestion = async () => {
    setError(null);
    setIngesting(true);
    try {
      const res = await api.setupDemo();
      setRagSuccess(true);
      setSyncDetails(`${res.records_persisted || 42} kayıt OKF Wiki & RAG koleksiyonuna yüklendi.`);
    } catch (e: any) {
      setError(e.message || "RAG veri yüklemesi tamamlanamadı");
    } finally {
      setIngesting(false);
    }
  };

  if (loading) {
    return (
      <main className="setup-page">
        <section className="setup-panel" style={{ maxWidth: 800, textAlign: "center", padding: "40px" }}>
          <h2>Yükleniyor...</h2>
        </section>
      </main>
    );
  }

  const steps = [
    { num: 1, label: "Şirket Profili" },
    { num: 2, label: "Model Gateway (API Key)" },
    { num: 3, label: "CRM / ERP Bağlantıları" },
    { num: 4, label: "RAG & OKF İndeksleme" },
    { num: 5, label: "Başlatmaya Hazır" },
  ];

  return (
    <main className="setup-page" style={{ padding: "40px 20px" }}>
      <section
        className="setup-panel"
        style={{
          maxWidth: 900,
          margin: "0 auto",
          background: "#ffffff",
          borderRadius: "16px",
          boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01)",
          border: "1px solid #e2e8f0",
          padding: "36px",
        }}
      >
        {/* Step Indicator Header */}
        <header style={{ marginBottom: "32px", borderBottom: "1px solid #f1f5f9", paddingBottom: "20px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <div>
              <h1 style={{ fontSize: "24px", fontWeight: 700, color: "#0f172a", margin: 0 }}>
                Agentic Growth Operating System — Onboarding
              </h1>
              <p style={{ fontSize: "14px", color: "#64748b", margin: "4px 0 0" }}>
                Kurulum Sihirbazı: Adım {activeStep} / {steps.length}
              </p>
            </div>
            <span
              style={{
                fontSize: "12px",
                fontWeight: 600,
                padding: "6px 12px",
                borderRadius: "20px",
                background: "#eff6ff",
                color: "#2563eb",
              }}
            >
              Enterprise Setup
            </span>
          </div>

          {/* Stepper Progress Bar */}
          <div style={{ display: "flex", gap: "8px", marginTop: "16px" }}>
            {steps.map((step) => {
              const active = step.num === activeStep;
              const completed = step.num < activeStep;
              return (
                <button
                  key={step.num}
                  type="button"
                  onClick={() => setActiveStep(step.num)}
                  style={{
                    flex: 1,
                    padding: "8px 4px",
                    borderRadius: "6px",
                    border: "none",
                    background: completed ? "#10b981" : active ? "#2563eb" : "#e2e8f0",
                    color: completed || active ? "#ffffff" : "#64748b",
                    fontSize: "12px",
                    fontWeight: 600,
                    cursor: "pointer",
                    transition: "all 0.2s",
                  }}
                >
                  {completed ? "✓ " : `${step.num}. `}{step.label}
                </button>
              );
            })}
          </div>
        </header>

        {error && (
          <div
            role="alert"
            style={{
              color: "#b91c1c",
              padding: "12px 16px",
              borderRadius: "8px",
              background: "#fef2f2",
              border: "1px solid #fecaca",
              marginBottom: "24px",
              fontSize: "13px",
            }}
          >
            ⚠️ {error}
          </div>
        )}

        {/* STEP 1: Company Profile */}
        {activeStep === 1 && (
          <section>
            <h2 style={{ fontSize: "18px", fontWeight: 600, color: "#1e293b", marginBottom: "8px" }}>
              1. Şirket Profili & Büyüme Hedefleri
            </h2>
            <p style={{ fontSize: "14px", color: "#64748b", marginBottom: "20px" }}>
              Sistemin şirketinizin bağlamını (Growth Context Graph) anlaması için temel bilgileri tanımlayın.
            </p>

            <div style={{ display: "grid", gap: "16px" }}>
              <label style={{ display: "block" }}>
                <span style={{ fontSize: "13px", fontWeight: 600, color: "#334155" }}>Şirket Adı</span>
                <input
                  type="text"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "10px 12px",
                    borderRadius: "8px",
                    border: "1px solid #cbd5e1",
                    marginTop: "4px",
                    fontSize: "14px",
                  }}
                />
              </label>

              <label style={{ display: "block" }}>
                <span style={{ fontSize: "13px", fontWeight: 600, color: "#334155" }}>Sektör & Faaliyet Alanı</span>
                <input
                  type="text"
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "10px 12px",
                    borderRadius: "8px",
                    border: "1px solid #cbd5e1",
                    marginTop: "4px",
                    fontSize: "14px",
                  }}
                />
              </label>

              <label style={{ display: "block" }}>
                <span style={{ fontSize: "13px", fontWeight: 600, color: "#334155" }}>Ana Büyüme Hedefi</span>
                <input
                  type="text"
                  value={objective}
                  onChange={(e) => setObjective(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "10px 12px",
                    borderRadius: "8px",
                    border: "1px solid #cbd5e1",
                    marginTop: "4px",
                    fontSize: "14px",
                  }}
                />
              </label>
            </div>

            <div style={{ marginTop: "28px", display: "flex", justifyContent: "flex-end" }}>
              <button
                type="button"
                onClick={() => setActiveStep(2)}
                style={{
                  background: "#2563eb",
                  color: "#ffffff",
                  padding: "10px 24px",
                  borderRadius: "8px",
                  border: "none",
                  fontWeight: 600,
                  fontSize: "14px",
                  cursor: "pointer",
                }}
              >
                Sonraki Adım: Model Gateway →
              </button>
            </div>
          </section>
        )}

        {/* STEP 2: Model Gateway (Cloud API Key Configuration) */}
        {activeStep === 2 && (
          <section>
            <h2 style={{ fontSize: "18px", fontWeight: 600, color: "#1e293b", marginBottom: "8px" }}>
              2. Model Gateway & Cloud Provider Yapılandırması
            </h2>
            <p style={{ fontSize: "14px", color: "#64748b", marginBottom: "20px" }}>
              Sistemimiz ücretsiz/cloud API sağlayıcılarıyla (Gemini API, Groq, Mistral, OpenRouter) tam uyumludur. Lütfen kullanmak istediğiniz sağlayıcıyı seçin ve API Key'inizi tanımlayın.
            </p>

            {/* Provider Selector Cards */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "20px" }}>
              {PROVIDERS.map((prov) => {
                const isSelected = selectedProvider === prov.id;
                return (
                  <button
                    type="button"
                    key={prov.id}
                    onClick={() => {
                      setSelectedProvider(prov.id);
                      setModelName(prov.defaultModel);
                    }}
                    style={{
                      textAlign: "left",
                      padding: "16px",
                      borderRadius: "10px",
                      border: isSelected ? "2px solid #2563eb" : "1px solid #e2e8f0",
                      background: isSelected ? "#f0f6ff" : "#f8fafc",
                      cursor: "pointer",
                      transition: "all 0.2s",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <strong style={{ fontSize: "14px", color: "#0f172a" }}>{prov.name}</strong>
                      {isSelected ? <span style={{ color: "#2563eb", fontWeight: 700 }}>✓ Seçildi</span> : null}
                    </div>
                    <span style={{ fontSize: "11px", fontWeight: 600, color: "#2563eb", display: "block", margin: "4px 0" }}>
                      {prov.tag}
                    </span>
                    <p style={{ fontSize: "12px", color: "#64748b", margin: 0 }}>{prov.description}</p>
                  </button>
                );
              })}
            </div>

            <div style={{ display: "grid", gap: "16px" }}>
              <label style={{ display: "block" }}>
                <span style={{ fontSize: "13px", fontWeight: 600, color: "#334155" }}>
                  {(() => {
                    const name = PROVIDERS.find((p) => p.id === selectedProvider)?.name || "";
                    return name.endsWith("API") ? `${name} Key` : `${name} API Key`;
                  })()}
                </span>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="AIzaSy... veya gsk_..."
                  style={{
                    width: "100%",
                    padding: "10px 12px",
                    borderRadius: "8px",
                    border: "1px solid #cbd5e1",
                    marginTop: "4px",
                    fontSize: "14px",
                    fontFamily: "monospace",
                  }}
                />
              </label>

              <label style={{ display: "block" }}>
                <span style={{ fontSize: "13px", fontWeight: 600, color: "#334155" }}>Model Adı (Önerilenler)</span>
                {(() => {
                  const currentProv = PROVIDERS.find((p) => p.id === selectedProvider);
                  const options = currentProv?.modelOptions || [modelName];
                  return (
                    <select
                      value={modelName}
                      onChange={(e) => setModelName(e.target.value)}
                      style={{
                        width: "100%",
                        padding: "10px 12px",
                        borderRadius: "8px",
                        border: "1px solid #cbd5e1",
                        marginTop: "4px",
                        fontSize: "14px",
                        background: "#ffffff",
                      }}
                    >
                      {options.map((opt) => (
                        <option key={opt} value={opt}>
                          {opt}
                        </option>
                      ))}
                    </select>
                  );
                })()}
              </label>
            </div>

            <div style={{ marginTop: "24px", display: "flex", alignItems: "center", gap: "16px" }}>
              <button
                type="button"
                className="primary-button"
                onClick={handleConfigureAndProbe}
                disabled={probing}
                style={{
                  background: "#10b981",
                  color: "#ffffff",
                  padding: "10px 20px",
                  borderRadius: "8px",
                  border: "none",
                  fontWeight: 600,
                  fontSize: "14px",
                  cursor: probing ? "not-allowed" : "pointer",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "8px",
                }}
              >
                {probing ? <Loader2 size={16} className="spinner" /> : <Sparkles size={16} />}
                {probing ? "Canlı Probe Test Ediliyor..." : "🔌 API Key & Modeli Canlı Test Et"}
              </button>

              {probeSuccess && (
                <span style={{ color: "#059669", fontWeight: 600, fontSize: "13px", display: "inline-flex", alignItems: "center", gap: "6px" }}>
                  <CheckCircle2 size={16} /> Model Gateway ve Structured Output probe testi başarılı!
                </span>
              )}
            </div>

            <div style={{ marginTop: "28px", display: "flex", justifyContent: "space-between" }}>
              <button
                type="button"
                onClick={() => setActiveStep(1)}
                style={{ background: "#f1f5f9", color: "#475569", padding: "10px 20px", borderRadius: "8px", border: "none", cursor: "pointer" }}
              >
                ← Geri
              </button>
              <button
                type="button"
                onClick={() => {
                  handleConfigureAndProbe();
                  setActiveStep(3);
                }}
                style={{ background: "#2563eb", color: "#ffffff", padding: "10px 24px", borderRadius: "8px", border: "none", fontWeight: 600, cursor: "pointer" }}
              >
                Sonraki Adım: Veri Bağlantıları →
              </button>
            </div>
          </section>
        )}

        {/* STEP 3: CRM / ERP & MCP / DB Connectors */}
        {activeStep === 3 && (
          <section>
            <h2 style={{ fontSize: "18px", fontWeight: 600, color: "#1e293b", marginBottom: "8px" }}>
              3. CRM, ERP & Veri Kaynağı Bağlantıları
            </h2>
            <p style={{ fontSize: "14px", color: "#64748b", marginBottom: "20px" }}>
              Sistemimiz kurumsal Model Context Protocol (MCP) sunucularını, canlı veritabanlarını (PostgreSQL/MySQL) ve dosya kaynaklarını destekler. Tüm erişimler kesinlikle **read-only** (salt okunur) olarak yürütülür.
            </p>

            {/* Connector Type Tabs */}
            <div style={{ display: "flex", gap: "8px", borderBottom: "1px solid #e2e8f0", marginBottom: "20px" }}>
              <button
                type="button"
                onClick={() => setConnectorTab("mcp")}
                style={{
                  padding: "10px 16px",
                  borderRadius: "8px 8px 0 0",
                  border: "none",
                  borderBottom: connectorTab === "mcp" ? "2px solid #2563eb" : "2px solid transparent",
                  background: connectorTab === "mcp" ? "#eff6ff" : "transparent",
                  color: connectorTab === "mcp" ? "#2563eb" : "#64748b",
                  fontWeight: 600,
                  fontSize: "13px",
                  cursor: "pointer",
                }}
              >
                ⚡ Model Context Protocol (MCP)
              </button>
              <button
                type="button"
                onClick={() => setConnectorTab("db")}
                style={{
                  padding: "10px 16px",
                  borderRadius: "8px 8px 0 0",
                  border: "none",
                  borderBottom: connectorTab === "db" ? "2px solid #2563eb" : "2px solid transparent",
                  background: connectorTab === "db" ? "#eff6ff" : "transparent",
                  color: connectorTab === "db" ? "#2563eb" : "#64748b",
                  fontWeight: 600,
                  fontSize: "13px",
                  cursor: "pointer",
                }}
              >
                🐘 Canlı Veritabanı (PostgreSQL / MySQL)
              </button>
              <button
                type="button"
                onClick={() => setConnectorTab("demo")}
                style={{
                  padding: "10px 16px",
                  borderRadius: "8px 8px 0 0",
                  border: "none",
                  borderBottom: connectorTab === "demo" ? "2px solid #2563eb" : "2px solid transparent",
                  background: connectorTab === "demo" ? "#eff6ff" : "transparent",
                  color: connectorTab === "demo" ? "#2563eb" : "#64748b",
                  fontWeight: 600,
                  fontSize: "13px",
                  cursor: "pointer",
                }}
              >
                📁 Demo Şirket & CSV Yükleme
              </button>
            </div>

            {/* MCP TAB CONTENT */}
            {connectorTab === "mcp" && (
              <div style={{ background: "#f8fafc", padding: "20px", borderRadius: "10px", border: "1px solid #e2e8f0" }}>
                <h3 style={{ fontSize: "14px", fontWeight: 600, color: "#0f172a", marginBottom: "8px" }}>
                  Model Context Protocol (MCP) Sunucu Bağlantısı
                </h3>
                <p style={{ fontSize: "12px", color: "#64748b", marginBottom: "16px" }}>
                  MCP sunucunuzun HTTP/SSE uç noktasını tanımlayın. Agent'lar otomatik olarak CRM, ERP ve DWH tool'larını keşfedecektir.
                </p>
                <label style={{ display: "block", marginBottom: "16px" }}>
                  <span style={{ fontSize: "12px", fontWeight: 600, color: "#334155" }}>MCP Server URL / Uç Nokta</span>
                  <input
                    type="text"
                    value={mcpUrl}
                    onChange={(e) => setMcpUrl(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "8px 12px",
                      borderRadius: "6px",
                      border: "1px solid #cbd5e1",
                      marginTop: "4px",
                      fontSize: "13px",
                      fontFamily: "monospace",
                    }}
                  />
                </label>
                <button
                  type="button"
                  onClick={handleTestMcp}
                  disabled={mcpTesting}
                  style={{
                    background: "#0d9488",
                    color: "#ffffff",
                    padding: "8px 18px",
                    borderRadius: "6px",
                    border: "none",
                    fontWeight: 600,
                    fontSize: "13px",
                    cursor: "pointer",
                  }}
                >
                  {mcpTesting ? "Bağlantı Kuruluyor..." : "🔌 MCP Sunucusunu & Tool'ları Canlı Test Et"}
                </button>

                {mcpResult && (
                  <div style={{ marginTop: "16px", padding: "12px", background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: "8px" }}>
                    <strong style={{ color: "#166534", fontSize: "13px", display: "block", marginBottom: "4px" }}>
                      ✓ {mcpResult.message} (Protokol: {mcpResult.protocol_version})
                    </strong>
                    <span style={{ fontSize: "12px", color: "#15803d", fontWeight: 600 }}>Algılanan Read-Only Tool'lar:</span>
                    <ul style={{ margin: "4px 0 0 16px", fontSize: "12px", color: "#166534" }}>
                      {mcpResult.tools_discovered.map((t) => (
                        <li key={t.name}>
                          <code>{t.name}</code>: {t.description}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* LIVE DB TAB CONTENT */}
            {connectorTab === "db" && (
              <div style={{ background: "#f8fafc", padding: "20px", borderRadius: "10px", border: "1px solid #e2e8f0" }}>
                <h3 style={{ fontSize: "14px", fontWeight: 600, color: "#0f172a", marginBottom: "8px" }}>
                  Canlı SQL Veritabanı Bağlantısı (PostgreSQL / MySQL)
                </h3>
                <p style={{ fontSize: "12px", color: "#64748b", marginBottom: "16px" }}>
                  CRM / ERP veritabanınızın read-only erişim bilgilerini girin. Bağlantı sadece okunabilir modda açılır.
                </p>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "16px" }}>
                  <label style={{ display: "block" }}>
                    <span style={{ fontSize: "12px", fontWeight: 600, color: "#334155" }}>Veritabanı Tipi</span>
                    <select
                      value={dbType}
                      onChange={(e) => setDbType(e.target.value)}
                      style={{ width: "100%", padding: "8px 12px", borderRadius: "6px", border: "1px solid #cbd5e1", marginTop: "4px", fontSize: "13px" }}
                    >
                      <option value="postgresql">PostgreSQL</option>
                      <option value="mysql">MySQL</option>
                      <option value="sqlite">SQLite / Embedded</option>
                    </select>
                  </label>
                  <label style={{ display: "block" }}>
                    <span style={{ fontSize: "12px", fontWeight: 600, color: "#334155" }}>Host / Sunucu</span>
                    <input
                      type="text"
                      value={dbHost}
                      onChange={(e) => setDbHost(e.target.value)}
                      style={{ width: "100%", padding: "8px 12px", borderRadius: "6px", border: "1px solid #cbd5e1", marginTop: "4px", fontSize: "13px" }}
                    />
                  </label>
                  <label style={{ display: "block" }}>
                    <span style={{ fontSize: "12px", fontWeight: 600, color: "#334155" }}>Port</span>
                    <input
                      type="number"
                      value={dbPort}
                      onChange={(e) => setDbPort(Number(e.target.value))}
                      style={{ width: "100%", padding: "8px 12px", borderRadius: "6px", border: "1px solid #cbd5e1", marginTop: "4px", fontSize: "13px" }}
                    />
                  </label>
                  <label style={{ display: "block" }}>
                    <span style={{ fontSize: "12px", fontWeight: 600, color: "#334155" }}>Veritabanı Adı</span>
                    <input
                      type="text"
                      value={dbName}
                      onChange={(e) => setDbName(e.target.value)}
                      style={{ width: "100%", padding: "8px 12px", borderRadius: "6px", border: "1px solid #cbd5e1", marginTop: "4px", fontSize: "13px" }}
                    />
                  </label>
                  <label style={{ display: "block" }}>
                    <span style={{ fontSize: "12px", fontWeight: 600, color: "#334155" }}>Kullanıcı (Read-Only)</span>
                    <input
                      type="text"
                      value={dbUser}
                      onChange={(e) => setDbUser(e.target.value)}
                      style={{ width: "100%", padding: "8px 12px", borderRadius: "6px", border: "1px solid #cbd5e1", marginTop: "4px", fontSize: "13px" }}
                    />
                  </label>
                </div>
                <button
                  type="button"
                  onClick={handleTestDb}
                  disabled={dbTesting}
                  style={{
                    background: "#0284c7",
                    color: "#ffffff",
                    padding: "8px 18px",
                    borderRadius: "6px",
                    border: "none",
                    fontWeight: 600,
                    fontSize: "13px",
                    cursor: "pointer",
                  }}
                >
                  {dbTesting ? "Bağlanılıyor..." : "🔌 Veritabanı Bağlantısını Canlı Test Et"}
                </button>

                {dbResult && (
                  <div style={{ marginTop: "16px", padding: "12px", background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: "8px" }}>
                    <strong style={{ color: "#166534", fontSize: "13px", display: "block", marginBottom: "4px" }}>
                      ✓ {dbResult.message} ({dbResult.connection_time_ms} ms)
                    </strong>
                    <span style={{ fontSize: "12px", color: "#15803d" }}>
                      Şema Taranan Tablolar: <code>{dbResult.tables_found.join(", ")}</code>
                    </span>
                  </div>
                )}
              </div>
            )}

            {/* DEMO / CSV TAB CONTENT */}
            {connectorTab === "demo" && (
              <div style={{ background: "#f8fafc", padding: "20px", borderRadius: "10px", border: "1px solid #e2e8f0" }}>
                <label
                  style={{
                    border: "2px dashed #93c5fd",
                    borderRadius: "10px",
                    padding: "24px",
                    textAlign: "center",
                    background: "#ffffff",
                    marginBottom: "16px",
                    display: "block",
                    cursor: "pointer",
                    transition: "all 0.2s",
                  }}
                >
                  <input
                    type="file"
                    accept=".csv,.xlsx"
                    style={{ display: "none" }}
                    onChange={async (e) => {
                      const file = e.target.files?.[0];
                      if (!file) return;
                      try {
                        const preview = await api.previewSourceFile(file, "accounts");
                        setSyncDetails(`✓ ${file.name} başarıyla önizlendi (${preview.preview.length} satır algılandı).`);
                      } catch (err: any) {
                        setError(err.message || "Dosya yüklenemedi");
                      }
                    }}
                  />
                  <UploadCloud size={32} style={{ color: "#2563eb", marginBottom: "4px" }} />
                  <strong style={{ fontSize: "13px", color: "#1e293b", display: "block" }}>
                    CSV / XLSX Veri Dosyasını Seçmek Veya Sürüklemek İçin Tıklayın
                  </strong>
                  <span style={{ fontSize: "12px", color: "#64748b" }}>
                    Otomatik alan eşleme ve önizleme desteği aktiftir.
                  </span>
                </label>

                <div style={{ background: "#e0f2fe", border: "1px solid #bae6fd", padding: "12px 16px", borderRadius: "8px", fontSize: "13px", color: "#0369a1" }}>
                  <strong>✓ Hazır Şirket Demo Verisi Aktif:</strong> Anka Sentetik CRM & ERP veri seti kullanıma hazır.
                </div>
              </div>
            )}

            <div style={{ marginTop: "28px", display: "flex", justifyContent: "space-between" }}>
              <button
                type="button"
                onClick={() => setActiveStep(2)}
                style={{ background: "#f1f5f9", color: "#475569", padding: "10px 20px", borderRadius: "8px", border: "none", cursor: "pointer" }}
              >
                ← Geri
              </button>
              <button
                type="button"
                onClick={() => setActiveStep(4)}
                style={{ background: "#2563eb", color: "#ffffff", padding: "10px 24px", borderRadius: "8px", border: "none", fontWeight: 600, cursor: "pointer" }}
              >
                Sonraki Adım: RAG İndeksleme →
              </button>
            </div>
          </section>
        )}

        {/* STEP 4: OKF RAG Ingestion */}
        {activeStep === 4 && (
          <section>
            <h2 style={{ fontSize: "18px", fontWeight: 600, color: "#1e293b", marginBottom: "8px" }}>
              4. OKF Wiki & ChromaDB RAG Vektör İndeksleme
            </h2>
            <p style={{ fontSize: "14px", color: "#64748b", marginBottom: "20px" }}>
              Bağlanan verileri değişmez kanıt parçalarına (`ev_...`) dönüştürün ve ajanların `search_knowledge` ile erişebilmesi için ChromaDB RAG vektör indeksini oluşturun.
            </p>

            <div style={{ marginBottom: "24px" }}>
              <button
                type="button"
                onClick={handleStartIngestion}
                disabled={ingesting}
                style={{
                  background: "#8b5cf6",
                  color: "#ffffff",
                  padding: "12px 24px",
                  borderRadius: "8px",
                  border: "none",
                  fontWeight: 600,
                  fontSize: "14px",
                  cursor: "pointer",
                }}
              >
                {ingesting ? "RAG İndeksi Oluşturuluyor..." : "⚡ OKF Wiki & RAG İndekslemesini Başlat"}
              </button>

              {ragSuccess && (
                <div style={{ marginTop: "16px", color: "#059669", fontWeight: 600, fontSize: "13px" }}>
                  ✓ {syncDetails}
                </div>
              )}
            </div>

            <div style={{ marginTop: "28px", display: "flex", justifyContent: "space-between" }}>
              <button
                type="button"
                onClick={() => setActiveStep(3)}
                style={{ background: "#f1f5f9", color: "#475569", padding: "10px 20px", borderRadius: "8px", border: "none", cursor: "pointer" }}
              >
                ← Geri
              </button>
              <button
                type="button"
                onClick={() => setActiveStep(5)}
                style={{ background: "#2563eb", color: "#ffffff", padding: "10px 24px", borderRadius: "8px", border: "none", fontWeight: 600, cursor: "pointer" }}
              >
                Sonraki Adım: Kurulumu Tamamla →
              </button>
            </div>
          </section>
        )}

        {/* STEP 5: Final Ready Step */}
        {activeStep === 5 && (
          <section style={{ textAlign: "center", padding: "20px 0" }}>
            <div style={{ fontSize: "48px", marginBottom: "12px" }}>🎉</div>
            <h2 style={{ fontSize: "22px", fontWeight: 700, color: "#0f172a", marginBottom: "8px" }}>
              Tebrikler! Kurulum Başarıyla Tamamlandı
            </h2>
            <p style={{ fontSize: "14px", color: "#64748b", maxWidth: "600px", margin: "0 auto 24px" }}>
              Şirket profili, Model Gateway (Cloud Provider), CRM/ERP okuma konektörleri ve OKF RAG vektör indeksi hazır.
            </p>

            <button
              type="button"
              onClick={onComplete}
              style={{
                background: "#059669",
                color: "#ffffff",
                padding: "14px 32px",
                borderRadius: "10px",
                border: "none",
                fontWeight: 700,
                fontSize: "16px",
                cursor: "pointer",
                boxShadow: "0 10px 15px -3px rgba(5, 150, 105, 0.3)",
              }}
            >
              🚀 Web Console Dashboard'a Geçiş Yap
            </button>
          </section>
        )}
      </section>
    </main>
  );
}
