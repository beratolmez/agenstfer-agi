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
    const run = vi.spyOn(api, "runDiagnostic").mockRejectedValue(new Error("Model qualification required"));

    render(<Dashboard onNavigate={vi.fn()} />);

    expect(await screen.findByRole("heading", { name: "Henüz Growth Diagnostic yok" })).toBeVisible();
    expect(screen.queryByRole("table", { name: "Öncelikli fırsatlar" })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "İlk tanıyı çalıştır" }));
    await waitFor(() => expect(run).toHaveBeenCalledOnce());
    expect(await screen.findByRole("alert")).toHaveTextContent("Model qualification required");
  });
});
