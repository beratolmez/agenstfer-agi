import { access, readFile } from "node:fs/promises";

import { expect, type Page, type APIResponse, test } from "@playwright/test";

const enabled = process.env.AGI_E2E_REAL_MODEL === "true";
const disposable = process.env.AGI_E2E_CONFIRM_DISPOSABLE === "true";
const adminEmail = process.env.AGI_E2E_ADMIN_EMAIL ?? "";
const adminPassword = process.env.AGI_E2E_ADMIN_PASSWORD ?? "";
const bootstrapToken = process.env.AGI_E2E_BOOTSTRAP_TOKEN ?? "";
const modelProfile = process.env.AGI_E2E_MODEL_PROFILE ?? "local-balanced";
const timeoutMs = Number(process.env.AGI_E2E_TIMEOUT_MS ?? 3_600_000);
const expectRestarts = process.env.AGI_E2E_EXPECT_RESTARTS === "true";
const restartReadyFile = process.env.AGI_E2E_RESTART_READY_FILE ?? "";
const restartEvidenceFile = process.env.AGI_E2E_RESTART_EVIDENCE_FILE ?? "";

type SetupStatus = {
  bootstrap_required: boolean;
  auth_enabled: boolean;
};

type WorkflowDefinition = {
  id: string;
  version: number;
  status: string;
  nodes: Array<{ kind: string; config: Record<string, unknown> }>;
  [key: string]: unknown;
};

type RunDetail = {
  id: string;
  status: string;
  current_step: string | null;
  error: { code?: string; message?: string } | null;
  steps: Array<{ agent_id: string | null; status: string }>;
};

async function checkedJson<T>(response: APIResponse, label: string): Promise<T> {
  if (!response.ok()) {
    throw new Error(`${label} failed (${response.status()}): ${await response.text()}`);
  }
  return response.json() as Promise<T>;
}

async function authenticate(page: Page, status: SetupStatus): Promise<string> {
  if (!status.auth_enabled) {
    throw new Error("Real-model release E2E refuses deployments with authentication disabled.");
  }
  await page.goto("/");
  const form = page.locator(".auth-card form");
  if (status.bootstrap_required) {
    if (!bootstrapToken) throw new Error("AGI_E2E_BOOTSTRAP_TOKEN is required on a clean install.");
    await form.locator('input[type="password"]').nth(0).fill(bootstrapToken);
    await form.locator('input:not([type="password"]):not([type="email"])').fill("Release Admin");
    await form.locator('input[type="email"]').fill(adminEmail);
    await form.locator('input[type="password"]').nth(1).fill(adminPassword);
  } else {
    await form.locator('input[type="email"]').fill(adminEmail);
    await form.locator('input[type="password"]').fill(adminPassword);
  }
  await form.locator('button[type="submit"]').click();
  await expect(page.locator(".app-shell")).toBeVisible();
  const session = await checkedJson<{ csrf_token: string | null }>(
    await page.request.get("/api/auth/me"),
    "Current session",
  );
  if (!session.csrf_token) throw new Error("Authenticated session did not return a CSRF token.");
  return session.csrf_token;
}

async function mutate(
  page: Page,
  csrfToken: string,
  path: string,
  options: { method?: string; data?: unknown; headers?: Record<string, string> } = {},
): Promise<APIResponse> {
  return page.request.fetch(path, {
    method: options.method ?? "POST",
    data: options.data,
    headers: { "X-CSRF-Token": csrfToken, ...options.headers },
  });
}

async function waitForRun(page: Page, runId: string, expected: string): Promise<RunDetail> {
  const deadline = Date.now() + timeoutMs;
  let last: RunDetail | null = null;
  let lastTransientError = "none";
  while (Date.now() < deadline) {
    let response: APIResponse;
    try {
      response = await page.request.get(`/api/runs/${encodeURIComponent(runId)}`);
    } catch (error) {
      lastTransientError = error instanceof Error ? error.name : "request error";
      await page.waitForTimeout(1_000);
      continue;
    }
    if ([502, 503, 504].includes(response.status())) {
      lastTransientError = `HTTP ${response.status()}`;
      await page.waitForTimeout(1_000);
      continue;
    }
    last = await checkedJson<RunDetail>(response, "Workflow run detail");
    if (last.status === expected) return last;
    if (["failed", "rejected", "expired", "cancelled"].includes(last.status)) {
      throw new Error(
        `Workflow ended as ${last.status} at ${last.current_step ?? "unknown"}: `
        + `${last.error?.code ?? "unknown error"}`,
      );
    }
    await page.waitForTimeout(5_000);
  }
  throw new Error(
    `Workflow did not reach ${expected} within ${timeoutMs} ms; last status was `
    + `${last?.status ?? "unknown"}; last transient error was ${lastTransientError}.`,
  );
}

