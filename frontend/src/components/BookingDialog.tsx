import { useEffect, useRef, useState } from 'react';
import { formatDuration, formatFare, formatFlightDate, formatTime } from '../lib/format';
import type { FareOption, Flight } from '../types';

interface Props {
  flight: Flight;
  defaultName: string;
  defaultPassport: string;
  onCancel: () => void;
  onConfirm: (details: {
    fare_class_code: string;
    passenger_full_name: string;
    passenger_passport: string;
    seat_number?: string;
  }) => Promise<void>;
}

/**
 * Collects the fare and passenger details for a booking. No payment details:
 * see the note beside the demonstration notice below.
 *
 * The dashboard originally had no form at all: it posted the account holder's
 * name, a passport number that fell back to the string "N/A", and a hardcoded
 * card number commented "Mocking input for demo".
 *
 * Fare selection is new in Phase 1. The document model had one price per
 * flight with no way to express what it entitled the passenger to; the
 * relational model carries branded fares and their rules.
 */
const BookingDialog = ({
  flight,
  defaultName,
  defaultPassport,
  onCancel,
  onConfirm,
}: Props) => {
  const [fareCode, setFareCode] = useState(flight.fares[0]?.fare_class_code ?? '');
  const [fullName, setFullName] = useState(defaultName);
  const [passport, setPassport] = useState(defaultPassport);
  const [seat, setSeat] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const firstFieldRef = useRef<HTMLInputElement>(null);

  const selectedFare: FareOption | undefined = flight.fares.find(
    (f) => f.fare_class_code === fareCode,
  );

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

    if (!fareCode) {
      setError('Choose a fare to continue.');
      return;
    }
    if (!fullName.trim()) {
      setError('Enter the passenger name exactly as printed in the passport.');
      return;
    }
    if (passport.trim().length < 4) {
      setError('Enter the passport number exactly as printed, without spaces.');
      return;
    }
    setSubmitting(true);
    try {
      await onConfirm({
        fare_class_code: fareCode,
        passenger_full_name: fullName.trim(),
        passenger_passport: passport.trim().toUpperCase(),
        ...(seat.trim() ? { seat_number: seat.trim().toUpperCase() } : {}),
      });
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data
        ?.detail;
      setError(
        typeof detail === 'string'
          ? detail
          : 'We could not complete the booking. Nothing has been charged.',
      );
      setSubmitting(false);
    }
  };

  const labelClass = 'af-label block mb-2 text-muted';

  return (
    <div
      className="fixed inset-0 z-50 flex items-start md:items-center justify-center p-4 overflow-y-auto"
      style={{ background: 'var(--surface-scrim)' }}
      onClick={onCancel}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="booking-dialog-title"
        className="bg-raised border border-subtle w-full max-w-lg p-6 md:p-8 my-8"
        style={{ borderRadius: 'var(--radius-overlay)' }}
        onClick={(e) => e.stopPropagation()}
      >
        <span className="af-eyebrow">Confirm booking</span>
        <h2
          id="booking-dialog-title"
          className="text-lg uppercase tracking-[-0.028em] mt-2"
        >
          {flight.origin_iata} → {flight.destination_iata}
        </h2>
        <p className="af-data text-sm text-muted mt-2 mb-8">
          {flight.flight_number} · {formatFlightDate(flight.departure_date)} ·{' '}
          {formatTime(flight.scheduled_departure)}–{formatTime(flight.scheduled_arrival)} ·{' '}
          {formatDuration(flight.duration_minutes)}
        </p>

        {error && (
          <div
            role="alert"
            className="border-l-2 border-critical bg-critical-bg text-critical text-sm p-3 mb-6"
          >
            {error}
          </div>
        )}

        {/* noValidate is deliberate. With native validation on, the browser
            intercepts an empty required field first and shows its own
            message — "Please fill out this field" — so the messages written
            to the brand voice guide never appear. The fields keep `required`
            for assistive technology; the checks in handleSubmit are what the
            passenger actually reads. */}
        <form onSubmit={handleSubmit} className="space-y-6" noValidate>
          <div role="radiogroup" aria-labelledby="fare-legend">
            <p id="fare-legend" className={labelClass}>
              Fare
            </p>
            <div className="space-y-2">
              {flight.fares.map((fare) => {
                const selected = fareCode === fare.fare_class_code;
                return (
                  <label
                    key={fare.fare_class_code}
                    className={`flex items-start gap-3 p-3 border cursor-pointer transition-colors ${
                      selected
                        ? 'border-action bg-inset'
                        : 'border-hairline hover:border-edge'
                    }`}
                    style={{ borderRadius: 'var(--radius-control)' }}
                  >
                    <input
                      type="radio"
                      name="fare"
                      value={fare.fare_class_code}
                      checked={selected}
                      onChange={() => setFareCode(fare.fare_class_code)}
                      className="mt-1 accent-[var(--action-primary-bg)]"
                    />
                    <span className="flex-1">
                      <span className="flex justify-between items-baseline gap-2">
                        <span className="af-label text-strong">{fare.name}</span>
                        <span className="af-data text-sm text-strong">
                          {formatFare(fare.price_eur)}
                        </span>
                      </span>
                      <span className="block text-xs text-muted mt-1">
                        {[
                          fare.cabin_bag_included && 'cabin bag',
                          fare.checked_bag_included && 'checked bag',
                          fare.changeable && 'changeable',
                          fare.refundable && 'refundable',
                        ]
                          .filter(Boolean)
                          .join(' · ')}
                      </span>
                    </span>
                  </label>
                );
              })}
            </div>
          </div>

          <div>
            <label className={labelClass} htmlFor="passenger-name">
              Passenger name
            </label>
            <input
              id="passenger-name"
              ref={firstFieldRef}
              className="ds-field"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              autoComplete="name"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelClass} htmlFor="passport">
                Passport number
              </label>
              <input
                id="passport"
                className="ds-field af-data"
                value={passport}
                onChange={(e) => setPassport(e.target.value.toUpperCase())}
                required
              />
            </div>
            <div>
              <label className={labelClass} htmlFor="seat">
                Seat (optional)
              </label>
              <input
                id="seat"
                className="ds-field af-data"
                value={seat}
                onChange={(e) => setSeat(e.target.value.toUpperCase())}
                placeholder="12A"
                maxLength={4}
              />
            </div>
          </div>

          {/* No card field, deliberately. This is a public demonstration with
              no payment provider behind it, and an ordinary-looking card
              input will eventually be handed a real card by someone who did
              not read the page. The API refuses payment details outright
              (422) rather than accepting and discarding them. */}
          <div
            className="border-l-2 p-3"
            style={{
              // Not --status-info-*: AF derives those from the Signal ramp,
              // so an "info" panel renders vermilion and reads as an error.
              borderColor: 'var(--border-strong)',
              background: 'var(--status-neutral-bg)',
              borderRadius: 'var(--radius-control)',
            }}
          >
            <p className="af-label" style={{ color: 'var(--text-muted)' }}>
              Demonstration
            </p>
            <p className="text-xs text-muted mt-2">
              No payment is taken and no card details are collected. Do not enter real
              payment information anywhere in this application.
            </p>
          </div>

          <div className="flex items-center justify-between gap-4 pt-5 border-t border-hairline">
            <div>
              <span className="af-label text-muted">Total</span>
              <p className="af-data text-lg text-strong mt-1">
                {selectedFare ? formatFare(selectedFare.price_eur) : '—'}
              </p>
            </div>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={onCancel}
                className="ds-action ds-action--secondary"
              >
                Cancel
              </button>
              {/* The one primary action in this view. */}
              <button
                type="submit"
                disabled={submitting}
                className="ds-action ds-action--primary"
              >
                {submitting ? 'Booking…' : 'Confirm'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default BookingDialog;
