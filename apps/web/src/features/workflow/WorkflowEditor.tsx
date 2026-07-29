import {
  Bot,
  Box,
  CalendarClock,
  Check,
  ChevronDown,
  CirclePlay,
  Copy,
  Database,
  FileOutput,
  FileSearch,
  FolderOpen,
  GitBranch,
  GripVertical,
  History,
  Play,
  Plus,
  Search,
  Save,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Trash2,
  Upload,
  X,
} from "lucide-react";
import {
  addEdge,
  Background,
  Controls,
  Handle,
  MarkerType,
  Position,
  ReactFlow,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
  useReactFlow,
  type Connection,
  type Edge,
  type Node,
  type NodeProps,
} from "@xyflow/react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../../api";
import type {
  AgentDefinitionView,
  CapabilityDefinitionView,
  ModelProfileView,
  WorkflowDefinition,
  WorkflowScheduleView,
  WorkflowSummary,
} from "../../types";

type Tone = "green" | "blue" | "violet" | "amber";
interface WorkflowNodeData extends Record<string, unknown> {
  label: string;
  kind: string;
  subtitle: string;
  tone: Tone;
  config: Record<string, unknown>;
  outputType: string;
}
type FlowNode = Node<WorkflowNodeData, "workflowNode">;

const nodeInfo: Record<string, { label: string; group: string; subtitle: string; tone: Tone; icon: typeof Database; output: string; config?: Record<string, unknown> }> = {
  manual_trigger: { label: "Manual Trigger", group: "Trigger", subtitle: "Elle tetikleme", tone: "green", icon: Play, output: "control" },
  data_source_sync: { label: "Data Source Sync", group: "Veri", subtitle: "CRM & DWH senkronizasyonu", tone: "blue", icon: Database, output: "raw_records", config: { connector_id: "demo-company" } },
  normalize_context: { label: "Normalize Context", group: "Veri", subtitle: "Bağlam normalizasyonu", tone: "blue", icon: SlidersHorizontal, output: "context" },
  okf_compile: { label: "OKF Compile", group: "AI ve Analiz", subtitle: "Hedef & OKF derle", tone: "violet", icon: Box, output: "knowledge" },
  knowledge_search: { label: "Knowledge Search", group: "AI ve Analiz", subtitle: "Bilgi bankası araması", tone: "violet", icon: FileSearch, output: "evidence", config: { query: "growth evidence" } },
  agent_run: { label: "Agent Run", group: "AI ve Analiz", subtitle: "Analiz ajanı çalıştır", tone: "violet", icon: Bot, output: "agent_result", config: { agent_id: "company-analyst", model_profile: "local-balanced", output_type: "CompanyAnalysis" } },
  deterministic_score: { label: "Deterministic Score", group: "AI ve Analiz", subtitle: "Skor hesaplama", tone: "violet", icon: Sparkles, output: "scored_opportunities" },
  condition: { label: "Condition", group: "Kontrol", subtitle: "Eşik kontrolü", tone: "amber", icon: GitBranch, output: "control", config: { field: "scores.energy-retrofit", operator: "gte", value: 60 } },
  policy_check: { label: "Policy Check", group: "Kontrol", subtitle: "Politika kontrolü", tone: "amber", icon: ShieldCheck, output: "control", config: { policy_id: "material-claim-evidence" } },
  approval: { label: "Approval", group: "Kontrol", subtitle: "Onay gerektirir", tone: "amber", icon: Check, output: "approved", config: { role: "approver", timeout_days: 7 } },
  report_output: { label: "Report Output", group: "Çıktı", subtitle: "Rapor çıktısı", tone: "blue", icon: FileOutput, output: "artifact", config: { format: "okf+html" } },
};

