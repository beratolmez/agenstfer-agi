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

test("workflow editor clones a draft and executes a labeled deterministic dry-run", async ({ page }) => {
  await page.goto("/#workflow");

  await expect(page.getByRole("heading", { name: "Growth Diagnostic" })).toBeVisible();
  await expect(page.getByText("Taslak yüklendi", { exact: false })).toBeVisible();
  await page.getByRole("button", { name: "Dry-run" }).click();
  await expect(page.getByText("Dry-run tamamlandı", { exact: false })).toBeVisible();
  await expect(page.getByRole("button", { name: "Çalıştır" })).toBeDisabled();
});
