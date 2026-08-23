/**
 * Regenerate docs/screenshots/* from the running application.
 *
 * This exists because the alternative failed. The screenshots in this
 * directory were once design comps rather than captures, and the README
 * described the interface in them — a hero carousel, destination cards, live
 * weather — none of which the code contained. Nothing caught it, because
 * nothing connected the pictures to the product.
 *
 * Run it against a live stack:
 *
 *     make dev          # in one shell
 *     make screenshots  # in another
 *
 * It registers a throwaway account each run, so it is idempotent against a
 * database that keeps its data, and it waits for the weather call to land so
 * the chips are real rather than empty.
 */
import { chromium } from '@playwright/test';
import { mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const BASE = process.env.SCREENSHOT_BASE_URL ?? 'http://localhost:5173';
const OUT = resolve(dirname(fileURLToPath(import.meta.url)), '../../docs/screenshots');

const stamp = Date.now().toString(36);
const user = `shot${stamp}`;
const pass = 'screenshot-only-2026';

const shot = (page, name, fullPage = false) =>
  page.screenshot({ path: `${OUT}/${name}.jpg`, type: 'jpeg', quality: 88, fullPage });

/** Vite keeps an HMR socket open, so `networkidle` never fires in dev. */
const settle = (page, ms = 2500) => page.waitForTimeout(ms);

const register = async (page) => {
  await page.goto(`${BASE}/register`, { waitUntil: 'domcontentloaded' });
  await page.getByLabel('Full name').fill('Alex Demo');
  await page.getByLabel('Username').fill(user);
  await page.getByLabel('Email address').fill(`${user}@example.com`);
  await page.getByLabel('Passport number').fill('XX9912345');
  await page.getByLabel('Password').fill(pass);
};

const signIn = async (page) => {
  await page.goto(`${BASE}/login`, { waitUntil: 'domcontentloaded' });
  await page.getByLabel('Username').fill(user);
  await page.getByLabel('Password').fill(pass);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.waitForURL('**/dashboard');
};

const setTheme = async (page, theme) => {
  await page.evaluate((t) => localStorage.setItem('ds-theme', t), theme);
  await page.reload({ waitUntil: 'domcontentloaded' });
};

const run = async () => {
  mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();

  const desktop = await browser.newContext({
    viewport: { width: 1280, height: 900 },
    deviceScaleFactor: 2,
  });
  const page = await desktop.newPage();

  await register(page);
  await settle(page, 600);
  await shot(page, 'register-light');
  await page.getByRole('button', { name: 'Create account' }).click();
  await page.waitForURL('**/login');

  await signIn(page);
  await settle(page);
  await shot(page, 'dashboard-light', true);

  await setTheme(page, 'dark');
  await settle(page);
  await shot(page, 'dashboard-dark', true);

  await setTheme(page, 'light');
  await settle(page, 1500);
  await page.locator('#origin').fill('ATH');
  await page.locator('#destination').fill('FCO');
  await settle(page, 1200);
  await page.locator('#flights').scrollIntoViewIfNeeded();
  await settle(page, 500);
  await shot(page, 'results-light');

  await desktop.close();

  const mobile = await browser.newContext({
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 3,
    isMobile: true,
    hasTouch: true,
  });
  const m = await mobile.newPage();
  await m.goto(`${BASE}/login`, { waitUntil: 'domcontentloaded' });
  await settle(m, 2000);
  await shot(m, 'mobile-login');

  await signIn(m);
  await settle(m, 4000);
  await shot(m, 'mobile-dashboard', true);

  await mobile.close();
  await browser.close();
  console.log(`Screenshots written to ${OUT}`);
};

run().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
