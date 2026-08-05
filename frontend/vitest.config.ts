import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    // Only the component suite. e2e/ holds Playwright specs, which import a
    // different `test` and must not be collected here.
    include: ['src/**/*.test.{ts,tsx}'],
    exclude: ['e2e/**', 'node_modules/**', 'dist/**'],
    // The Atlas token layer is 250+ lines of CSS custom properties that jsdom
    // cannot evaluate and no assertion here depends on. Colour and contrast
    // are covered by docs/brand/contrast_check.py against the real files.
    css: false,
    coverage: {
      provider: 'v8',
      include: ['src/**/*.{ts,tsx}'],
      exclude: ['src/test/**', 'src/main.tsx', 'src/types.ts', 'src/design-system/**'],
    },
  },
});
