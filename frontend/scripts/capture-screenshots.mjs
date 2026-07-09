/**
 * Captures the README screenshots against a running stack (docker compose up).
 *
 * One-time setup (playwright is intentionally not a project dependency):
 *   cd frontend
 *   npm i --no-save playwright && npx playwright install chromium
 *   node scripts/capture-screenshots.mjs
 */

import { mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const BASE = process.env.BASE_URL ?? "http://localhost:3000";
const OUT = fileURLToPath(new URL("../../docs/screenshots/", import.meta.url));
const PASSWORD = "DemoPassword1";

async function login(page, email) {
  await page.goto(`${BASE}/login`);
  await page.fill('input[name="email"]', email);
  await page.fill('input[name="password"]', PASSWORD);
  await page.click('button[type="submit"]');
  await page.waitForURL("**/documents");
}

async function logout(page) {
  await page.click(".nav-user button");
  await page.waitForURL("**/login");
}

const shot = (page, name) =>
  page.screenshot({ path: `${OUT}${name}.png` });

const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width: 1360, height: 850 },
  deviceScaleFactor: 2,
});
await mkdir(OUT, { recursive: true });

// 1 — login
await page.goto(`${BASE}/login`);
await page.waitForSelector('input[name="email"]');
await shot(page, "login");

// 2 — document library (demo user, seeded docs)
await login(page, "user@demo.docquery");
await page.waitForSelector(".data-table tbody tr");
await shot(page, "documents");

// 3 — chat with an open citation card
await page.goto(`${BASE}/chat`);
await page.click(".conversation-item");
await page.waitForSelector(".bubble-answer");
await page.click(".answer-content .chip");
await page.waitForSelector(".citation-card");
await shot(page, "chat");

// 4 — review queue (admin)
await logout(page);
await login(page, "admin@demo.docquery");
await page.goto(`${BASE}/review`);
await page.waitForSelector(".data-table tbody tr, .empty-state");
await shot(page, "review");

// 5 — usage dashboard
await page.goto(`${BASE}/admin/usage`);
await page.waitForSelector(".recharts-surface");
await page.waitForTimeout(600); // let the bars animate in
await shot(page, "usage");

await browser.close();
console.log(`Saved 5 screenshots to ${OUT}`);
