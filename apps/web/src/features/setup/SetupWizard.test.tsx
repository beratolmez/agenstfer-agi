import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "../../api";
import { SetupWizard } from "./SetupWizard";

afterEach(() => vi.restoreAllMocks());

describe("SetupWizard", () => {
  it("allows navigating onboarding steps and handles model probe failure gracefully", async () => {
    vi.spyOn(api, "saveSetupProgress").mockResolvedValue({
      current_step: 1,
      completed_steps: [1],
      configuration: {},
      status: "in_progress",
      updated_at: null,
    });
    vi.spyOn(api, "setupProgress").mockResolvedValue({
      current_step: 0,
      completed_steps: [],
      configuration: {},
      status: "in_progress",
      updated_at: null,
    });
    vi.spyOn(api, "modelProfiles").mockResolvedValue({
      items: [
        {
          id: "cloud-balanced",
          provider: "gemini",
          model: "gemini-3.6-flash",
          local: false,
          enabled: true,
          configured: true,
          selected: true,
          available: true,
        },
      ],
    });
    const probe = vi.spyOn(api, "probeModel").mockRejectedValue(new Error("Seçili model kurulu değil"));

    render(<SetupWizard onComplete={vi.fn()} />);

    // Check step 1 heading
    expect(await screen.findByText(/1. Şirket Profili & Büyüme Hedefleri/i)).toBeInTheDocument();

    // Navigate to step 2 (Model Gateway)
    const nextBtn = screen.getByRole("button", { name: /Sonraki Adım: Model Gateway/i });
    fireEvent.click(nextBtn);

    // Click probe button in Step 2
    const probeBtn = await screen.findByRole("button", { name: /API Key & Modeli Canlı Test Et/i });
    fireEvent.click(probeBtn);

    expect(await screen.findByRole("alert")).toHaveTextContent("Seçili model kurulu değil");
    expect(probe).toHaveBeenCalled();
  });

  it("persists setup progress when clicking Sonraki Adım button in step 1", async () => {
    const saveProgress = vi.spyOn(api, "saveSetupProgress").mockResolvedValue({
      current_step: 2,
      completed_steps: [1, 2],
      configuration: {},
      status: "in_progress",
      updated_at: null,
    });
    vi.spyOn(api, "setupProgress").mockResolvedValue({
      current_step: 1,
      completed_steps: [1],
      configuration: {},
      status: "in_progress",
      updated_at: null,
    });
    vi.spyOn(api, "modelProfiles").mockResolvedValue({ items: [] });

    render(<SetupWizard onComplete={vi.fn()} />);

    expect(await screen.findByText(/1. Şirket Profili & Büyüme Hedefleri/i)).toBeInTheDocument();

    const nextBtn = screen.getByRole("button", { name: /Sonraki Adım: Model Gateway/i });
    fireEvent.click(nextBtn);

    expect(saveProgress).toHaveBeenCalledWith(
      expect.objectContaining({
        current_step: 2,
        completed_steps: [1, 2],
        status: "in_progress",
      })
    );
  });
});
