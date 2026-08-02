import { describe, expect, it } from 'vitest';
import { formatDuration, formatFare, formatFlightDate, formatTime } from './format';

describe('formatFare', () => {
  it('renders EUR, not USD', () => {
    // The interface rendered `${flight.cost}` — a dollar sign on a carrier
    // that operates exclusively in the eurozone (DEF-015).
    const formatted = formatFare('129.00');
    expect(formatted).toContain('€');
    expect(formatted).not.toContain('$');
  });

  it('accepts the string the API sends', () => {
    // Decimal is serialised as a string deliberately: money must not
    // round-trip through a float.
    expect(formatFare('187.05')).toBe(formatFare(187.05));
  });

  it('always shows two decimal places', () => {
    expect(formatFare('89')).toMatch(/89[.,]00/);
  });

  it('returns the input unchanged rather than NaN when it is not a number', () => {
    expect(formatFare('not-a-number')).toBe('not-a-number');
  });
});

describe('formatFlightDate', () => {
  it('formats a plain date', () => {
    expect(formatFlightDate('2026-08-15')).toBe('Sat, 15 Aug 2026');
  });

  it('formats a full timestamp', () => {
    expect(formatFlightDate('2026-08-15T10:30:00Z')).toContain('15 Aug 2026');
  });

  it('does not shift the day across a timezone boundary', () => {
    // A bare date parsed as UTC midnight renders as the previous day in any
    // negative offset. It is appended with T00:00:00 for that reason.
    expect(formatFlightDate('2026-01-01')).toContain('1 Jan 2026');
  });

  it('returns the input unchanged when it is unparseable', () => {
    expect(formatFlightDate('tomorrow')).toBe('tomorrow');
  });
});

describe('formatTime', () => {
  it('renders 24-hour time in UTC', () => {
    expect(formatTime('2026-08-15T10:30:00Z')).toBe('10:30');
  });

  it('pads the hour', () => {
    expect(formatTime('2026-08-15T06:20:00Z')).toBe('06:20');
  });

  it('returns empty for an unparseable value rather than "Invalid Date"', () => {
    expect(formatTime('nonsense')).toBe('');
  });
});

describe('formatDuration', () => {
  it('renders hours and padded minutes', () => {
    expect(formatDuration(225)).toBe('3h 45m');
    expect(formatDuration(125)).toBe('2h 05m');
  });

  it('omits the hour when under one', () => {
    expect(formatDuration(45)).toBe('45m');
  });

  it('handles an exact hour', () => {
    expect(formatDuration(120)).toBe('2h 00m');
  });
});
