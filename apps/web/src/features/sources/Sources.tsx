import { AlertTriangle, CheckCircle2, Database, FileSpreadsheet, RefreshCw, Upload } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { api, ApiError } from "../../api";
import type { DataSourceView, FilePreview, SourceSyncRunView } from "../../types";

function canonicalField(value: string, index: number): string {
  const normalized = value
    .trim()
    .toLocaleLowerCase("tr-TR")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9_]+/g, "_")
    .replace(/^_+|_+$/g, "");
  return /^[a-z][a-z0-9_]*$/.test(normalized) ? normalized : `field_${index + 1}`;
}

export function Sources() {
  const [sources, setSources] = useState<DataSourceView[]>([]);
  const [runs, setRuns] = useState<SourceSyncRunView[]>([]);
  const [preview, setPreview] = useState<FilePreview | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [entityType, setEntityType] = useState("accounts");
  const [idField, setIdField] = useState("");
  const [classification, setClassification] = useState("internal");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    const [sourceResponse, runResponse] = await Promise.all([
      api.sources(),
      api.sourceSyncRuns(),
    ]);
    setSources(sourceResponse.items);
    setRuns(runResponse.items);
  }, []);

  useEffect(() => {
    refresh().catch((caught) => {
      setError(caught instanceof ApiError ? caught.message : "Kaynaklar yüklenemedi");
    });
  }, [refresh]);

  const columns = useMemo(
    () => preview?.schema.entities[entityType] ?? [],
    [entityType, preview],
  );

  async function uploadAndPreview(event: React.FormEvent) {
    event.preventDefault();
    if (!file) return;
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const result = await api.previewSourceFile(file, entityType);
      const discovered = result.schema.entities[entityType] ?? [];
      setPreview(result);
      setIdField(discovered.find((column) => column.toLowerCase() === "id") ?? discovered[0] ?? "");
      setMessage("Dosya read-only olarak doğrulandı. Mapping onayınızı bekliyor.");
      await refresh();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Dosya önizlenemedi");
    } finally {
      setBusy(false);
    }
  }

  async function mapAndSync() {
    if (!preview || !idField) return;
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const mapping: Record<string, string> = { id: idField };
      columns.forEach((column, index) => {
        if (column !== idField) mapping[canonicalField(column, index)] = column;
      });
      await api.mapSource(preview.source_id, {
        entity_type: entityType,
        field_mapping: mapping,
        classification,
      });
      const result = await api.syncSource(preview.source_id);
      setMessage(`${result.total_records} kayıt immutable snapshot ve evidence katmanına yazıldı.`);
      setPreview(null);
      setFile(null);
      await refresh();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Mapping veya sync tamamlanamadı");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="page sources-page">
      <header className="page-heading">
        <div>
          <p className="eyebrow">READ-ONLY INGESTION</p>
          <h1>Veri Kaynakları</h1>
          <p>CSV/XLSX verisini önce doğrulayın, sonra canonical context ve evidence katmanına alın.</p>
        </div>
        <button className="secondary-button" type="button" onClick={() => refresh()} disabled={busy}>
          <RefreshCw size={15} /> Yenile
        </button>
      </header>

      {error ? <div className="inline-alert inline-alert--error" role="alert"><AlertTriangle size={17} />{error}</div> : null}
      {message ? <div className="inline-alert inline-alert--success" role="status"><CheckCircle2 size={17} />{message}</div> : null}

      <section className="source-workspace">
        <form className="source-upload-card" onSubmit={uploadAndPreview}>
          <FileSpreadsheet size={28} />
          <div>
            <h2>Dosya kaynağı ekle</h2>
            <p>En fazla 25 MB. Formül benzeri hücreler uyarı olarak işaretlenir; hiçbir dış sisteme yazılmaz.</p>
          </div>
          <label>
            Entity type
            <input value={entityType} onChange={(event) => setEntityType(event.target.value)} pattern="[a-z][a-z0-9_]*" required />
          </label>
          <label className="file-picker">
            <Upload size={16} />
            <span>{file?.name ?? "CSV veya XLSX seçin"}</span>
            <input type="file" accept=".csv,.xlsx" onChange={(event) => setFile(event.target.files?.[0] ?? null)} required />
          </label>
          <button className="primary-button" type="submit" disabled={!file || busy}>{busy ? "Kontrol ediliyor…" : "Yükle ve önizle"}</button>
        </form>

        {preview ? (
          <section className="mapping-card" aria-label="Kaynak mapping">
            <header><div><small>MAPPING REQUIRED</small><h2>{preview.filename}</h2></div><span>{columns.length} alan · {preview.preview.length} önizleme satırı</span></header>
            <div className="mapping-controls">
              <label>Canonical ID alanı<select value={idField} onChange={(event) => setIdField(event.target.value)}>{columns.map((column) => <option key={column}>{column}</option>)}</select></label>
              <label>Veri sınıfı<select value={classification} onChange={(event) => setClassification(event.target.value)}><option value="internal">Internal</option><option value="confidential">Confidential</option><option value="restricted">Restricted</option><option value="public">Public</option></select></label>
            </div>
            {preview.warnings.length ? <div className="mapping-warning"><AlertTriangle size={14} />{preview.warnings.length} formula benzeri hücre bulundu; değerler untrusted data olarak tutulacak.</div> : null}
            <div className="preview-table" tabIndex={0}>
              <table><thead><tr>{columns.slice(0, 6).map((column) => <th key={column}>{column}</th>)}</tr></thead><tbody>{preview.preview.slice(0, 5).map((record) => <tr key={record.external_id}>{columns.slice(0, 6).map((column) => <td key={column}>{String(record.data[column] ?? "—")}</td>)}</tr>)}</tbody></table>
            </div>
            <button className="primary-button" type="button" disabled={!idField || busy} onClick={mapAndSync}>Mapping’i kaydet ve sync et</button>
          </section>
        ) : null}
      </section>

      <section className="source-inventory">
        <header><h2>Bağlı kaynaklar</h2><span>{sources.length} kaynak</span></header>
        {sources.length ? sources.map((source) => {
          const latestRun = runs.find((run) => run.source_id === source.id);
          return <article key={source.id}><Database size={19} /><div><strong>{source.name}</strong><small>{source.id} · {source.connector_type}</small></div><span className={`source-status source-status--${source.status}`}>{source.status}</span><div className="source-run"><strong>{latestRun?.records_persisted ?? 0}</strong><small>persisted records</small></div></article>;
        }) : <div className="empty-panel">Henüz kaynak yok. Demo sihirbazını çalıştırabilir veya bir dosya yükleyebilirsiniz.</div>}
      </section>
    </main>
  );
}
