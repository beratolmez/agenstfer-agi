import { expect, type Page, test } from "@playwright/test";

const enabled = process.env.AGI_E2E_RESTORED_STATE === "true";
const adminEmail = process.env.AGI_E2E_ADMIN_EMAIL ?? "";
const adminPassword = process.env.AGI_E2E_ADMIN_PASSWORD ?? "";

async function login(page: Page): Promise<void> {
  const status = await page.request.get("/api/setup/status");
  expect(status.ok()).toBeTruthy();
  const payload = await status.json() as { bootstrap_required: boolean; auth_enabled: boolean };
  if (!payload.auth_enabled || payload.bootstrap_required) {
    throw new Error("Restore verification requires an authenticated, already-bootstrapped install.");
  }
  await page.goto("/");
  const form = page.locator(".auth-card form");
  await form.locator('input[type="email"]').fill(adminEmail);
  await form.locator('input[type="password"]').fill(adminPassword);
  await form.locator('button[type="submit"]').click();
  await expect(page.locator(".app-shell")).toBeVisible();
}

test.describe("restored release state", () => {
  test.skip(!enabled, "Set AGI_E2E_RESTORED_STATE=true after restoring a release backup.");

  test("keeps the diagnostic, exact evidence, lexical search, approval, and export", async ({ page, context }) => {
    if (!adminEmail || !adminPassword) {
      throw new Error("AGI_E2E_ADMIN_EMAIL and AGI_E2E_ADMIN_PASSWORD are required.");
    }
    await login(page);

    const table = page.getByRole("table");
    await expect(table).toBeVisible();
    await expect(table.locator(".opportunity-row:not(.opportunity-row--head)")).toHaveCount(5);
    await table.locator(".evidence-link").first().click();
    const [sourcePage] = await Promise.all([
      context.waitForEvent("page"),
      page.locator('.evidence-drawer a[href^="/api/evidence/"]').click(),
    ]);
    await sourcePage.waitForLoadState();
    const evidence = JSON.parse(await sourcePage.locator("body").innerText()) as {
      snapshot_sha256?: string;
      locator?: Record<string, unknown>;
    };
    expect(evidence.snapshot_sha256).toMatch(/^[a-f0-9]{64}$/);
    expect(evidence.locator).toBeTruthy();
    await sourcePage.close();

    await page.goto("/#knowledge");
    const search = page.locator(".knowledge-page form");
    await search.locator("input").fill("Growth Diagnostic");
    await search.locator('button[type="submit"]').click();
    await expect(page.locator(".concept-row").first()).toBeVisible();

    await page.goto("/#approvals");
    await expect(page.locator(".approval-card .tag", { hasText: "approved" }).first()).toBeVisible();
    const downloadPromise = page.waitForEvent("download");
    await page.locator('a[href="/api/okf/export"]').click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toBe("company-okf-0.1.zip");
    expect(await download.failure()).toBeNull();
    await download.delete();
  });
});
