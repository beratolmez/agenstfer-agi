import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "../../api";
import { ApprovalCenter } from "./ApprovalCenter";

afterEach(() => vi.restoreAllMocks());

describe("ApprovalCenter", () => {
  it("loads a candidate diff and submits an idempotent human decision", async () => {
    vi.spyOn(api, "approvals").mockResolvedValue({ items: [{
      id: "approval-1", run_id: "run-12345678", kind: "okf-candidate-merge", status: "pending",
      artifact_uri: "artifact.md", requested_role: "approver", candidate_id: "candidate-1",
      decision_by: null, decision_reason: null, expires_at: "2026-07-20T12:00:00Z", decided_at: null,
    }] });
    vi.spyOn(api, "okfCandidates").mockResolvedValue({ items: [{
      id: "candidate-1", run_id: "run-12345678", status: "pending", base_revision: "a",
      candidate_revision: "b", validation_report: { errors: [], warnings: [] },
      created_at: "2026-07-13T12:00:00Z", expires_at: "2026-07-20T12:00:00Z", decision_reason: null,
    }] });
    vi.spyOn(api, "candidateDiff").mockResolvedValue({ diff: "+ evidence-reviewed report", status: "pending" });
    const decide = vi.spyOn(api, "decideApproval").mockResolvedValue({ run_status: "completed", qmd: "disabled" });

    render(<ApprovalCenter />);
    const diffButton = await screen.findByRole("button", { name: "Diff" });
    fireEvent.click(diffButton);
    expect(await screen.findByText("+ evidence-reviewed report")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Onayla" }));
    await waitFor(() => expect(decide).toHaveBeenCalledWith(
      "approval-1", "approved", "Kanıtlar ve OKF diff insan tarafından incelendi.",
    ));
  });
});
