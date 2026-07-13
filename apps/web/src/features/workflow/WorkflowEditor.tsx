import {
  Bot,
  Box,
  Check,
  ChevronDown,
  CirclePlay,
  Database,
  FileOutput,
  FileSearch,
  GitBranch,
  GripVertical,
  Play,
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
import type { WorkflowDefinition } from "../../types";

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

function Inspector({ node, onChange, onDelete }: { node: FlowNode | null; onChange: (node: FlowNode) => void; onDelete: () => void }) {
  if (!node) return <aside className="node-inspector node-inspector--empty"><SlidersHorizontal size={28} /><h2>Node seçin</h2><p>Konfigürasyonu burada düzenleyebilirsiniz.</p></aside>;
  const currentNode = node;
  const config = currentNode.data.config;
  function updateConfig(key: string, value: unknown) {
    onChange({ ...currentNode, data: { ...currentNode.data, config: { ...config, [key]: value } } });
  }
  return (
    <aside className="node-inspector">
      <header><h2>{node.data.label}</h2><button type="button" aria-label="Inspector kapat"><X size={18} /></button></header>
      <section><h3>Genel</h3><label>ID<input value={node.id} disabled /></label><label>Açıklama<textarea value={node.data.subtitle} onChange={(event) => onChange({ ...node, data: { ...node.data, subtitle: event.target.value } })} /></label></section>
      {node.data.kind === "agent_run" ? (
        <section>
          <h3>Konfigürasyon</h3>
          <label>Agent<select value={String(config.agent_id ?? "company-analyst")} onChange={(event) => updateConfig("agent_id", event.target.value)}><option value="company-analyst">Company Analyst</option><option value="growth-opportunity-analyst">Growth Opportunity Analyst</option><option value="evidence-reviewer">Evidence Reviewer</option></select></label>
          <label>Model profili<select value={String(config.model_profile ?? "local-balanced")} onChange={(event) => updateConfig("model_profile", event.target.value)}><option>local-balanced</option><option>local-strong</option><option>cloud-balanced</option></select></label>
          <label>Çıktı tipi<select value={String(config.output_type ?? "CompanyAnalysis")} onChange={(event) => updateConfig("output_type", event.target.value)}><option>CompanyAnalysis</option><option>OpportunityHypotheses</option><option>EvidenceReview</option></select></label>
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
      <button className="delete-button" type="button" onClick={onDelete}><Trash2 size={16} /> Node'u sil</button>
    </aside>
  );
}

function EditorSurface() {
  const [workflow, setWorkflow] = useState<WorkflowDefinition | null>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState<FlowNode>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [validation, setValidation] = useState("Geçerli graph");
  const [saved, setSaved] = useState("Yükleniyor…");
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const { screenToFlowPosition, fitView } = useReactFlow();

  useEffect(() => {
    api.workflow().then(async (definition) => {
      const editable = definition.status === "published"
        ? await api.cloneWorkflow(definition)
        : definition;
      const flow = toFlow(editable);
      setWorkflow(editable);
      setNodes(flow.nodes);
      setEdges(flow.edges);
      setSelectedId("company_agent");
      requestAnimationFrame(() => fitView({ padding: 0.2 }));
      setSaved("Taslak yüklendi");
    }).catch((reason: Error) => setActionError(reason.message));
  }, [fitView, setEdges, setNodes]);

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
      setWorkflow(published);
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
    const kind = event.dataTransfer.getData("application/agi-node");
    const info = nodeInfo[kind];
    if (!info) return;
    const id = `${kind}_${Date.now().toString(36)}`;
    const position = screenToFlowPosition({ x: event.clientX, y: event.clientY });
    setNodes((current) => current.concat({ id, type: "workflowNode", position, data: { label: info.label, kind, subtitle: info.subtitle, tone: info.tone, config: info.config ?? {}, outputType: info.output } }));
    setSelectedId(id);
  }, [screenToFlowPosition, setNodes]);
  return (
    <div className="workflow-screen">
      <header className="workflow-toolbar">
        <div><h1>{workflow?.name ?? "Growth Diagnostic"}</h1><span>{workflow?.status === "published" ? "Yayınlandı" : `Taslak v${workflow?.version ?? "–"}`}</span></div>
        <div><button type="button" onClick={save} disabled={busy || workflow?.status === "published"}><Save size={17} /> Kaydet</button><button type="button" onClick={dryRun} disabled={busy}><CirclePlay size={17} /> Dry-run</button><button type="button" onClick={validate} disabled={busy}><Check size={17} /> Doğrula</button><button type="button" onClick={run} disabled={busy || workflow?.status !== "published"}><Play size={17} /> Çalıştır</button><button className="publish-button" type="button" onClick={publish} disabled={busy || workflow?.status === "published"}><Upload size={17} /> Yayınla<ChevronDown size={15} /></button></div>
      </header>
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
            fitView
            minZoom={0.35}
            maxZoom={1.5}
            deleteKeyCode={null}
          >
            <Background gap={18} size={1} color="#d8dee7" />
            <Controls showInteractive={false} />
          </ReactFlow>
        </div>
        <Inspector node={selectedNode} onChange={updateSelected} onDelete={() => { if (selectedId) setNodes((current) => current.filter((node) => node.id !== selectedId)); setSelectedId(null); }} />
      </div>
      {actionError ? <div className="inline-alert inline-alert--error" role="alert">{actionError}</div> : null}
      <footer className="workflow-status"><span><GitBranch size={15} /> {nodes.length} node</span><span><i /> <strong>{validation}:</strong> Growth Diagnostic v1</span><span><Check size={15} /> {saved} · 10:24:31</span></footer>
    </div>
  );
}

export default function WorkflowEditor() {
  return <ReactFlowProvider><EditorSurface /></ReactFlowProvider>;
}
