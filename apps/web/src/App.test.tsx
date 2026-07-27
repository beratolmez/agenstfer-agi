import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("authentication gate", () => {
  it("shows first-admin bootstrap when authentication is enabled and no user exists", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      if (String(input).endsWith("/api/setup/status")) {
        return new Response(JSON.stringify({
          steps: [],
          demo_available: true,
          bootstrap_required: true,
          auth_enabled: true,
          cloud_models_enabled: false,
        }), { status: 200, headers: { "content-type": "application/json" } });
      }
      return new Response(null, { status: 404 });
    }));

    render(<App />);

    expect(await screen.findByRole("heading", { name: "İlk yöneticiyi oluşturun" })).toBeVisible();
    expect(screen.getByLabelText("Bootstrap token")).toBeVisible();
    expect(screen.getByRole("button", { name: "Yönetici oluştur" })).toBeEnabled();
  });

  it("enforces setup wizard gate when setup_completed is false even on #workflow hash route", async () => {
    window.location.hash = "#workflow";
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      if (String(input).endsWith("/api/setup/status")) {
        return new Response(JSON.stringify({
          steps: [],
          demo_available: true,
          bootstrap_required: false,
          auth_enabled: false,
          setup_completed: false,
          cloud_models_enabled: false,
        }), { status: 200, headers: { "content-type": "application/json" } });
      }
      return new Response(null, { status: 404 });
    }));

    render(<App />);

    expect(await screen.findByRole("heading", { name: /Agentic Growth Operating System — Onboarding/i })).toBeInTheDocument();
    expect(screen.queryByText(/Bileşen Deposu/i)).not.toBeInTheDocument();
  });
});
