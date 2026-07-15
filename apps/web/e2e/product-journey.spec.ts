import { expect, test } from "@playwright/test";

const setupConfiguration = {
  company_name: "Anka Endüstriyel Otomasyon",
  objective: "Mevcut müşteri tabanından kârlı büyüme",
  model_profile: "local-balanced",
  source_mode: "synthetic-demo",
  locale: "tr-TR",
};

test("dashboard never presents a synthetic fallback as an agent result", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Henüz Growth Diagnostic yok" })).toBeVisible();
  await expect(page.getByRole("table", { name: "Öncelikli fırsatlar" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "İlk tanıyı çalıştır" })).toBeEnabled();
});

test("setup exposes only code-defined model profiles and keeps cloud disabled by default", async ({ page, request }) => {
  const reset = await request.put("/api/setup/progress", {
    data: {
      current_step: 2,
      completed_steps: [0, 1],
      configuration: setupConfiguration,
      status: "in_progress",
    },
  });
  expect(reset.ok()).toBeTruthy();

  await page.goto("/#setup");
  const profiles = page.getByLabel("Model profili");
  await expect(profiles).toBeVisible();
  await expect(profiles.locator('option[value="local-balanced"]')).toHaveCount(1);
  await expect(profiles.locator('option[value="local-strong"]')).toHaveCount(1);
  await expect(profiles.locator('option[value="cloud-balanced"]')).toHaveAttribute("disabled", "");
});

test("setup progress survives reload and demo data uses the real source pipeline", async ({ page, request }) => {
  const reset = await request.put("/api/setup/progress", {
    data: {
      current_step: 0,
      completed_steps: [],
      configuration: setupConfiguration,
      status: "in_progress",
    },
  });
  expect(reset.ok()).toBeTruthy();

  await page.goto("/#setup");
  await expect(page.getByRole("heading", { name: "İlk yönetici hazır" })).toBeVisible();
  await page.getByRole("button", { name: "Kaydet ve devam et" }).click();
  await expect(page.getByRole("heading", { name: "Rol ayrımını doğrulayın" })).toBeVisible();

  await page.reload();
  await expect(page.getByRole("heading", { name: "Rol ayrımını doğrulayın" })).toBeVisible();

  const jumpToSource = await request.put("/api/setup/progress", {
    data: {
      current_step: 4,
      completed_steps: [0, 1, 2, 3],
      configuration: setupConfiguration,
      status: "in_progress",
    },
  });
  expect(jumpToSource.ok()).toBeTruthy();
  await page.reload();
  await expect(page.getByRole("heading", { name: "Veri kaynağını seçin" })).toBeVisible();

  await page.getByRole("button", { name: "Kaydet ve devam et" }).click();
  await expect(page.getByText("Kaynaklar kalıcılaştırıldı")).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText("1783 kayıt · 3 kaynak")).toBeVisible();

  await page.goto("/#sources");
  await expect(page.getByRole("heading", { name: "Veri Kaynakları" })).toBeVisible();
  await expect(page.getByText("3 kaynak")).toBeVisible();
  await expect(page.getByText("src-crm-001 · demo")).toBeVisible();
  await expect(page.getByText("src-erp-001 · demo")).toBeVisible();
  await expect(page.getByText("src-strategy-001 · demo")).toBeVisible();
});

test("agent registry creates and publishes only an allowlisted typed agent draft", async ({ page }) => {
  await page.goto("/#settings");

  await expect(page.getByRole("heading", { name: "Ayarlar ve Registry" })).toBeVisible();
  await page.getByRole("button", { name: "Yeni", exact: true }).click();
  await page.getByLabel("Agent ID").fill("e2e-evidence-agent");
  await page.getByLabel("Ad", { exact: true }).fill("E2E Evidence Agent");
  await page.getByLabel("Versioned agent instruction").fill(
    "Use only supplied immutable evidence and return the requested typed result.",
  );
  await page.getByRole("button", { name: "Kaydet" }).click();
  await expect(page.getByText("e2e-evidence-agent v1 taslağı kaydedildi.")).toBeVisible();
  await page.getByRole("button", { name: "Yayınla" }).click();
  await expect(page.getByText("e2e-evidence-agent v1 immutable olarak yayınlandı.")).toBeVisible();
});

test("workflow editor persists version history and manages a published schedule", async ({ page }) => {
  await page.goto("/#workflow");

  await expect(page.getByRole("heading", { name: "Growth Diagnostic" })).toBeVisible();
  await expect(page.getByText(/Taslak v\d+ yüklendi/)).toBeVisible();
  await page.getByRole("button", { name: "Dry-run" }).click();
  await expect(page.getByText("Dry-run tamamlandı", { exact: false })).toBeVisible();
  await expect(page.getByRole("button", { name: "Çalıştır" })).toBeDisabled();

  await page.getByRole("button", { name: "Yayınla" }).click();
  await expect(page.getByText("immutable olarak yayınlandı", { exact: false })).toBeVisible();
  await expect(page.getByRole("button", { name: "Çalıştır" })).toBeEnabled();
  await page.getByRole("button", { name: "Sürümler" }).click();
  await page.getByRole("button", { name: "Schedule ekle" }).click();
  await expect(page.getByText("0 9 * * 1-5", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Devre dışı bırak" }).click();
  await expect(page.getByRole("button", { name: "Etkinleştir" })).toBeVisible();
});
