import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach, beforeEach, vi } from 'vitest';

// jsdom implements neither of these, and both are load-bearing: ThemeContext
// reads matchMedia to follow the operating system, and the booking dialog is
// unreachable in a test that cannot scroll.
beforeEach(() => {
  vi.stubGlobal(
    'matchMedia',
    vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  );
  window.scrollTo = vi.fn();
  // jsdom does not always provide a working Storage, and several tests turn
  // on what is or is not persisted, so back it with a real in-memory store
  // rather than skipping the assertions.
  const store = new Map<string, string>();
  vi.stubGlobal('localStorage', {
    getItem: (k: string) => store.get(k) ?? null,
    setItem: (k: string, v: string) => void store.set(k, String(v)),
    removeItem: (k: string) => void store.delete(k),
    clear: () => store.clear(),
    key: (i: number) => [...store.keys()][i] ?? null,
    get length() {
      return store.size;
    },
  });
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});
