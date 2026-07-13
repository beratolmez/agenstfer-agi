import type {
  AuthSession,
  DataSourceView,
  FilePreview,
  GrowthDiagnostic,
  SetupStatus,
  SourceSyncRunView,
  WorkflowDefinition,
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
  dashboard: () => request<GrowthDiagnostic>("/api/dashboard"),
  runDiagnostic: () => request<GrowthDiagnostic>("/api/diagnostics/run", {
    method: "POST",
    headers: { "Idempotency-Key": `diagnostic-${crypto.randomUUID()}` },
  }),
  workflow: () => request<WorkflowDefinition>("/api/workflows/default"),
  validateWorkflow: (workflow: WorkflowDefinition) =>
    request<{ valid: boolean; issues: Array<{ message: string }> }>("/api/workflows/validate", {
      method: "POST",
      body: JSON.stringify(workflow),
    }),
  knowledge: (query = "") =>
    request<{ items: Array<Record<string, unknown>> }>(`/api/knowledge?query=${encodeURIComponent(query)}`),
  setupDemo: () => request<Record<string, unknown>>("/api/setup/demo", { method: "POST" }),
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