function WorkflowNode({ data, selected }: NodeProps<FlowNode>) {
  const info = nodeInfo[data.kind] ?? nodeInfo.agent_run;
  const Icon = info.icon;
  return (
    <div className={`flow-node flow-node--${data.tone} ${selected ? "is-selected" : ""}`}>
      <Handle type="target" position={Position.Left} />
      <span className="flow-node__icon"><Icon size={16} /></span>
      <span><strong>{data.label}</strong><small>{data.subtitle}</small></span>
      <Check size={13} className="flow-node__valid" />
      {data.kind === "condition" ? (
        <>
          <Handle id="true" type="source" position={Position.Right} style={{ top: "36%" }} />
          <Handle id="false" type="source" position={Position.Right} style={{ top: "70%" }} />
        </>
      ) : <Handle type="source" position={Position.Right} />}
    </div>
  );
}

const nodeTypes = { workflowNode: WorkflowNode };

function toFlow(workflow: WorkflowDefinition): { nodes: FlowNode[]; edges: Edge[] } {
  const nodes: FlowNode[] = workflow.nodes.map((node) => {
    const info = nodeInfo[node.kind] ?? nodeInfo.agent_run;
    return {
      id: node.id,
      type: "workflowNode",
      position: node.position,
      data: {
        label: node.label,
        kind: node.kind,
        subtitle: node.kind === "agent_run" ? String(node.config.agent_id ?? info.subtitle) : info.subtitle,
        tone: node.kind === "approval" ? "amber" : info.tone,
        config: node.config,
        outputType: node.output_type ?? info.output,
      },
    };
  });
  const edges: Edge[] = workflow.edges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    data: { dataType: edge.data_type },
    sourceHandle: edge.branch ?? undefined,
    markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16 },
    style: { stroke: "#637083", strokeWidth: 1.4 },
  }));
  return { nodes, edges };
}

function NodeCatalog() {
  const groups = useMemo(() => ["Trigger", "Veri", "AI ve Analiz", "Kontrol", "Çıktı"], []);
  const [query, setQuery] = useState("");
  return (
    <aside className="node-catalog">
      <h2>Node kataloğu <ChevronDown size={16} /></h2>
      <label><Search size={15} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Ara node…" /></label>
      {groups.map((group) => {
        const entries = Object.entries(nodeInfo).filter(([, info]) => info.group === group && info.label.toLowerCase().includes(query.toLowerCase()));
        return entries.length ? (
          <section key={group}>
            <h3>{group}<ChevronDown size={14} /></h3>
            {entries.map(([kind, info]) => {
              const Icon = info.icon;
              return (
                <div
                  className={`catalog-node catalog-node--${info.tone}`}
                  draggable
                  key={kind}
                  onDragStart={(event) => {
                    event.dataTransfer.setData("application/agi-node", kind);
                    event.dataTransfer.effectAllowed = "move";
                  }}
                >
                  <span><Icon size={15} /></span>{info.label}<GripVertical size={14} />
                </div>
              );
            })}
          </section>
        ) : null;
      })}
    </aside>
  );
}

