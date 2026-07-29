import { useEffect, useRef, useState } from 'react';
import { formatFare, formatFlightDate, groupCardDigits, isLuhnValid } from '../lib/format';
import type { Flight } from '../types';

interface Props {
  flight: Flight;
  defaultName: string;
  defaultPassport: string;
  onCancel: () => void;
  onConfirm: (details: {
    full_name: string;
    passport_num: string;
    credit_card: string;
  }) => Promise<void>;
}

/**
 * Collects the passenger and payment details for a booking.
 *
 * The dashboard previously had no booking form at all: it posted the
 * passenger's account name, a passport number that fell back to the literal
 * string "N/A", and a hardcoded card number with the comment
 * "Mocking input for demo".
 *
 * The card is sent once and never stored — the API keeps only the last four
 * digits. Phase 3 replaces this field with a provider-hosted input so the
 * number never reaches our servers at all.
 */
const BookingDialog = ({
  flight,
  defaultName,
  defaultPassport,
  onCancel,
  onConfirm,
}: Props) => {
  const [fullName, setFullName] = useState(defaultName);
  const [passport, setPassport] = useState(defaultPassport);
  const [card, setCard] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const firstFieldRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    firstFieldRef.current?.focus();
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCancel();
    };
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [onCancel]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!fullName.trim()) {
      setError('Enter the passenger name exactly as printed in the passport.');
      return;
    }
    if (passport.trim().length < 4) {
      setError('Enter the passport number exactly as printed, without spaces.');
      return;
    }
    if (!isLuhnValid(card)) {
      setError('Check the card number — some digits look wrong.');
      return;
    }

    setSubmitting(true);
    try {
      await onConfirm({
        full_name: fullName.trim(),
        passport_num: passport.trim(),
        credit_card: card.replace(/\s/g, ''),
      });
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data
        ?.detail;
      setError(detail ?? 'We could not complete the booking. Nothing has been charged.');
      setSubmitting(false);
    }
  };

  const field =
    'w-full px-4 py-2 bg-white border border-gray-300 rounded-[6px] focus:outline-none focus:border-secondary transition-colors';
  const label = 'block text-primary text-label font-bold tracking-[0.06em] uppercase mb-1';

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-dark/50 p-4"
      onClick={onCancel}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="booking-dialog-title"
        className="bg-white rounded-[12px] shadow-float w-full max-w-lg p-6 md:p-8"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="booking-dialog-title" className="text-section font-bold text-primary mb-1">
          Confirm your booking
        </h2>
        <p className="text-sm text-gray-600 mb-6">
          {flight.departure} → {flight.destination} · {formatFlightDate(flight.date)} at{' '}
          {flight.time}
        </p>

        {error && (
          <div
            role="alert"
            className="bg-red-50 border-l-4 border-danger p-3 mb-5 text-danger text-sm font-medium"
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className={label} htmlFor="passenger-name">
              Passenger name
            </label>
            <input
              id="passenger-name"
              ref={firstFieldRef}
              className={field}
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              autoComplete="name"
              required
            />
          </div>

          <div>
            <label className={label} htmlFor="passport">
              Passport number
            </label>
            <input
              id="passport"
              className={field}
              value={passport}
              onChange={(e) => setPassport(e.target.value.toUpperCase())}
              required
            />
          </div>

          <div>
            <label className={label} htmlFor="card">
              Card number
            </label>
            <input
              id="card"
              className={`${field} tabular`}
              value={card}
              onChange={(e) => setCard(groupCardDigits(e.target.value))}
              inputMode="numeric"
              autoComplete="cc-number"
              placeholder="4242 4242 4242 4242"
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              We store only the last four digits.
            </p>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-gray-200">
            <div>
              <div className="text-label uppercase tracking-[0.06em] text-gray-500 font-bold">
                Total
              </div>
              <div className="text-section font-bold text-signal tabular">
                {formatFare(flight.cost)}
              </div>
            </div>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={onCancel}
                className="px-5 py-2.5 rounded-full font-semibold text-primary hover:bg-accent transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="bg-signal text-white px-6 py-2.5 rounded-full font-semibold hover:opacity-90 transition-opacity shadow-md disabled:opacity-60"
              >
                {submitting ? 'Booking…' : 'Confirm booking'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default BookingDialog;
