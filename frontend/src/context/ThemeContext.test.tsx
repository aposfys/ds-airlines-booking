import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ThemeProvider, useTheme } from './ThemeContext';

const Probe = () => {
  const { theme, toggle } = useTheme();
  return (
    <>
      <span data-testid="theme">{theme}</span>
      <button onClick={toggle}>toggle</button>
    </>
  );
};

const renderProbe = () =>
  render(
    <ThemeProvider>
      <Probe />
    </ThemeProvider>,
  );

/* The provider asks one question — "(prefers-color-scheme: dark)" — because
   light is the default and dark is the departure from it. This stub answers
   whatever is asked, so the flag reads as "the OS prefers dark". */
const prefersDark = (matches: boolean) =>
  vi.stubGlobal(
    'matchMedia',
    vi.fn().mockImplementation((query: string) => ({
      matches,
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
      onchange: null,
    })),
  );

describe('ThemeProvider', () => {
  beforeEach(() => {
    document.documentElement.removeAttribute('data-theme');
  });

  describe('resolution order', () => {
    it('prefers an explicit stored choice over everything', async () => {
      localStorage.setItem('ds-theme', 'light');
      prefersDark(true); // the OS says dark; the stored choice wins
      renderProbe();
      expect(screen.getByTestId('theme')).toHaveTextContent('light');
    });

    it('falls back to the operating system when nothing is stored', () => {
      prefersDark(true);
      renderProbe();
      expect(screen.getByTestId('theme')).toHaveTextContent('dark');
    });

    it('falls back to the light default when the OS expresses no preference', () => {
      prefersDark(false);
      renderProbe();
      expect(screen.getByTestId('theme')).toHaveTextContent('light');
    });

    it('ignores a stored value that is not a theme', () => {
      localStorage.setItem('ds-theme', 'chartreuse');
      prefersDark(false);
      renderProbe();
      expect(screen.getByTestId('theme')).toHaveTextContent('light');
    });
  });

  describe('applying the theme', () => {
    it('sets data-theme on the document element', () => {
      prefersDark(false);
      renderProbe();
      // A bare :root is already light, but the attribute is written anyway so
      // the rendered theme is never merely the absence of one.
      expect(document.documentElement.dataset.theme).toBe('light');
    });

    it('sets the attribute explicitly in both directions', async () => {
      prefersDark(true);
      renderProbe();
      expect(document.documentElement.dataset.theme).toBe('dark');

      await userEvent.click(screen.getByRole('button', { name: 'toggle' }));
      expect(document.documentElement.dataset.theme).toBe('light');
    });
  });

  describe('toggling', () => {
    it('switches and persists the choice', async () => {
      prefersDark(false);
      renderProbe();

      await userEvent.click(screen.getByRole('button', { name: 'toggle' }));

      expect(screen.getByTestId('theme')).toHaveTextContent('dark');
      expect(localStorage.getItem('ds-theme')).toBe('dark');
    });

    it('does not persist anything before the passenger chooses', () => {
      prefersDark(false);
      renderProbe();
      // Following the system is not a choice, and storing it would freeze
      // the interface against later system changes.
      expect(localStorage.getItem('ds-theme')).toBeNull();
    });
  });

  it('throws when used outside the provider', () => {
    const quiet = vi.spyOn(console, 'error').mockImplementation(() => {});
    expect(() => render(<Probe />)).toThrow(/must be used within a ThemeProvider/);
    quiet.mockRestore();
  });
});
