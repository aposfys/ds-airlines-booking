import { useEffect, useRef, useState } from 'react';
import {
  formatDuration,
  formatFare,
  formatFlightDate,
  formatTime,
  groupCardDigits,
  isLuhnValid,
} from '../lib/format';
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
    credit_card: string;
    seat_number?: string;
  }) => Promise<void>;
}

/**
 * Collects the fare, passenger and payment details for a booking.
 *
 * The dashboard originally had no form at all: it posted the account holder's
 * name, a passport number that fell back to the string "N/A", and a hardcoded
 * card number commented "Mocking input for demo".
 *
 * Fare selection is new in Phase 1. The document model had one price per
 * flight with no way to express what it entitled the passenger to; the
 * relational model carries branded fares and their rules, so the passenger
 * can see what they differ on before choosing.
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
  const [card, setCard] = useState('');
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
    if (!isLuhnValid(card)) {
      setError('Check the card number — some digits look wrong.');
      return;
    }

    setSubmitting(true);
    try {
      await onConfirm({
        fare_class_code: fareCode,
        passenger_full_name: fullName.trim(),
        passenger_passport: passport.trim().toUpperCase(),
        credit_card: card.replace(/\s/g, ''),
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

  const field =
    'w-full px-4 py-2 bg-white border border-gray-300 rounded-[6px] focus:outline-none focus:border-secondary transition-colors';
  const label = 'block text-primary text-label font-bold tracking-[0.06em] uppercase mb-1';

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-dark/50 p-4 overflow-y-auto"
      onClick={onCancel}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="booking-dialog-title"
        className="bg-white rounded-[12px] shadow-float w-full max-w-lg p-6 md:p-8 my-8"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="booking-dialog-title" className="text-section font-bold text-primary mb-1">
          Confirm your booking
        </h2>
        <p className="text-sm text-gray-600 mb-6 tabular">
          {flight.flight_number} · {flight.origin_iata} → {flight.destination_iata} ·{' '}
          {formatFlightDate(flight.departure_date)} at {formatTime(flight.scheduled_departure)}{' '}
          · {formatDuration(flight.duration_minutes)}
        </p>

        {error && (
          <div
            role="alert"
            className="bg-red-50 border-l-4 border-danger p-3 mb-5 text-danger text-sm font-medium"
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <fieldset>
            <legend className={label}>Fare</legend>
            <div className="space-y-2">
              {flight.fares.map((fare) => (
                <label
                  key={fare.fare_class_code}
                  className={`flex items-start gap-3 p-3 border rounded-[6px] cursor-pointer transition-colors ${
                    fareCode === fare.fare_class_code
                      ? 'border-signal bg-accent'
                      : 'border-gray-300 hover:border-secondary'
                  }`}
                >
                  <input
                    type="radio"
                    name="fare"
                    value={fare.fare_class_code}
                    checked={fareCode === fare.fare_class_code}
                    onChange={() => setFareCode(fare.fare_class_code)}
                    className="mt-1"
                  />
                  <span className="flex-1">
                    <span className="flex justify-between items-baseline gap-2">
                      <span className="font-bold text-primary">{fare.name}</span>
                      <span className="font-bold text-signal tabular">
                        {formatFare(fare.price_eur)}
                      </span>
                    </span>
                    <span className="block text-xs text-gray-600 mt-1">
                      {[
                        fare.cabin_bag_included && 'Cabin bag',
                        fare.checked_bag_included && 'Checked bag',
                        fare.changeable && 'Changeable',
                        fare.refundable && 'Refundable',
                      ]
                        .filter(Boolean)
                        .join(' · ')}
                    </span>
                  </span>
                </label>
              ))}
            </div>
          </fieldset>

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

          <div className="grid grid-cols-2 gap-4">
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
              <label className={label} htmlFor="seat">
                Seat <span className="font-normal lowercase tracking-normal">(optional)</span>
              </label>
              <input
                id="seat"
                className={`${field} tabular`}
                value={seat}
                onChange={(e) => setSeat(e.target.value.toUpperCase())}
                placeholder="12A"
                maxLength={4}
              />
            </div>
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
                {selectedFare ? formatFare(selectedFare.price_eur) : '—'}
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
