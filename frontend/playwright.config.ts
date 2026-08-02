import { defineConfig, devices } from '@playwright/test';

/**
 * End-to-end tests against the real stack: a real browser, the real API and a
 * real PostgreSQL.
 *
 * These exist because four Phase 1 defects were invisible to a green unit
 * suite and only appeared when the pages were actually rendered — including
 * the webfonts failing to load in the production build, which produced no
 * error at all.
 *
 * The API must already be running (`make dev` or `make e2e`); Playwright
 * starts the interface itself.
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false, // one database, shared seat inventory
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['github'], ['list']] : [['list']],
  timeout: 30_000,

  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:4173',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },

  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],

  webServer: {
    command: 'npm run build && npm run preview -- --port 4173',
    url: 'http://localhost:4173/login',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
