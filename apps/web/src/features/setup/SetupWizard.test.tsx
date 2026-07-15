import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "../../api";
import { SetupWizard } from "./SetupWizard";

afterEach(() => vi.restoreAllMocks());

describe("SetupWizard", () => {
  it("restores persisted progress and blocks advancement when the real model probe fails", async () => {
    vi.spyOn(api, "setupProgress").mockResolvedValue({
      current_step: 2, completed_steps: [0, 1], configuration: {}, status: "in_progress", updated_at: null,
    });
    vi.spyOn(api, "modelProfiles").mockResolvedValue({ items: [{
      id: "local-balanced", provider: "ollama", model: "qwen3.5:9b", local: true,
      enabled: true, configured: true, selected: true, available: false,
    }] });
    const probe = vi.spyOn(api, "probeModel").mockRejectedValue(new Error("Seçili model kurulu değil"));
    const save = vi.spyOn(api, "saveSetupProgress");

    render(<SetupWizard onComplete={vi.fn()} />);
    const action = await screen.findByRole("button", { name: /Modeli test et ve devam et/i });
    fireEvent.click(action);
    expect(await screen.findByRole("alert")).toHaveTextContent("Seçili model kurulu değil");
    expect(save).not.toHaveBeenCalled();
    expect(probe).toHaveBeenCalledWith("local-balanced");
    expect(screen.getByText("Adım 3 / 10")).toBeVisible();
  });
});
