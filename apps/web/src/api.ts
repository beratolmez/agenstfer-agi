import type { GrowthDiagnostic, WorkflowDefinition } from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    credentials: "include",
    headers: { "content-type": "application/json", ...init?.headers },
    ...init,
  });
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json() as Promise<T>;
}

export const api = {
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
