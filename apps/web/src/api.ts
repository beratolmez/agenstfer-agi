import type { AuthSession, GrowthDiagnostic, SetupStatus, WorkflowDefinition } from "./types";

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
  const response = await fetch(path, {
    credentials: "include",
    headers: {
      "content-type": "application/json",
      ...(mutating && csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
      ...init?.headers,
    },
    ...init,
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
  dashboard: () => request<GrowthDiagnostic>("/api/dashboard"),
  runDiagnostic: () => request<GrowthDiagnostic>("/api/diagnostics/run", { method: "POST" }),
  workflow: () => request<WorkflowDefinition>("/api/workflows/default"),
  validateWorkflow: (workflow: WorkflowDefinition) =>
    request<{ valid: boolean; issues: Array<{ message: string }> }>("/api/workflows/validate", {
      method: "POST",
      body: JSON.stringify(workflow),
    }),
  knowledge: (query = "") =>
    request<{ items: Array<Record<string, unknown>> }>(`/api/knowledge?query=${encodeURIComponent(query)}`),
  setupDemo: () => request<Record<string, unknown>>("/api/setup/demo", { method: "POST" }),
};
