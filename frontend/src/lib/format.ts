/** Fares are in EUR on every route DS Airlines operates. The interface
 *  previously rendered them with a `$` prefix. */
const eur = new Intl.NumberFormat('el-GR', {
  style: 'currency',
  currency: 'EUR',
  minimumFractionDigits: 2,
});

export const formatFare = (amount: number): string => eur.format(amount);

export const formatFlightDate = (iso: string): string => {
  const parsed = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return iso;
  return parsed.toLocaleDateString('en-GB', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
};

/** Mirrors the server-side check in BookingCreate so the passenger is told
 *  about a mistyped digit before the request is made, not after. */
export const isLuhnValid = (cardNumber: string): boolean => {
  const digits = cardNumber.replace(/[ -]/g, '');
  if (!/^\d{12,19}$/.test(digits)) return false;

  let total = 0;
  const parity = digits.length % 2;
  for (let i = 0; i < digits.length; i += 1) {
    let d = Number(digits[i]);
    if (i % 2 === parity) {
      d *= 2;
      if (d > 9) d -= 9;
    }
    total += d;
  }
  return total % 10 === 0;
};

export const groupCardDigits = (value: string): string =>
  value
    .replace(/\D/g, '')
    .slice(0, 19)
    .replace(/(.{4})/g, '$1 ')
    .trim();
