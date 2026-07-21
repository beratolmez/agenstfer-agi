import { useEffect, useState } from "react";
import { api } from "../../api";
import { TriggerEventView, TriggerRuleView } from "../../types";

export function EventPanel() {
  const [rules, setRules] = useState<TriggerRuleView[]>([]);
  const [events, setEvents] = useState<TriggerEventView[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Webhook Test Form
  const [sourceId, setSourceId] = useState("src-crm-001");
  const [eventType, setEventType] = useState("inbound.form_submitted");
  const [payloadJson, setPayloadJson] = useState(
    JSON.stringify({ lead_name: "Anka Teknoloji A.Ş.", contact: "info@anka.com", intent_score: 85 }, null, 2)
  );
  const [sending, setSending] = useState(false);
  const [sendResult, setSendResult] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [r, e] = await Promise.all([api.triggerRules(), api.triggerEvents()]);
      setRules(r.items);
      setEvents(e.items);
      setLoading(false);
    } catch (err: any) {
      setError(err.message || "Tetikleyici kuralları ve olaylar yüklenemedi");
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSendWebhook = async () => {
    setError(null);
    setSendResult(null);
    setSending(true);

    try {
      const dataObj = JSON.parse(payloadJson);
      const res = await api.sendWebhookPayload(sourceId, {
        event_type: eventType,
        data: dataObj,
      });

      setSendResult(
        `✅ Event ${res.event_id} alındı. Durum: ${res.status}. ${res.matched_rules_count} kural eşleşti. Otomatik Başlatılan Akışlar: ${
          res.triggered_workflows.join(", ") || "Yok"
        }`
      );
      loadData();
    } catch (err: any) {
      setError(err.message || "Webhook gönderimi başarısız. Geçerli bir JSON girin.");
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return (
      <main className="dashboard">
        <section className="card" style={{ padding: "32px", textAlign: "center" }}>
          <h2>Olaylar ve Webhook Yükleniyor...</h2>
        </section>
      </main>
    );
  }

  return (
    <main className="dashboard" style={{ gap: "24px", display: "flex", flexDirection: "column" }}>
      <header className="page-header" style={{ marginBottom: 0 }}>
        <div>
          <h1 style={{ fontSize: "24px", fontWeight: 700, color: "#0f172a" }}>Olaylar & Webhook Yönetim Paneli</h1>
          <p style={{ fontSize: "14px", color: "#64748b", margin: "4px 0 0" }}>
            CRM/ERP güncellemeleri, inbound formlar veya webhook yükleri ile büyüme akışlarını otomatik çalıştırın.
          </p>
        </div>
      </header>

      {error && (
        <div role="alert" style={{ background: "#fef2f2", border: "1px solid #fecaca", color: "#b91c1c", padding: "12px", borderRadius: "8px", fontSize: "13px" }}>
          ⚠️ {error}
        </div>
      )}

      {/* Webhook Tester Section */}
      <section className="card" style={{ padding: "24px", background: "#ffffff", borderRadius: "12px", border: "1px solid #e2e8f0" }}>
        <h2 style={{ fontSize: "16px", fontWeight: 600, color: "#1e293b", marginBottom: "16px" }}>⚡ Canlı Webhook Yükü Testi (Ingestion Probe)</h2>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "16px" }}>
          <label style={{ display: "block" }}>
            <span style={{ fontSize: "13px", fontWeight: 600, color: "#334155" }}>Kaynak Kimliği (Source ID)</span>
            <input
              type="text"
              value={sourceId}
              onChange={(e) => setSourceId(e.target.value)}
              style={{ width: "100%", padding: "8px 12px", borderRadius: "6px", border: "1px solid #cbd5e1", marginTop: "4px", fontSize: "13px" }}
            />
          </label>

          <label style={{ display: "block" }}>
            <span style={{ fontSize: "13px", fontWeight: 600, color: "#334155" }}>Olay Türü (Event Type)</span>
            <select
              value={eventType}
              onChange={(e) => setEventType(e.target.value)}
              style={{ width: "100%", padding: "8px 12px", borderRadius: "6px", border: "1px solid #cbd5e1", marginTop: "4px", fontSize: "13px" }}
            >
              <option value="inbound.form_submitted">inbound.form_submitted (Intent Triage Workflow)</option>
              <option value="crm.account_updated">crm.account_updated (Data Hygiene Workflow)</option>
              <option value="competitor.signal_detected">competitor.signal_detected (Battlecard Workflow)</option>
              <option value="lead.opportunity_detected">lead.opportunity_detected (Lead Discovery Workflow)</option>
            </select>
          </label>
        </div>

        <label style={{ display: "block", marginBottom: "16px" }}>
          <span style={{ fontSize: "13px", fontWeight: 600, color: "#334155" }}>JSON Webhook Payload Data</span>
          <textarea
            rows={4}
            value={payloadJson}
            onChange={(e) => setPayloadJson(e.target.value)}
            style={{ width: "100%", padding: "10px", borderRadius: "6px", border: "1px solid #cbd5e1", marginTop: "4px", fontFamily: "monospace", fontSize: "12px" }}
          />
        </label>

        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <button
            type="button"
            className="primary-button"
            onClick={handleSendWebhook}
            disabled={sending}
            style={{ background: "#2563eb", color: "#ffffff", padding: "10px 20px", borderRadius: "8px", border: "none", fontWeight: 600, cursor: "pointer" }}
          >
            {sending ? "Webhook Gönderiliyor..." : "⚡ Webhook Yükü Gönder (POST /api/webhooks)"}
          </button>
          {sendResult && <span style={{ fontSize: "13px", fontWeight: 600, color: "#059669" }}>{sendResult}</span>}
        </div>
      </section>

      {/* Trigger Rules Grid */}
      <section className="card" style={{ padding: "24px", background: "#ffffff", borderRadius: "12px", border: "1px solid #e2e8f0" }}>
        <h2 style={{ fontSize: "16px", fontWeight: 600, color: "#1e293b", marginBottom: "16px" }}>📋 Tanımlı Tetikleyici Kuralları (Trigger Rule Registry)</h2>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
          {rules.map((rule) => (
            <div key={rule.id} style={{ padding: "16px", borderRadius: "8px", border: "1px solid #e2e8f0", background: "#f8fafc" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                <strong style={{ fontSize: "14px", color: "#0f172a" }}>{rule.name}</strong>
                <span style={{ fontSize: "11px", fontWeight: 600, padding: "2px 8px", borderRadius: "12px", background: rule.enabled ? "#dcfce7" : "#fee2e2", color: rule.enabled ? "#15803d" : "#b91c1c" }}>
                  {rule.enabled ? "Aktif Kural" : "Devre Dışı"}
                </span>
              </div>
              <p style={{ fontSize: "12px", color: "#64748b", margin: "4px 0 8px" }}>{rule.description}</p>
              <div style={{ fontSize: "11px", fontFamily: "monospace", color: "#2563eb", background: "#eff6ff", padding: "4px 8px", borderRadius: "4px" }}>
                Event: {rule.event_type} → Workflow: {rule.target_workflow_id}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Received Event Logs */}
      <section className="card" style={{ padding: "24px", background: "#ffffff", borderRadius: "12px", border: "1px solid #e2e8f0" }}>
        <h2 style={{ fontSize: "16px", fontWeight: 600, color: "#1e293b", marginBottom: "16px" }}>📜 Gelen Canlı Olay Günlüğü (Event Audit Stream)</h2>
        {events.length === 0 ? (
          <p style={{ fontSize: "13px", color: "#64748b" }}>Henüz bir olay tetiklenmedi. Yukarıdaki test panelinden webhook gönderin.</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {events.map((evt) => (
              <div key={evt.id} style={{ padding: "14px", borderRadius: "8px", border: "1px solid #e2e8f0", background: "#ffffff" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <span style={{ fontSize: "12px", fontWeight: 700, color: "#0f172a" }}>{evt.id}</span>
                    <span style={{ marginLeft: "12px", fontSize: "12px", color: "#64748b" }}>Kaynak: {evt.source_id}</span>
                    <span style={{ marginLeft: "12px", fontSize: "12px", fontWeight: 600, color: "#2563eb" }}>Tür: {evt.event_type}</span>
                  </div>
                  <span style={{ fontSize: "11px", padding: "2px 8px", borderRadius: "10px", background: evt.status === "triggered" ? "#dcfce7" : "#f1f5f9", color: evt.status === "triggered" ? "#15803d" : "#475569" }}>
                    {evt.status === "triggered" ? "⚡ Workflow Tetiklendi" : "Eşleşme Yok"}
                  </span>
                </div>
                <pre style={{ margin: "8px 0 0", padding: "8px", background: "#0f172a", color: "#38bdf8", borderRadius: "6px", fontSize: "11px", overflowX: "auto" }}>
                  {JSON.stringify(evt.payload, null, 2)}
                </pre>
              </div>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
