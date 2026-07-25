import type {
  AgentDefinitionView,
  AuthSession,
  CapabilityDefinitionView,
  DataSourceView,
  FilePreview,
  GrowthDiagnostic,
  ModelProfileView,
  ManagedUserView,
  OKFCandidateView,
  ApprovalView,
  SetupProgress,
  SetupStatus,
  SourceSyncRunView,
  UserView,
  WorkflowDefinition,
  WorkflowScheduleView,
  WorkflowSummary,
  WorkflowRunDetail,
  WorkflowRunStart,
  WorkflowRunView,
  TriggerRuleView,
  TriggerEventView,
} from "./types";

let csrfToken: string | null = null;

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public requestId?: string,
  ) {
    super(message);
  }
}

function rememberSession(session: AuthSession): AuthSession {
  csrfToken = session.csrf_token;
  return session;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const method = (init?.method ?? "GET").toUpperCase();
  const mutating = !["GET", "HEAD", "OPTIONS"].includes(method);
  const headers = new Headers(init?.headers);
  if (!(init?.body instanceof FormData) && !headers.has("content-type")) {
    headers.set("content-type", "application/json");
  }
  if (mutating && csrfToken) headers.set("X-CSRF-Token", csrfToken);
  const response = await fetch(path, {
    ...init,
    credentials: "include",
    headers,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null) as {
      error?: { code?: string; message?: string; request_id?: string };
    } | null;
    throw new ApiError(
      response.status,
      payload?.error?.code ?? `http.${response.status}`,
      payload?.error?.message ?? `${response.status} ${response.statusText}`,
      payload?.error?.request_id,
    );
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  setupStatus: () => request<SetupStatus>("/api/setup/status"),
  setupProgress: () => request<SetupProgress>("/api/setup/progress"),
  saveSetupProgress: (payload: Omit<SetupProgress, "updated_at">) =>
    request<SetupProgress>("/api/setup/progress", {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  me: () => request<AuthSession>("/api/auth/me").then(rememberSession),
  bootstrap: (payload: { token: string; email: string; name: string; password: string }) =>
    request<AuthSession>("/api/auth/bootstrap", {
      method: "POST",
      body: JSON.stringify(payload),
    }).then(rememberSession),
  login: (payload: { email: string; password: string }) =>
    request<AuthSession>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    }).then(rememberSession),
  logout: async () => {
    await request<void>("/api/auth/logout", { method: "POST" });
    csrfToken = null;
  },
  modelStatus: () => request<{ ready: boolean; profile: string; provider: string; model?: string; local?: boolean; message: string }>("/api/model/status"),
  modelProfiles: () => request<{ items: ModelProfileView[] }>("/api/models/profiles"),
  configureModelProvider: (payload: { provider: string; api_key: string; model?: string; profile_id?: string }) =>
    request<{ status: string; provider: string; model: string; profile: string }>("/api/models/configure", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  discoverModels: (provider: string, apiKey?: string) =>
    request<{ provider: string; models: string[]; dynamic: boolean }>("/api/models/discover", {
      method: "POST",
      body: JSON.stringify({ provider, api_key: apiKey }),
    }),
  probeModel: (profile?: string) => request<{
    ready: boolean;
    profile: string;
    provider: string;
    model: string;
    local: boolean;
    structured_output: boolean;
  }>(`/api/models/probe${profile ? `?profile=${encodeURIComponent(profile)}` : ""}`, {
    method: "POST",
  }),
  dashboard: () => request<GrowthDiagnostic | null>("/api/dashboard"),
  runDiagnostic: (workflow: WorkflowDefinition) => request<WorkflowRunStart>(
    `/api/diagnostics/run?workflow_id=${encodeURIComponent(workflow.id)}&version=${workflow.version}`,
    {
      method: "POST",
      headers: { "Idempotency-Key": `diagnostic-${crypto.randomUUID()}` },
    },
  ),
  workflow: () => request<WorkflowDefinition>("/api/workflows/default"),
  workflows: () => request<{ items: WorkflowSummary[] }>("/api/workflows"),
  workflowTemplates: () => request<{ items: WorkflowDefinition[] }>("/api/workflows/templates"),
  cloneWorkflow: (workflow: WorkflowDefinition, targetId?: string) => {
    const target = targetId ?? (workflow.id.startsWith("builtin-") ? "growth-diagnostic" : null);
    const query = target ? `?target_id=${encodeURIComponent(target)}` : "";
    return request<WorkflowDefinition>(
      `/api/workflows/${encodeURIComponent(workflow.id)}/versions/${workflow.version}/clone${query}`,
      { method: "POST" },
    );
  },
  workflowVersions: (workflowId: string) =>
    request<{ items: WorkflowDefinition[] }>(
      `/api/workflows/${encodeURIComponent(workflowId)}/versions`,
    ),
  prepareDiagnosticWorkflow: async (profile: string) => {
    const targetId = "growth-diagnostic";
    const versions = await request<{ items: WorkflowDefinition[] }>(
      `/api/workflows/${encodeURIComponent(targetId)}/versions`,
    );
    const matchesProfile = (definition: WorkflowDefinition) => {
      const agentNodes = definition.nodes.filter((node) => node.kind === "agent_run");
      return agentNodes.length > 0
        && agentNodes.every((node) => node.config.model_profile === profile);
    };
    const existing = versions.items.find(
      (item) => item.status === "published" && matchesProfile(item),
    );
    if (existing) return existing;

    const builtin = await request<WorkflowDefinition>("/api/workflows/default");
    const draft = await request<WorkflowDefinition>(
      `/api/workflows/${encodeURIComponent(builtin.id)}/versions/${builtin.version}/clone?target_id=${targetId}`,
      { method: "POST" },
    );
    const configured = {
      ...draft,
      nodes: draft.nodes.map((node) => node.kind === "agent_run"
        ? { ...node, config: { ...node.config, model_profile: profile } }
        : node),
    };
    const saved = await request<WorkflowDefinition>(
      `/api/workflows/${encodeURIComponent(configured.id)}/draft`,
      { method: "PUT", body: JSON.stringify(configured) },
    );
    return request<WorkflowDefinition>(
      `/api/workflows/${encodeURIComponent(saved.id)}/versions/${saved.version}/publish`,
      { method: "POST" },
    );
  },
  saveWorkflow: (workflow: WorkflowDefinition) =>
    request<WorkflowDefinition>(`/api/workflows/${encodeURIComponent(workflow.id)}/draft`, {
      method: "PUT",
      body: JSON.stringify(workflow),
    }),
  validateWorkflow: (workflow: WorkflowDefinition) =>
    request<{ valid: boolean; issues: Array<{ message: string }> }>("/api/workflows/validate", {
      method: "POST",
      body: JSON.stringify(workflow),
    }),
  dryRunWorkflow: (workflow: WorkflowDefinition) =>
    request<Record<string, unknown>>("/api/workflows/dry-run", {
      method: "POST",
      body: JSON.stringify(workflow),
    }),
  publishWorkflow: (workflow: WorkflowDefinition) =>
    request<WorkflowDefinition>(
      `/api/workflows/${encodeURIComponent(workflow.id)}/versions/${workflow.version}/publish`,
      { method: "POST" },
    ),
  runWorkflow: (workflow: WorkflowDefinition) =>
    request<{ run_id: string; status: string; current_step?: string }>(
      `/api/workflows/${encodeURIComponent(workflow.id)}/versions/${workflow.version}/run`,
      {
        method: "POST",
        headers: { "Idempotency-Key": `workflow-${crypto.randomUUID()}` },
      },
    ),
  workflowSchedules: () =>
    request<{ items: WorkflowScheduleView[] }>("/api/workflow-schedules"),
  createWorkflowSchedule: (workflow: WorkflowDefinition, cron: string, timezone: string) =>
    request<WorkflowScheduleView>(
      `/api/workflows/${encodeURIComponent(workflow.id)}/versions/${workflow.version}/schedules?cron=${encodeURIComponent(cron)}&timezone=${encodeURIComponent(timezone)}`,
      { method: "POST" },
    ),
  setWorkflowScheduleEnabled: (scheduleId: string, enabled: boolean) =>
    request<WorkflowScheduleView>(
      `/api/workflow-schedules/${encodeURIComponent(scheduleId)}?enabled=${enabled}`,
      { method: "PUT" },
    ),
  knowledge: (query = "") =>
    request<{ items: Array<Record<string, unknown>> }>(`/api/knowledge?query=${encodeURIComponent(query)}`),
  setupDemo: () => request<Record<string, unknown>>("/api/setup/demo", { method: "POST" }),
  syncDemoSource: () => request<{ total_records: number; sources: Array<{ source_id: string; records: number }> }>("/api/sources/demo/sync", { method: "POST" }),
  validateOkf: () => request<{ valid: boolean; errors: unknown[]; warnings: unknown[] }>("/api/okf/validate"),
  okfCandidates: () => request<{ items: OKFCandidateView[] }>("/api/okf/candidates"),
  candidateDiff: (candidateId: string) => request<{ diff: string; status: string }>(`/api/okf/candidates/${encodeURIComponent(candidateId)}/diff`),
  decideCandidate: (candidateId: string, decision: "approved" | "rejected", reason: string) =>
    request<{ candidate_id: string; status: string; revision: string; qmd: string }>(
      `/api/okf/candidates/${encodeURIComponent(candidateId)}/decision?decision=${decision}&reason=${encodeURIComponent(reason)}`,
      { method: "POST" },
    ),
  approvals: () => request<{ items: ApprovalView[] }>("/api/approvals"),
  decideApproval: (approvalId: string, decision: "approved" | "rejected", reason: string) =>
    request<{ run_status: string; qmd: string }>(
      `/api/approvals/${encodeURIComponent(approvalId)}/decision?decision=${decision}&reason=${encodeURIComponent(reason)}`,
      { method: "POST", headers: { "Idempotency-Key": `approval-${crypto.randomUUID()}` } },
    ),
  runs: () => request<{ items: WorkflowRunView[] }>("/api/runs"),
  runDetail: (runId: string) => request<WorkflowRunDetail>(
    `/api/runs/${encodeURIComponent(runId)}`,
  ),
  waitForDiagnostic: async (runId: string, timeoutMs = 7_200_000) => {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      const run = await request<WorkflowRunDetail>(`/api/runs/${encodeURIComponent(runId)}`);
      if (["awaiting_approval", "completed"].includes(run.status)) {
        if (!run.output?.diagnostic) {
          throw new Error("Workflow tamamlandı ancak kanıtlı diagnostic artifact bulunamadı");
        }
        return run.output.diagnostic;
      }
      if (["failed", "rejected", "expired", "cancelled"].includes(run.status)) {
        throw new Error(
          `Diagnostic workflow ${run.status}: ${run.error?.code ?? "güvenli hata ayrıntısı yok"}`,
        );
      }
      await new Promise((resolve) => globalThis.setTimeout(resolve, 2_000));
    }
    throw new Error("Diagnostic workflow zaman aşımına uğradı");
  },
  evidence: (evidenceId: string) => request<Record<string, unknown>>(`/api/evidence/${encodeURIComponent(evidenceId)}`),
  agents: () => request<{ items: AgentDefinitionView[] }>("/api/agents"),
  agentVersions: (agentId: string) => request<{ items: AgentDefinitionView[] }>(
    `/api/agents/${encodeURIComponent(agentId)}/versions`,
  ),
  agentVersion: (agentId: string, version: number) => request<AgentDefinitionView>(
    `/api/agents/${encodeURIComponent(agentId)}/versions/${version}`,
  ),
  cloneAgent: (agent: AgentDefinitionView) => request<AgentDefinitionView>(
    `/api/agents/${encodeURIComponent(agent.id)}/versions/${agent.version}/clone`,
    { method: "POST" },
  ),
  saveAgent: (agent: AgentDefinitionView) => request<AgentDefinitionView>(
    `/api/agents/${encodeURIComponent(agent.id)}/draft`,
    { method: "PUT", body: JSON.stringify(agent) },
  ),
  publishAgent: (agent: AgentDefinitionView) => request<AgentDefinitionView>(
    `/api/agents/${encodeURIComponent(agent.id)}/versions/${agent.version}/publish`,
    { method: "POST" },
  ),
  capabilities: () => request<{ items: CapabilityDefinitionView[] }>("/api/capabilities"),
  users: () => request<{ items: ManagedUserView[] }>("/api/users"),
  createUser: (payload: { email: string; name: string; password: string; roles: string[] }) =>
    request<UserView>("/api/users", { method: "POST", body: JSON.stringify(payload) }),
  updateUserRoles: (userId: string, roles: string[], active: boolean) =>
    request<UserView>(`/api/users/${encodeURIComponent(userId)}/roles`, {
      method: "PUT",
      body: JSON.stringify({ roles, active }),
    }),
  sources: () => request<{ items: DataSourceView[] }>("/api/sources"),
  sourceSyncRuns: () => request<{ items: SourceSyncRunView[] }>("/api/sources/sync-runs"),
  previewSourceFile: (file: File, entityType: string) => {
    const body = new FormData();
    body.append("file", file);
    return request<FilePreview>(
      `/api/sources/files/preview?entity_type=${encodeURIComponent(entityType)}`,
      { method: "POST", body },
    );
  },
  filePreview: (sourceId: string) => request<FilePreview>(`/api/sources/${sourceId}/preview`),
  triggerRules: () => request<{ items: TriggerRuleView[] }>("/api/triggers/rules"),
  triggerEvents: (limit = 50) => request<{ items: TriggerEventView[] }>(`/api/triggers/events?limit=${limit}`),
  sendWebhookPayload: (sourceId: string, payload: { event_type: string; data?: Record<string, unknown> }) =>
    request<{ event_id: string; status: string; matched_rules_count: number; triggered_workflows: string[] }>(
      `/api/webhooks/${sourceId}`,
      { method: "POST", body: JSON.stringify(payload) }
    ),
  mapSource: (
    sourceId: string,
    payload: { entity_type: string; field_mapping: Record<string, string>; classification: string },
  ) => request<Record<string, unknown>>(`/api/sources/${encodeURIComponent(sourceId)}/mapping`, {
    method: "POST",
    body: JSON.stringify(payload),
  }),
  syncSource: (sourceId: string) =>
    request<{ total_records: number }>(`/api/sources/${encodeURIComponent(sourceId)}/sync`, {
      method: "POST",
    }),
  testDbConnection: (payload: { db_type: string; host: string; port: number; database_name: string; username: string; password?: string }) =>
    request<{ status: string; db_type: string; host: string; database: string; tables_found: string[]; connection_time_ms: number; message: string }>("/api/sources/test-db", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  testMcpConnection: (payload: { mcp_url: string; auth_token?: string }) =>
    request<{ status: string; mcp_url: string; protocol_version: string; tools_discovered: Array<{ name: string; description: string }>; message: string }>("/api/sources/test-mcp", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};
