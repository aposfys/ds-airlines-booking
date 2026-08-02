/** Fares are in EUR on every route DS Airlines operates. The interface
 *  previously rendered them with a `$` prefix. */
const eur = new Intl.NumberFormat('el-GR', {
  style: 'currency',
  currency: 'EUR',
  minimumFractionDigits: 2,
});

/** Accepts a string because the API serialises Decimal as a string, which is
 *  deliberate — money must not round-trip through a float. */
export const formatFare = (amount: string | number): string => {
  const value = typeof amount === 'string' ? Number(amount) : amount;
  return Number.isNaN(value) ? String(amount) : eur.format(value);
};

export const formatFlightDate = (iso: string): string => {
  const parsed = new Date(iso.length <= 10 ? `${iso}T00:00:00` : iso);
  if (Number.isNaN(parsed.getTime())) return iso;
  return parsed.toLocaleDateString('en-GB', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
};

export const formatTime = (iso: string): string => {
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) return '';
  return parsed.toLocaleTimeString('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'UTC',
  });
};

export const formatDuration = (minutes: number): string => {
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return hours ? `${hours}h ${String(rest).padStart(2, '0')}m` : `${rest}m`;
};
