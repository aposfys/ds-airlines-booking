import { expect, test } from '@playwright/test';

/**
 * Things that only exist once a real browser renders the page.
 *
 * Every case here corresponds to a Phase 1 defect that a green unit suite did
 * not see — most seriously the webfonts, which failed to load in the
 * production build with no error of any kind.
 */

test.describe('the typographic identity actually loads', () => {
  test('Gabarito and Spline Sans Mono are served, not silently substituted', async ({
    page,
  }) => {
    const fonts: string[] = [];
    page.on('response', (r) => {
      if (r.url().endsWith('.woff2')) fonts.push(`${r.url()} ${r.status()}`);
    });

    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    // The build once emitted "../assets/fonts/…" verbatim and shipped no
    // .woff2 at all under the previous design system, so everything fell
    // back to Helvetica without a warning. Fonts are self-hosted via
    // @fontsource now, but the failure mode this guards against is the
    // same class of bug.
    expect(fonts.length).toBeGreaterThan(0);
    expect(fonts.every((f) => f.endsWith('200'))).toBe(true);

    const loaded = await page.evaluate(
      () =>
        document.fonts.check('700 46px "Gabarito"') &&
        document.fonts.check('500 13px "Spline Sans Mono"'),
    );
    expect(loaded).toBe(true);
  });

  test('nothing 404s on any page', async ({ page }) => {
    const failures: string[] = [];
    page.on('response', (r) => {
      if (r.status() >= 400 && r.request().resourceType() !== 'xhr') {
        failures.push(`${r.status()} ${r.url()}`);
      }
    });

    for (const path of ['/login', '/register']) {
      await page.goto(path);
      await page.waitForLoadState('networkidle');
    }
    expect(failures).toEqual([]);
  });
});

test.describe('themes', () => {
  test('switches, and persists the choice across a reload', async ({ page }) => {
    await page.goto('/login');

    const initial = await page.evaluate(() => document.documentElement.dataset.theme);
    await page.getByRole('button', { name: /Switch to (light|dark) theme/ }).click();

    const switched = await page.evaluate(() => document.documentElement.dataset.theme);
    expect(switched).not.toBe(initial);

    await page.reload();
    expect(await page.evaluate(() => document.documentElement.dataset.theme)).toBe(switched);
  });

  test('follows the operating system when nothing has been chosen', async ({ browser }) => {
    const context = await browser.newContext({ colorScheme: 'light' });
    const page = await context.newPage();
    await page.goto('/login');
    expect(await page.evaluate(() => document.documentElement.dataset.theme)).toBe('light');
    await context.close();
  });

  test('the interface is legible in both', async ({ page }) => {
    for (const theme of ['dark', 'light']) {
      await page.goto('/login');
      await page.evaluate((t) => localStorage.setItem('ds-theme', t), theme);
      await page.reload();

      const heading = page.getByRole('heading', { name: 'Log in' });
      await expect(heading).toBeVisible();

      // A colour that resolves to nothing means a token failed to load.
      const colour = await heading.evaluate((el) => getComputedStyle(el).color);
      expect(colour).toMatch(/^(rgb|oklch|color)/);
    }
  });
});

test.describe('routing and session', () => {
  test('the dashboard is unreachable signed out', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/login/);
  });

  test('the root redirects', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL(/\/(login|dashboard)/);
  });

  test('a token the server rejects does not look like a session', async ({ page }) => {
    await page.goto('/login');
    await page.evaluate(() => localStorage.setItem('token', 'not.a.real.token'));
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/login/);
  });
});

test.describe('accessibility', () => {
  test('every form control has an accessible name', async ({ page }) => {
    for (const path of ['/login', '/register']) {
      await page.goto(path);
      const unnamed = await page.locator('input:visible').evaluateAll((inputs) =>
        inputs
          .filter((el) => {
            const id = el.getAttribute('id');
            const labelled =
              (id && document.querySelector(`label[for="${id}"]`)) ||
              el.getAttribute('aria-label') ||
              el.getAttribute('aria-labelledby');
            return !labelled;
          })
          .map((el) => el.outerHTML.slice(0, 80)),
      );
      expect(unnamed, `unlabelled inputs on ${path}`).toEqual([]);
    }
  });

  test('focus is visible when tabbing', async ({ page }) => {
    await page.goto('/login');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    const outline = await page.evaluate(() => {
      const el = document.activeElement as HTMLElement;
      const s = getComputedStyle(el);
      return { width: s.outlineWidth, style: s.outlineStyle };
    });
    // Atlas makes the focus ring non-negotiable; it is the only way a keyboard
    // user can tell where they are.
    expect(outline.style).not.toBe('none');
    expect(parseFloat(outline.width)).toBeGreaterThan(0);
  });

  test('interactive targets meet the 44px minimum', async ({ page }) => {
    await page.goto('/login');
    const small = await page.locator('button:visible').evaluateAll((buttons) =>
      buttons
        .map((b) => ({ text: b.textContent?.trim(), h: b.getBoundingClientRect().height }))
        .filter((b) => b.h < 44),
    );
    expect(small).toEqual([]);
  });

  test('the page declares its language', async ({ page }) => {
    await page.goto('/login');
    expect(await page.getAttribute('html', 'lang')).toBeTruthy();
  });
});