function Inspector({
  node,
  agents,
  modelProfiles,
  capabilities,
  readOnly,
  onChange,
  onDelete,
}: {
  node: FlowNode | null;
  agents: AgentDefinitionView[];
  modelProfiles: ModelProfileView[];
  capabilities: CapabilityDefinitionView[];
  readOnly: boolean;
  onChange: (node: FlowNode) => void;
  onDelete: () => void;
}) {
  if (!node) return <aside className="node-inspector node-inspector--empty"><SlidersHorizontal size={28} /><h2>Node seçin</h2><p>Konfigürasyonu burada düzenleyebilirsiniz.</p></aside>;
  const currentNode = node;
  const config = currentNode.data.config;
  // Only offer what the registry actually reports. The previous hard-coded fallback listed
  // six capabilities that do nothing and omitted two that work, so a node could be assigned
  // skills that silently never run.
  const availableCapIds = capabilities.map((c) => c.id);
  const plannedCapIds = new Set(
    capabilities.filter((c) => c.definition?.availability === "planned").map((c) => c.id),
  );

  function updateConfig(key: string, value: unknown) {
    onChange({ ...currentNode, data: { ...currentNode.data, config: { ...config, [key]: value } } });
  }
  function updateAgent(agentId: string) {
    const selected = agents.find((agent) => agent.id === agentId);
    onChange({
      ...currentNode,
      data: {
        ...currentNode.data,
        subtitle: selected?.name ?? agentId,
        config: {
          ...config,
          agent_id: agentId,
          agent_version: selected?.version,
          output_type: selected?.output_type ?? config.output_type,
        },
      },
    });
  }
  return (
    <aside className={`node-inspector ${readOnly ? "is-readonly" : ""}`}>
      <header><h2>{node.data.label}</h2><button type="button" aria-label="Inspector kapat"><X size={18} /></button></header>
      <section><h3>Genel</h3><label>ID<input value={node.id} disabled /></label><label>Açıklama<textarea value={node.data.subtitle} onChange={(event) => onChange({ ...node, data: { ...node.data, subtitle: event.target.value } })} /></label></section>
      {node.data.kind === "agent_run" ? (
        <section>
          <h3>Konfigürasyon</h3>
          <label>Agent<select value={String(config.agent_id ?? "company-analyst")} onChange={(event) => updateAgent(event.target.value)}>{agents.map((agent) => <option key={agent.id} value={agent.id}>{agent.name} · v{agent.version}</option>)}</select></label>
          <label>Model profili<select value={String(config.model_profile ?? "local-balanced")} onChange={(event) => updateConfig("model_profile", event.target.value)}>{modelProfiles.map((profile) => <option disabled={!profile.enabled} key={profile.id} value={profile.id}>{profile.id}{profile.available ? " · erişilebilir" : " · erişilebilir değil"}</option>)}</select></label>
          <label>Çıktı tipi<select value={String(config.output_type ?? "CompanyAnalysis")} onChange={(event) => updateConfig("output_type", event.target.value)}><option>CompanyAnalysis</option><option>OpportunityHypotheses</option><option>EvidenceReview</option><option>OKFChangeSet</option></select></label>
          <label style={{ display: "block", marginTop: "8px" }}>
            Atanan Skill'ler (Capabilities)
            <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginTop: "4px" }}>
              {availableCapIds.map((cap) => {
                const currentCaps = Array.isArray(config.capabilities) ? (config.capabilities as string[]) : ["knowledge.search"];
                const active = currentCaps.includes(cap);
                // A planned capability has no handler behind it. Assigning one used to look
                // identical to assigning a working skill and then silently did nothing.
                const planned = plannedCapIds.has(cap);
                return (
                  <button
                    type="button"
                    key={cap}
                    disabled={planned}
                    title={planned ? "Bu skill henüz uygulanmadı; ajana atanamaz." : undefined}
                    onClick={() => {
                      const next = active ? currentCaps.filter((c) => c !== cap) : [...currentCaps, cap];
                      updateConfig("capabilities", next);
                    }}
                    style={{
                      fontSize: "11px",
                      padding: "3px 8px",
                      borderRadius: "4px",
                      border: active ? "1px solid #3b82f6" : "1px solid #cbd5e1",
                      background: active ? "#eff6ff" : "#f8fafc",
                      color: planned ? "#94a3b8" : active ? "#1d4ed8" : "#475569",
                      cursor: planned ? "not-allowed" : "pointer",
                    }}
                  >
                    {planned ? "◦ " : active ? "✓ " : "+ "}{cap}{planned ? " (planlandı)" : ""}
                  </button>
                );
              })}
            </div>
          </label>
        </section>
      ) : null}
      {node.data.kind === "condition" ? (
        <section>
          <h3>Güvenli koşul</h3>
          <label>Alan<input value={String(config.field ?? "")} onChange={(event) => updateConfig("field", event.target.value)} /></label>
          <label>Operatör<select value={String(config.operator ?? "gte")} onChange={(event) => updateConfig("operator", event.target.value)}><option value="eq">eşit</option><option value="ne">eşit değil</option><option value="gt">büyük</option><option value="gte">büyük/eşit</option><option value="lt">küçük</option><option value="lte">küçük/eşit</option><option value="contains">içerir</option></select></label>
          <label>Değer<input value={String(config.value ?? "")} onChange={(event) => updateConfig("value", Number.isNaN(Number(event.target.value)) ? event.target.value : Number(event.target.value))} /></label>
        </section>
      ) : null}
      <div className="inspector-note">Bu node, yalnız registry'de izin verilen capability ve typed output sözleşmesini kullanır.</div>
      <button className="delete-button" disabled={readOnly} type="button" onClick={onDelete}><Trash2 size={16} /> Node'u sil</button>
    </aside>
  );
}

