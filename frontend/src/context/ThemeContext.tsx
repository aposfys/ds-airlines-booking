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
 * Airy Sky ships both themes token-complete and defaults to light. Nothing
 * exposed a switch, so the light theme was unreachable — and unreachable
 * styling is where accessibility regressions hide, which is exactly what
 * docs/brand/contrast_check.py checks for.
 *
 * Resolution order: an explicit stored choice, then the operating system's
 * preference, then the system's light default.
 */
const resolveInitialTheme = (): Theme => {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === 'dark' || stored === 'light') return stored;
  // Light is the default now, so the query asks about dark: an unset or
  // unsupported matchMedia lands on light, which is what a bare :root renders.
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
};

export const ThemeProvider = ({ children }: { children: ReactNode }) => {
  const [theme, setTheme] = useState<Theme>(resolveInitialTheme);

  useEffect(() => {
    // tokens.css keys the dark palette off [data-theme="dark"] and treats a
    // bare :root as light, but the attribute is set explicitly in
    // both directions so the state is legible in the DOM.
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  useEffect(() => {
    // Follow the system while the passenger has not chosen for themselves.
    if (localStorage.getItem(STORAGE_KEY)) return;
    const query = window.matchMedia('(prefers-color-scheme: dark)');
    const onChange = (e: MediaQueryListEvent) => setTheme(e.matches ? 'dark' : 'light');
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
