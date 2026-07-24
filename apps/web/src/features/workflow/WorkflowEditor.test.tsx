import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "../../api";
import type { WorkflowDefinition } from "../../types";
import WorkflowEditor from "./WorkflowEditor";

afterEach(() => vi.restoreAllMocks());

const published: WorkflowDefinition = {
  id: "growth-diagnostic",
  name: "Growth Diagnostic v1",
  version: 1,
  status: "published",
  nodes: [
    { id: "trigger", kind: "manual_trigger", label: "Manual Trigger", position: { x: 0, y: 0 }, config: {}, output_type: "control" },
    { id: "report", kind: "report_output", label: "Report Output", position: { x: 200, y: 0 }, config: { format: "okf+html" }, output_type: "artifact" },
    { id: "approval", kind: "approval", label: "Approval", position: { x: 400, y: 0 }, config: { role: "approver", timeout_days: 7 }, output_type: "approved" },
  ],
  edges: [
    { id: "trigger-report", source: "trigger", target: "report", data_type: "control" },
    { id: "report-approval", source: "report", target: "approval", data_type: "artifact" },
  ],
};
const draft = { ...published, version: 2, status: "draft" };

describe("WorkflowEditor", () => {
  it("clones, saves, dry-runs, publishes, and starts a persisted version", async () => {
    vi.spyOn(api, "workflow").mockResolvedValue(published);
    vi.spyOn(api, "workflows").mockResolvedValue({ items: [{
      id: "builtin-growth-diagnostic", version: 3, name: "Built-in Growth Diagnostic",
      status: "published", created_at: "2026-07-15T10:00:00Z", updated_at: "2026-07-15T10:00:00Z",
    }] });
    vi.spyOn(api, "workflowVersions").mockResolvedValue({ items: [draft, published] });
    vi.spyOn(api, "workflowSchedules").mockResolvedValue({ items: [] });
    vi.spyOn(api, "agents").mockResolvedValue({ items: [] });
    vi.spyOn(api, "capabilities").mockResolvedValue({ items: [] });
    vi.spyOn(api, "modelProfiles").mockResolvedValue({ items: [{
      id: "local-balanced", provider: "ollama", model: "qwen3.5:9b", local: true,
      enabled: true, configured: true, selected: true, available: true,
    }] });
    const clone = vi.spyOn(api, "cloneWorkflow").mockResolvedValue(draft);
    const save = vi.spyOn(api, "saveWorkflow").mockResolvedValue(draft);
    vi.spyOn(api, "validateWorkflow").mockResolvedValue({ valid: true, issues: [] });
    const dryRun = vi.spyOn(api, "dryRunWorkflow").mockResolvedValue({ status: "dry-run-completed" });
    const publish = vi.spyOn(api, "publishWorkflow").mockResolvedValue({ ...draft, status: "published" });
    const run = vi.spyOn(api, "runWorkflow").mockResolvedValue({ run_id: "run-12345678", status: "awaiting_approval" });
    const schedule = vi.spyOn(api, "createWorkflowSchedule").mockResolvedValue({
      id: "schedule-1", workflow_id: draft.id, workflow_version: draft.version,
      cron: "0 9 * * 1-5", timezone: "Europe/Istanbul", enabled: true, last_fire_key: null,
    });

    render(<WorkflowEditor userRoles={["admin", "analyst"]} />);
    await screen.findByText("Taslak v2");
    expect(clone).toHaveBeenCalledWith(published);

    fireEvent.click(screen.getByRole("button", { name: "Kaydet" }));
    await waitFor(() => expect(save).toHaveBeenCalled());
    fireEvent.click(screen.getByRole("button", { name: "Dry-run" }));
    await waitFor(() => expect(dryRun).toHaveBeenCalled());
    fireEvent.click(screen.getByRole("button", { name: "Yayınla" }));
    await waitFor(() => expect(publish).toHaveBeenCalledWith(draft));
    fireEvent.click(screen.getByRole("button", { name: "Çalıştır" }));
    await waitFor(() => expect(run).toHaveBeenCalledWith({ ...draft, status: "published" }));
    expect(await screen.findByText(/run-1234/i)).toBeVisible();

    fireEvent.click(screen.getByRole("button", { name: "Sürümler" }));
    fireEvent.click(screen.getByRole("button", { name: "Schedule ekle" }));
    await waitFor(() => expect(schedule).toHaveBeenCalledWith(
      { ...draft, status: "published" }, "0 9 * * 1-5", "Europe/Istanbul",
    ));
  });
});
