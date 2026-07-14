import type {
  AuthSession,
  DataSourceView,
  FilePreview,
  GrowthDiagnostic,
  OKFCandidateView,
  ApprovalView,
  SetupProgress,
  SetupStatus,
  SourceSyncRunView,
  UserView,
  WorkflowDefinition,
  WorkflowRunView,
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
  probeModel: () => request<{
    ready: boolean;
    profile: string;
    provider: string;
    model: string;
    local: boolean;
    structured_output: boolean;
  }>("/api/models/probe", { method: "POST" }),
  dashboard: () => request<GrowthDiagnostic | null>("/api/dashboard"),
  runDiagnostic: () => request<GrowthDiagnostic>("/api/diagnostics/run", {
    method: "POST",
    headers: { "Idempotency-Key": `diagnostic-${crypto.randomUUID()}` },
  }),
  workflow: () => request<WorkflowDefinition>("/api/workflows/default"),
  cloneWorkflow: (workflow: WorkflowDefinition) =>
    request<WorkflowDefinition>(
      `/api/workflows/${encodeURIComponent(workflow.id)}/versions/${workflow.version}/clone`,
      { method: "POST" },
    ),
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
  knowledge: (query = "") =>
    request<{ items: Array<Record<string, unknown>> }>(`/api/knowledge?query=${encodeURIComponent(query)}`),
  setupDemo: () => request<Record<string, unknown>>("/api/setup/demo", { method: "POST" }),
  syncDemoSource: () => request<{ total_records: number; sources: Array<{ source_id: string; records: number }> }>("/api/sources/demo/sync", { method: "POST" }),
  validateOkf: () => request<{ valid: boolean; errors: unknown[]; warnings: unknown[] }>("/api/okf/validate"),
  okfCandidates: () => request<{ items: OKFCandidateView[] }>("/api/okf/candidates"),
  candidateDiff: (candidateId: string) => request<{ diff: string; status: string }>(`/api/okf/candidates/${encodeURIComponent(candidateId)}/diff`),
  decideCandidate: (candidateId: string, decision: "approved" | "rejected", reason: string) =>
    request<{ status: string; revision: string; qmd: string }>(
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
  runDetail: (runId: string) => request<Record<string, unknown>>(`/api/runs/${encodeURIComponent(runId)}`),
  evidence: (evidenceId: string) => request<Record<string, unknown>>(`/api/evidence/${encodeURIComponent(evidenceId)}`),
  agents: () => request<{ items: Array<Record<string, unknown>> }>("/api/agents"),
  capabilities: () => request<{ items: Array<Record<string, unknown>> }>("/api/capabilities"),
  users: () => request<{ items: Array<UserView & { active: boolean; created_at: string }> }>("/api/users"),
  createUser: (payload: { email: string; name: string; password: string; roles: string[] }) =>
    request<UserView>("/api/users", { method: "POST", body: JSON.stringify(payload) }),
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
};
