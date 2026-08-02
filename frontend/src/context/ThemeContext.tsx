import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';

export type Theme = 'dark' | 'light';

interface ThemeContextType {
  theme: Theme;
  toggle: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const STORAGE_KEY = 'ds-theme';

/**
 * AF ships both themes token-complete and defaults to dark. Nothing exposed a
 * switch, so the light theme was unreachable — and unreachable styling is
 * where accessibility regressions hide, which is exactly what
 * docs/brand/contrast_check.py found in it.
 *
 * Resolution order: an explicit stored choice, then the operating system's
 * preference, then AF's dark default.
 */
const resolveInitialTheme = (): Theme => {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === 'dark' || stored === 'light') return stored;
  return window.matchMedia?.('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
};

export const ThemeProvider = ({ children }: { children: ReactNode }) => {
  const [theme, setTheme] = useState<Theme>(resolveInitialTheme);

  useEffect(() => {
    // AF's color.css keys the light palette off [data-theme="light"] and
    // treats anything else as dark, but the attribute is set explicitly in
    // both directions so the state is legible in the DOM.
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  useEffect(() => {
    // Follow the system while the passenger has not chosen for themselves.
    if (localStorage.getItem(STORAGE_KEY)) return;
    const query = window.matchMedia('(prefers-color-scheme: light)');
    const onChange = (e: MediaQueryListEvent) => setTheme(e.matches ? 'light' : 'dark');
    query.addEventListener('change', onChange);
    return () => query.removeEventListener('change', onChange);
  }, []);

  const toggle = useCallback(() => {
    setTheme((current) => {
      const next = current === 'dark' ? 'light' : 'dark';
      localStorage.setItem(STORAGE_KEY, next);
      return next;
    });
  }, []);

  return (
    <ThemeContext.Provider value={{ theme, toggle }}>{children}</ThemeContext.Provider>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
