import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "../../api";
import type { AgentDefinitionView } from "../../types";
import { Settings } from "./Settings";

afterEach(() => vi.restoreAllMocks());

const published: AgentDefinitionView = {
  id: "company-analyst",
  name: "Company Analyst",
  version: 3,
  model_profile: "local-balanced",
  output_type: "CompanyAnalysis",
  capabilities: ["context.query"],
  timeout_seconds: 300,
  max_output_tokens: 900,
  data_classification: "internal",
  approval_risk: "low",
  system_prompt: "Analyze only supplied evidence and return the typed company analysis.",
  status: "published",
};
const draft: AgentDefinitionView = { ...published, version: 4, status: "draft" };

describe("Settings registry", () => {
  it("loads the persisted prompt and clones, saves, and publishes an agent version", async () => {
    vi.spyOn(api, "modelStatus").mockResolvedValue({
      ready: true, profile: "local-balanced", provider: "ollama", model: "qwen3.5:9b", message: "ready",
    });
    vi.spyOn(api, "modelProfiles").mockResolvedValue({ items: [{
      id: "local-balanced", provider: "ollama", model: "qwen3.5:9b", local: true,
      enabled: true, configured: true, selected: true, available: true,
    }] });
    vi.spyOn(api, "agents").mockResolvedValue({ items: [published] });
    vi.spyOn(api, "capabilities").mockResolvedValue({ items: [{
      id: "context.query", version: 1, name: "Context query", status: "published", definition: {},
    }] });
    vi.spyOn(api, "runs").mockResolvedValue({ items: [] });
    vi.spyOn(api, "users").mockResolvedValue({ items: [{
      id: "user-1", email: "admin@example.test", name: "Admin User",
      roles: ["admin", "analyst", "approver"], active: true, created_at: "2026-07-15T10:00:00Z",
    }] });
    vi.spyOn(api, "agentVersion").mockImplementation(async (_id, version) =>
      version === 4 ? draft : published,
    );
    const clone = vi.spyOn(api, "cloneAgent").mockResolvedValue(draft);
    const save = vi.spyOn(api, "saveAgent").mockResolvedValue(draft);
    const publish = vi.spyOn(api, "publishAgent").mockResolvedValue({ ...draft, status: "published" });

    render(<Settings onSetup={() => undefined} userRoles={["admin", "analyst"]} />);

    expect(await screen.findByDisplayValue(published.system_prompt!)).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Taslak klonla" }));
    await waitFor(() => expect(clone).toHaveBeenCalledWith(published));

    const prompt = await screen.findByDisplayValue(draft.system_prompt!);
    expect(prompt).toBeEnabled();
    fireEvent.change(prompt, { target: { value: "Use only supplied immutable evidence and produce the typed result." } });
    fireEvent.click(screen.getByRole("button", { name: "Kaydet" }));
    await waitFor(() => expect(save).toHaveBeenCalledWith(expect.objectContaining({
      id: "company-analyst", version: 4,
    })));

    fireEvent.click(screen.getByRole("button", { name: "Yayınla" }));
    await waitFor(() => expect(publish).toHaveBeenCalledWith(draft));
  });
});
