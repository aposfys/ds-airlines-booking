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

const prefersLight = (matches: boolean) =>
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
      prefersLight(false); // the OS says dark; the stored choice wins
      renderProbe();
      expect(screen.getByTestId('theme')).toHaveTextContent('light');
    });

    it('falls back to the operating system when nothing is stored', () => {
      prefersLight(true);
      renderProbe();
      expect(screen.getByTestId('theme')).toHaveTextContent('light');
    });

    it("falls back to Atlas's dark default when the OS expresses no preference", () => {
      prefersLight(false);
      renderProbe();
      expect(screen.getByTestId('theme')).toHaveTextContent('dark');
    });

    it('ignores a stored value that is not a theme', () => {
      localStorage.setItem('ds-theme', 'chartreuse');
      prefersLight(false);
      renderProbe();
      expect(screen.getByTestId('theme')).toHaveTextContent('dark');
    });
  });

  describe('applying the theme', () => {
    it('sets data-theme on the document element', () => {
      prefersLight(true);
      renderProbe();
      // Atlas's tokens.css keys the light palette off [data-theme="light"].
      expect(document.documentElement.dataset.theme).toBe('light');
    });

    it('sets the attribute explicitly in both directions', async () => {
      prefersLight(false);
      renderProbe();
      expect(document.documentElement.dataset.theme).toBe('dark');

      await userEvent.click(screen.getByRole('button', { name: 'toggle' }));
      expect(document.documentElement.dataset.theme).toBe('light');
    });
  });

  describe('toggling', () => {
    it('switches and persists the choice', async () => {
      prefersLight(false);
      renderProbe();

      await userEvent.click(screen.getByRole('button', { name: 'toggle' }));

      expect(screen.getByTestId('theme')).toHaveTextContent('light');
      expect(localStorage.getItem('ds-theme')).toBe('light');
    });

    it('does not persist anything before the passenger chooses', () => {
      prefersLight(true);
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
