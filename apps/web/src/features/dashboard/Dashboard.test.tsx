import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "../../api";
import { Dashboard } from "./Dashboard";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("Dashboard", () => {
  it("shows a truthful empty state instead of a synthetic diagnostic", async () => {
    vi.spyOn(api, "dashboard").mockResolvedValue(null);
    vi.spyOn(api, "setupProgress").mockResolvedValue({
      current_step: 7,
      completed_steps: [0, 1, 2, 3, 4, 5, 6],
      configuration: { model_profile: "local-strong" },
      status: "in_progress",
      updated_at: null,
    });
    const prepare = vi.spyOn(api, "prepareDiagnosticWorkflow")
      .mockRejectedValue(new Error("Model qualification required"));

    render(<Dashboard onNavigate={vi.fn()} />);

    expect(await screen.findByRole("heading", { name: "Henüz Growth Diagnostic yok" })).toBeVisible();
    expect(screen.queryByRole("table", { name: "Öncelikli fırsatlar" })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "İlk tanıyı çalıştır" }));
    await waitFor(() => expect(prepare).toHaveBeenCalledWith("local-strong"));
    expect(await screen.findByRole("alert")).toHaveTextContent("Model qualification required");
  });
});