function EditorSurface({ userRoles }: { userRoles: string[] }) {
  const canEdit = userRoles.includes("analyst");
  const isAdmin = userRoles.includes("admin");
  const [workflow, setWorkflow] = useState<WorkflowDefinition | null>(null);
  const [templates, setTemplates] = useState<WorkflowDefinition[]>([]);
  const [templateOpen, setTemplateOpen] = useState(false);
  const [nodes, setNodes, onNodesChange] = useNodesState<FlowNode>([]);

  useEffect(() => {
    api.workflowTemplates().then((res) => setTemplates(res.items)).catch(() => {});
  }, []);

  function loadTemplate(tpl: WorkflowDefinition) {
    loadDefinition(tpl);
    setTemplateOpen(false);
    setSaved(`Şablon yüklendi: ${tpl.name}`);
  }
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [agents, setAgents] = useState<AgentDefinitionView[]>([]);
  const [modelProfiles, setModelProfiles] = useState<ModelProfileView[]>([]);
  const [workflowCatalog, setWorkflowCatalog] = useState<WorkflowSummary[]>([]);
  const [versionHistory, setVersionHistory] = useState<WorkflowDefinition[]>([]);
  const [schedules, setSchedules] = useState<WorkflowScheduleView[]>([]);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [cron, setCron] = useState("0 9 * * 1-5");
  const [timezone, setTimezone] = useState("Europe/Istanbul");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [validation, setValidation] = useState("Geçerli graph");
  const [saved, setSaved] = useState("Yükleniyor…");
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const { screenToFlowPosition, fitView } = useReactFlow();

  const loadDefinition = useCallback((definition: WorkflowDefinition) => {
    const flow = toFlow(definition);
    setWorkflow(definition);
    setNodes(flow.nodes);
    setEdges(flow.edges);
    setSelectedId(null);
    setSaved(definition.status === "published"
      ? `Published v${definition.version} salt okunur`
      : `Taslak v${definition.version} yüklendi`);
    requestAnimationFrame(() => fitView({ padding: 0.2 }));
  }, [fitView, setEdges, setNodes]);

  const refreshMetadata = useCallback(async (workflowId: string) => {
    const [catalog, versions, scheduleResult] = await Promise.all([
      api.workflows(),
      api.workflowVersions(workflowId),
      api.workflowSchedules(),
    ]);
    setWorkflowCatalog(catalog.items);
    setVersionHistory(versions.items);
    setSchedules(scheduleResult.items);
  }, []);

  const [capabilitiesList, setCapabilitiesList] = useState<CapabilityDefinitionView[]>([]);

  useEffect(() => {
    Promise.all([api.workflow(), api.workflows(), api.agents(), api.modelProfiles(), api.capabilities()]).then(async ([definition, catalog, agentResult, profileResult, capResult]) => {
      const latestAgents = agentResult.items.filter((agent, index, items) =>
        agent.status === "published"
        && items.findIndex((candidate) => candidate.id === agent.id && candidate.status === "published") === index,
      );
      setAgents(latestAgents);
      setModelProfiles(profileResult.items);
      setCapabilitiesList(capResult.items);

      const userSummary = catalog.items.find((item) => item.id === "growth-diagnostic");
      let selected = definition;
      if (userSummary) selected = (await api.workflowVersions(userSummary.id)).items[0] ?? definition;
      if (canEdit && selected.status === "published") selected = await api.cloneWorkflow(selected);
      loadDefinition(selected);
      await refreshMetadata(selected.id);
    }).catch((reason: Error) => setActionError(reason.message));
  }, [canEdit, loadDefinition, refreshMetadata]);

  async function openWorkflow(workflowId: string) {
    setBusy(true);
    setActionError(null);
    try {
      const versions = await api.workflowVersions(workflowId);
      if (!versions.items[0]) throw new Error("Workflow sürümü bulunamadı");
      setVersionHistory(versions.items);
      loadDefinition(versions.items[0]);
      await refreshMetadata(workflowId);
    } catch (reason) {
      setActionError(reason instanceof Error ? reason.message : "Workflow yüklenemedi");
    } finally { setBusy(false); }
  }

  async function openVersion(definition: WorkflowDefinition) {
    loadDefinition(definition);
    setHistoryOpen(false);
  }

  async function cloneCurrent() {
    if (!workflow || !canEdit) return;
    setBusy(true);
    setActionError(null);
    try {
      const draft = await api.cloneWorkflow(workflow);
      loadDefinition(draft);
      await refreshMetadata(draft.id);
    } catch (reason) {
      setActionError(reason instanceof Error ? reason.message : "Workflow klonlanamadı");
    } finally { setBusy(false); }
  }

  async function createSchedule() {
    if (!workflow || workflow.status !== "published" || !isAdmin) return;
    setBusy(true);
    setActionError(null);
    try {
      await api.createWorkflowSchedule(workflow, cron, timezone);
      await refreshMetadata(workflow.id);
      setSaved(`v${workflow.version} için schedule oluşturuldu`);
    } catch (reason) {
      setActionError(reason instanceof Error ? reason.message : "Schedule oluşturulamadı");
    } finally { setBusy(false); }
  }

  async function toggleSchedule(schedule: WorkflowScheduleView) {
    if (!isAdmin) return;
    setBusy(true);
    setActionError(null);
    try {
      await api.setWorkflowScheduleEnabled(schedule.id, !schedule.enabled);
      if (workflow) await refreshMetadata(workflow.id);
    } catch (reason) {
      setActionError(reason instanceof Error ? reason.message : "Schedule güncellenemedi");
    } finally { setBusy(false); }
  }

  const selectedNode = nodes.find((node) => node.id === selectedId) ?? null;
  const onConnect = useCallback((connection: Connection) => setEdges((current) => addEdge({ ...connection, markerEnd: { type: MarkerType.ArrowClosed } }, current)), [setEdges]);
  const updateSelected = useCallback((updated: FlowNode) => {
    setNodes((current) => current.map((node) => node.id === updated.id ? updated : node));
    setSaved("Kaydedilmemiş değişiklikler");
  }, [setNodes]);
  const buildDto = useCallback((): WorkflowDefinition | null => workflow ? ({
    ...workflow,
    nodes: nodes.map((node) => ({ id: node.id, kind: node.data.kind, label: node.data.label, position: node.position, config: node.data.config, output_type: node.data.outputType })),
    edges: edges.map((edge) => ({ id: edge.id, source: edge.source, target: edge.target, data_type: String(edge.data?.dataType ?? nodes.find((node) => node.id === edge.source)?.data.outputType ?? "control"), branch: edge.sourceHandle === "true" || edge.sourceHandle === "false" ? edge.sourceHandle : null })),
  }) : null, [edges, nodes, workflow]);
  async function validate() {
    const dto = buildDto();
    if (!dto) return;
    const result = await api.validateWorkflow(dto);
    setValidation(result.valid ? "Geçerli graph" : `${result.issues.length} doğrulama hatası`);
  }
  async function save() {
    const dto = buildDto();
    if (!dto) return null;
    setBusy(true);
    setActionError(null);
    try {
      const persisted = await api.saveWorkflow({ ...dto, status: "draft" });
      setWorkflow(persisted);
      setSaved(`Taslak v${persisted.version} kaydedildi`);
      await refreshMetadata(persisted.id);
      return persisted;
    } catch (reason) {
      setActionError(reason instanceof Error ? reason.message : "Taslak kaydedilemedi");
      return null;
    } finally { setBusy(false); }
  }
  async function dryRun() {
    const dto = buildDto();
    if (!dto) return;
    setBusy(true);
    setActionError(null);
    try {
      const result = await api.dryRunWorkflow(dto);
      setValidation(result.status === "dry-run-completed" ? "Dry-run tamamlandı" : "Dry-run sonucu alındı");
    } catch (reason) { setActionError(reason instanceof Error ? reason.message : "Dry-run tamamlanamadı"); }
    finally { setBusy(false); }
  }
  async function publish() {
    const persisted = await save();
    if (!persisted) return;
    setBusy(true);
    try {
      const published = await api.publishWorkflow(persisted);
      loadDefinition(published);
      await refreshMetadata(published.id);
      setSaved(`v${published.version} immutable olarak yayınlandı`);
    } catch (reason) { setActionError(reason instanceof Error ? reason.message : "Workflow yayınlanamadı"); }
    finally { setBusy(false); }
  }
  async function run() {
    if (!workflow || workflow.status !== "published") {
      setActionError("Production run öncesinde workflow yayınlanmalıdır.");
      return;
    }
    setBusy(true);
    try {
      const result = await api.runWorkflow(workflow);
      setSaved(`Run ${result.run_id.slice(0, 8)} · ${result.status}`);
    } catch (reason) { setActionError(reason instanceof Error ? reason.message : "Workflow çalıştırılamadı"); }
    finally { setBusy(false); }
  }
  const onDrop = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    if (!canEdit || workflow?.status === "published") return;
    const kind = event.dataTransfer.getData("application/agi-node");
    const info = nodeInfo[kind];
    if (!info) return;
    const id = `${kind}_${Date.now().toString(36)}`;
    const position = screenToFlowPosition({ x: event.clientX, y: event.clientY });
    setNodes((current) => current.concat({ id, type: "workflowNode", position, data: { label: info.label, kind, subtitle: info.subtitle, tone: info.tone, config: info.config ?? {}, outputType: info.output } }));
    setSelectedId(id);
  }, [canEdit, screenToFlowPosition, setNodes, workflow?.status]);
  const workflowOptions = workflowCatalog.filter((item, index, items) =>
    items.findIndex((candidate) => candidate.id === item.id) === index,
  );
  const currentSchedules = schedules.filter((item) => item.workflow_id === workflow?.id);
  const readOnly = !canEdit || workflow?.status === "published";
  return (
    <div className="workflow-screen">
      <header className="workflow-toolbar">
        <div className="workflow-identity">
          <select aria-label="Workflow seçimi" value={workflow?.id ?? ""} onChange={(event) => openWorkflow(event.target.value)}>
            {workflowOptions.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select>
          <h1>{workflow?.name ?? "Growth Diagnostic"}</h1>
          <span>{workflow?.status === "published" ? `Published v${workflow.version}` : `Taslak v${workflow?.version ?? "–"}`}</span>
        </div>
        <div>
          <div style={{ position: "relative", display: "inline-block" }}>
            <button type="button" onClick={() => setTemplateOpen((current) => !current)}><FolderOpen size={17} /> Şablon Yükle</button>
            {templateOpen ? (
              <div style={{ position: "absolute", top: "100%", left: 0, zIndex: 100, background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "8px", boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.1)", width: "280px", padding: "8px", marginTop: "4px" }}>
                <div style={{ fontSize: "11px", fontWeight: 700, color: "#64748b", padding: "4px 8px", textTransform: "uppercase" }}>Hazır Büyüme Şablonları</div>
                {templates.map((tpl) => (
                  <button key={tpl.id} type="button" onClick={() => loadTemplate(tpl)} style={{ display: "block", width: "100%", textAlign: "left", padding: "8px", background: "none", border: "none", cursor: "pointer", borderRadius: "6px", fontSize: "12px", color: "#1e293b" }}>
                    <strong style={{ display: "block", color: "#0f172a" }}>{tpl.name}</strong>
                    <span style={{ fontSize: "11px", color: "#64748b" }}>{tpl.nodes.length} node · {tpl.edges.length} edge</span>
                  </button>
                ))}
              </div>
            ) : null}
          </div>
          <button aria-expanded={historyOpen} type="button" onClick={() => setHistoryOpen((current) => !current)}><History size={17} /> Sürümler</button>
          {workflow?.status === "published" ? <button type="button" onClick={cloneCurrent} disabled={busy || !canEdit}><Copy size={17} /> Klonla</button> : null}
          <button type="button" onClick={save} disabled={busy || readOnly}><Save size={17} /> Kaydet</button>
          <button type="button" onClick={dryRun} disabled={busy || !canEdit}><CirclePlay size={17} /> Dry-run</button>
          <button type="button" onClick={validate} disabled={busy}><Check size={17} /> Doğrula</button>
          <button type="button" onClick={run} disabled={busy || !canEdit || workflow?.status !== "published"}><Play size={17} /> Çalıştır</button>
          <button className="publish-button" type="button" onClick={publish} disabled={busy || !isAdmin || workflow?.status === "published"}><Upload size={17} /> Yayınla<ChevronDown size={15} /></button>
        </div>
      </header>
      {historyOpen ? <aside className="workflow-drawer">
        <header><div><History size={18} /><h2>Sürüm geçmişi</h2></div><button aria-label="Sürüm geçmişini kapat" type="button" onClick={() => setHistoryOpen(false)}><X size={17} /></button></header>
        <section className="workflow-version-list">
          {versionHistory.map((item) => <button className={workflow?.version === item.version ? "is-selected" : ""} key={`${item.id}-${item.version}`} onClick={() => openVersion(item)} type="button">
            <span><strong>v{item.version}</strong><small>{item.nodes.length} node · {item.edges.length} edge</small></span><em className="tag">{item.status}</em>
          </button>)}
        </section>
        <section className="schedule-panel">
          <h2><CalendarClock size={17} /> Schedule</h2>
          {currentSchedules.length === 0 ? <p>Bu workflow için schedule yok.</p> : currentSchedules.map((item) => <article key={item.id}>
            <div><strong>{item.cron}</strong><small>v{item.workflow_version} · {item.timezone}</small></div>
            <button disabled={busy || !isAdmin} onClick={() => toggleSchedule(item)} type="button">{item.enabled ? "Devre dışı bırak" : "Etkinleştir"}</button>
          </article>)}
          {workflow?.status === "published" && isAdmin ? <div className="schedule-form">
            <label>Cron<input value={cron} onChange={(event) => setCron(event.target.value)} /></label>
            <label>Timezone<input value={timezone} onChange={(event) => setTimezone(event.target.value)} /></label>
            <button disabled={busy} onClick={createSchedule} type="button"><Plus size={15} /> Schedule ekle</button>
          </div> : <p>Yeni schedule yalnız admin tarafından published sürüme bağlanabilir.</p>}
        </section>
      </aside> : null}
      <div className="workflow-body">
        <NodeCatalog />
        <div className="flow-canvas" onDrop={onDrop} onDragOver={(event) => { event.preventDefault(); event.dataTransfer.dropEffect = "move"; }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={(_, node) => setSelectedId(node.id)}
            onPaneClick={() => setSelectedId(null)}
            nodesConnectable={!readOnly}
            nodesDraggable={!readOnly}
            fitView
            minZoom={0.35}
            maxZoom={1.5}
            deleteKeyCode={null}
          >
            <Background gap={18} size={1} color="#d8dee7" />
            <Controls showInteractive={false} />
          </ReactFlow>
        </div>
        <Inspector agents={agents} modelProfiles={modelProfiles} capabilities={capabilitiesList} node={selectedNode} readOnly={readOnly} onChange={readOnly ? () => undefined : updateSelected} onDelete={() => { if (!readOnly && selectedId) setNodes((current) => current.filter((node) => node.id !== selectedId)); setSelectedId(null); }} />
      </div>
      {actionError ? <div className="inline-alert inline-alert--error" role="alert">{actionError}</div> : null}
      <footer className="workflow-status"><span><GitBranch size={15} /> {nodes.length} node</span><span><i /> <strong>{validation}:</strong> {workflow?.id} v{workflow?.version ?? "–"}</span><span><Check size={15} /> {saved}</span></footer>
    </div>
  );
}

export default function WorkflowEditor({ userRoles }: { userRoles: string[] }) {
  return <ReactFlowProvider><EditorSurface userRoles={userRoles} /></ReactFlowProvider>;
}
