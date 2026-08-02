import { useTheme } from '../context/ThemeContext';

/**
 * Switches between AF's dark and light themes.
 *
 * Icon-only, so it carries an aria-label and a title rather than relying on
 * the glyph. The label states the action ("Switch to light") rather than the
 * current state, which is what a screen-reader user needs to hear from a
 * button.
 */
const ThemeToggle = () => {
  const { theme, toggle } = useTheme();
  const next = theme === 'dark' ? 'light' : 'dark';
  const label = `Switch to ${next} theme`;

  return (
    <button
      onClick={toggle}
      aria-label={label}
      title={label}
      className="ds-action ds-action--secondary"
      style={{ paddingInline: 'var(--space-3)' }}
    >
      <span aria-hidden="true" className="af-data">
        {theme === 'dark' ? 'LIGHT' : 'DARK'}
      </span>
    </button>
  );
};

export default ThemeToggle;
