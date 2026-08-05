import { Sun, MoonStars } from '@phosphor-icons/react';
import { useTheme } from '../context/ThemeContext';

/**
 * Switches between Atlas's dark and light themes.
 *
 * Icon-only, so it carries an aria-label and a title rather than relying on
 * the glyph. The label states the action ("Switch to light") rather than the
 * current state, which is what a screen-reader user needs to hear from a
 * button. The icon is decorative and repeats what the label already says,
 * per Atlas's iconography rule that a glyph never carries meaning alone.
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
      style={{ paddingInline: 'var(--sp-3)' }}
    >
      {theme === 'dark' ? (
        <Sun aria-hidden="true" weight="regular" className="v-icon" />
      ) : (
        <MoonStars aria-hidden="true" weight="regular" className="v-icon" />
      )}
      <span aria-hidden="true" className="v-num">
        {theme === 'dark' ? 'LIGHT' : 'DARK'}
      </span>
    </button>
  );
};

export default ThemeToggle;