async function waitForCoordinatedRestarts(page: Page, runId: string): Promise<void> {
  if (!expectRestarts) return;
  if (!restartReadyFile) {
    throw new Error("AGI_E2E_RESTART_READY_FILE is required when restart coordination is enabled.");
  }
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (restartEvidenceFile) {
      try {
        const evidence = JSON.parse(await readFile(restartEvidenceFile, "utf-8")) as {
          status?: string;
          failure_code?: string | null;
        };
        if (evidence.status === "failed") {
          throw new Error(`Restart watchdog failed: ${evidence.failure_code ?? "unknown"}.`);
        }
      } catch (error) {
        if (error instanceof Error && error.message.startsWith("Restart watchdog failed:")) {
          throw error;
        }
      }
    }
    try {
      await access(restartReadyFile);
      if ((await readFile(restartReadyFile, "utf-8")).trim() !== runId) {
        throw new Error("Restart coordination marker belongs to a different workflow run.");
      }
      const response = await page.request.get("/api/health");
      if (response.ok()) return;
    } catch {
      // The watchdog intentionally interrupts the app twice; retry until its ready marker exists.
    }
    await page.waitForTimeout(1_000);
  }
  throw new Error("The restart watchdog did not publish a healthy approval-ready checkpoint.");
}

test.describe("real model release journey", () => {
  test.skip(!enabled, "Set AGI_E2E_REAL_MODEL=true to run the opt-in release journey.");
  test.setTimeout(timeoutMs + 120_000);

  test("runs the durable four-agent diagnostic, citation, approval, and OKF export", async ({ page, context }) => {
    if (!disposable) throw new Error("Set AGI_E2E_CONFIRM_DISPOSABLE=true; this test mutates company state.");
    if (!adminEmail || !adminPassword) {
      throw new Error("AGI_E2E_ADMIN_EMAIL and AGI_E2E_ADMIN_PASSWORD are required.");
    }
    if (!Number.isFinite(timeoutMs) || timeoutMs < 60_000) {
      throw new Error("AGI_E2E_TIMEOUT_MS must be at least 60000.");
    }

    const status = await checkedJson<SetupStatus>(
      await page.request.get("/api/setup/status"),
      "Setup status",
    );
    const csrfToken = await authenticate(page, status);

    const setupConfiguration = {
      company_name: "Anka Endüstriyel Otomasyon",
      objective: "Mevcut müşteri tabanından kârlı büyüme",
      model_profile: modelProfile,
      source_mode: "synthetic-demo",
      locale: "tr-TR",
    };
    await checkedJson(
      await mutate(page, csrfToken, "/api/setup/progress", {
        method: "PUT",
        data: {
          current_step: 0,
          completed_steps: [],
          configuration: setupConfiguration,
          status: "in_progress",
        },
      }),
      "Reset setup progress",
    );

    await page.goto("/#setup");
    const next = page.locator(".setup-actions .primary-button");
    await next.click();
    await expect(page.locator(".setup-panel > p").first()).toContainText("2 / 10");
    await next.click();
    await expect(page.locator(".setup-panel > p").first()).toContainText("3 / 10");
    const probeResponse = page.waitForResponse(
      (response) => response.url().endsWith("/api/models/probe") && response.request().method() === "POST",
      { timeout: timeoutMs },
    );
    await next.click();
    expect((await probeResponse).ok()).toBeTruthy();
    await expect(page.locator(".setup-panel > p").first()).toContainText("4 / 10");
    await next.click();
    const syncResponse = page.waitForResponse(
      (response) => response.url().endsWith("/api/sources/demo/sync") && response.request().method() === "POST",
      { timeout: 120_000 },
    );
    await next.click();
    expect((await syncResponse).ok()).toBeTruthy();
    await next.click();
    await next.click();
    await expect(page.locator(".setup-panel > p").first()).toContainText("8 / 10");

    const published = await checkedJson<WorkflowDefinition>(
      await page.request.get("/api/workflows/default"),
      "Published workflow",
    );
    if (published.status !== "published") {
      throw new Error("A disposable release install must start without an existing workflow draft.");
    }
    const draft = await checkedJson<WorkflowDefinition>(
      await mutate(
        page,
        csrfToken,
        `/api/workflows/${encodeURIComponent(published.id)}/versions/${published.version}/clone?target_id=release-growth-diagnostic`,
      ),
      "Clone workflow",
    );
    draft.nodes = draft.nodes.map((node) => node.kind === "agent_run"
      ? { ...node, config: { ...node.config, model_profile: modelProfile } }
      : node);
    const saved = await checkedJson<WorkflowDefinition>(
      await mutate(page, csrfToken, `/api/workflows/${encodeURIComponent(draft.id)}/draft`, {
        method: "PUT",
        data: draft,
      }),
      "Save release workflow",
    );
    const releaseWorkflow = await checkedJson<WorkflowDefinition>(
      await mutate(
        page,
        csrfToken,
        `/api/workflows/${encodeURIComponent(saved.id)}/versions/${saved.version}/publish`,
      ),
      "Publish release workflow",
    );
    const runStart = await checkedJson<{ run_id: string; status: string }>(
      await mutate(
        page,
        csrfToken,
        `/api/workflows/${encodeURIComponent(releaseWorkflow.id)}/versions/${releaseWorkflow.version}/run`,
        { headers: { "Idempotency-Key": `release-e2e-${crypto.randomUUID()}` } },
      ),
      "Start durable workflow",
    );
    const awaiting = await waitForRun(page, runStart.run_id, "awaiting_approval");
    const agents = new Set(awaiting.steps.map((step) => step.agent_id).filter(Boolean));
    expect(agents).toEqual(new Set([
      "company-analyst",
      "growth-opportunity-analyst",
      "evidence-reviewer",
      "wiki-curator",
    ]));
    await waitForCoordinatedRestarts(page, runStart.run_id);

    await page.goto("/#dashboard");
    const table = page.getByRole("table");
    await expect(table).toBeVisible();
    await expect(table.locator(".opportunity-row:not(.opportunity-row--head)")).toHaveCount(5);
    await table.locator(".evidence-link").first().click();
    const sourceLink = page.locator('.evidence-drawer a[href^="/api/evidence/"]');
    const [sourcePage] = await Promise.all([context.waitForEvent("page"), sourceLink.click()]);
    await sourcePage.waitForLoadState();
    const evidence = JSON.parse(await sourcePage.locator("body").innerText()) as {
      snapshot_sha256?: string;
      locator?: Record<string, unknown>;
      excerpt?: unknown;
    };
    expect(evidence.snapshot_sha256).toMatch(/^[a-f0-9]{64}$/);
    expect(evidence.locator).toBeTruthy();
    expect(evidence.excerpt).toBeTruthy();
    await sourcePage.close();

    await page.goto("/#approvals");
    const pendingCard = page.locator(".approval-card").filter({ has: page.locator(".tag", { hasText: "pending" }) }).first();
    await expect(pendingCard).toBeVisible();
    await pendingCard.locator("button").filter({ has: page.locator("svg") }).first().click();
    await expect(page.locator(".diff-review pre")).not.toBeEmpty();
    const decisionResponse = page.waitForResponse(
      (response) => response.url().includes("/api/approvals/") && response.url().includes("/decision"),
      { timeout: 60_000 },
    );
    await pendingCard.locator(".primary-button").click();
    const decision = await checkedJson<{ run_status: string }>(await decisionResponse, "Approval decision");
    expect(decision.run_status).toBe("decision_submitted");
    await waitForRun(page, runStart.run_id, "completed");

    await page.reload();
    await expect(page.locator(".approval-card .tag", { hasText: "approved" }).first()).toBeVisible();
    const downloadPromise = page.waitForEvent("download");
    await page.locator('a[href="/api/okf/export"]').click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toBe("company-okf-0.1.zip");
    expect(await download.failure()).toBeNull();
    await download.delete();
  });
});
