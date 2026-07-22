import { chromium } from "playwright";
import path from "path";
import fs from "fs";

const artifactDir = "C:\\Users\\mypc\\.gemini\\antigravity\\brain\\a3747b88-a3a9-42f4-9159-69e5c56f0161";

async function runBrowserTest() {
  console.log("Starting Playwright browser UI test on http://localhost:8080...");
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  // 1. Open Setup Wizard
  await page.goto("http://localhost:8080/#setup", { waitUntil: "networkidle" });
  await page.screenshot({ path: path.join(artifactDir, "ui_setup_wizard_step1.png") });
  console.log("Saved ui_setup_wizard_step1.png");

  // Click step 2
  const nextBtn = await page.$("button:has-text('Devam Et'), button:has-text('Sonraki')");
  if (nextBtn) {
    await nextBtn.click();
    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(artifactDir, "ui_setup_wizard_step2.png") });
    console.log("Saved ui_setup_wizard_step2.png");
  }

  // 2. Open Dashboard
  await page.goto("http://localhost:8080/#dashboard", { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(artifactDir, "ui_dashboard.png") });
  console.log("Saved ui_dashboard.png");

  // 3. Open Events & Webhooks
  await page.goto("http://localhost:8080/#events", { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(artifactDir, "ui_events_panel.png") });
  console.log("Saved ui_events_panel.png");

  // 4. Open Workflow Dashboard
  await page.goto("http://localhost:8080/#workflow", { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(artifactDir, "ui_workflow_editor.png") });
  console.log("Saved ui_workflow_editor.png");

  // 5. Open Settings & Models
  await page.goto("http://localhost:8080/#settings", { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(artifactDir, "ui_settings.png") });
  console.log("Saved ui_settings.png");

  await browser.close();
  console.log("Browser UI test completed successfully.");
}

runBrowserTest().catch((err) => {
  console.error("Browser test error:", err);
  process.exit(1);
});
