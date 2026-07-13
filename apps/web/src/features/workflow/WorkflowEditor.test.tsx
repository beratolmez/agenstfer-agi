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
    const clone = vi.spyOn(api, "cloneWorkflow").mockResolvedValue(draft);
    const save = vi.spyOn(api, "saveWorkflow").mockResolvedValue(draft);
    vi.spyOn(api, "validateWorkflow").mockResolvedValue({ valid: true, issues: [] });
    const dryRun = vi.spyOn(api, "dryRunWorkflow").mockResolvedValue({ status: "dry-run-completed" });
    const publish = vi.spyOn(api, "publishWorkflow").mockResolvedValue({ ...draft, status: "published" });
    const run = vi.spyOn(api, "runWorkflow").mockResolvedValue({ run_id: "run-12345678", status: "awaiting_approval" });

    render(<WorkflowEditor />);
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
  });
});
