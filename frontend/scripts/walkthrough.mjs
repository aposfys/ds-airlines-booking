/**
 * Record docs/media/usage.webm from the running application.
 *
 * Same reasoning as scripts/screenshots.mjs: the previous walkthrough was a
 * recording of a design prototype, not of this product, and the README
 * presented it as the product. This drives the real thing.
 *
 *     make dev          # in one shell
 *     make walkthrough  # in another
 *
 * Produces a .webm; the Makefile converts it to the looping animated WebP the
 * README embeds, because GitHub will not autoplay a video.
 */
import { chromium } from '@playwright/test';
import { mkdirSync, readdirSync, renameSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const BASE = process.env.SCREENSHOT_BASE_URL ?? 'http://localhost:5173';
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const OUT = join(ROOT, 'docs/media');
const RAW = join(ROOT, 'frontend/.walkthrough');

const stamp = Date.now().toString(36);
const user = `tour${stamp}`;
const pass = 'walkthrough-only-2026';

const run = async () => {
  mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    recordVideo: { dir: RAW, size: { width: 1280, height: 800 } },
  });
  const page = await context.newPage();
  const pause = (ms) => page.waitForTimeout(ms);

  // Register
  await page.goto(`${BASE}/register`, { waitUntil: 'domcontentloaded' });
  await pause(1200);
  await page.getByLabel('Full name').type('Alex Demo', { delay: 40 });
  await page.getByLabel('Username').type(user, { delay: 25 });
  await page.getByLabel('Email address').type(`${user}@example.com`, { delay: 15 });
  await page.getByLabel('Passport number').type('XX9912345', { delay: 30 });
  await page.getByLabel('Password').type(pass, { delay: 25 });
  await pause(600);
  await page.getByRole('button', { name: 'Create account' }).click();
  await page.waitForURL('**/login');
  await pause(900);

  // Sign in
  await page.getByLabel('Username').type(user, { delay: 35 });
  await page.getByLabel('Password').type(pass, { delay: 35 });
  await pause(400);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.waitForURL('**/dashboard');
  await pause(3000); // the weather lands

  // The hero carousel, driven rather than waited on
  await page.getByRole('button', { name: 'Next destination' }).click();
  await pause(1400);
  await page.getByRole('button', { name: 'Next destination' }).click();
  await pause(1400);

  // Down through destinations and the weather strip
  for (const y of [300, 600, 900, 1200]) {
    await page.mouse.wheel(0, y === 300 ? 300 : 300);
    await pause(700);
  }
  await pause(1200);

  // A search
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await pause(1200);
  await page.locator('#origin').fill('');
  await page.locator('#origin').type('ATH', { delay: 180 });
  await page.locator('#destination').fill('');
  await page.locator('#destination').type('LHR', { delay: 180 });
  await pause(2200);
  await page.locator('#flights').scrollIntoViewIfNeeded();
  await pause(2500);

  await context.close();
  await browser.close();

  const file = readdirSync(RAW).find((f) => f.endsWith('.webm'));
  if (!file) throw new Error('no video produced');
  renameSync(join(RAW, file), join(OUT, 'usage.webm'));
  console.log(`Recorded ${join(OUT, 'usage.webm')}`);
};

run().catch((e) => { console.error(e.message); process.exit(1); });
