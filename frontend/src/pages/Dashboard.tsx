import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import BookingDialog from '../components/BookingDialog';
import { useAuth } from '../context/AuthContext';
import { formatDuration, formatFare, formatFlightDate, formatTime } from '../lib/format';
import type { Booking, Flight } from '../types';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [flights, setFlights] = useState<Flight[]>([]);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState<{ tone: 'positive' | 'critical'; text: string } | null>(
    null,
  );
  const [bookingFlight, setBookingFlight] = useState<Flight | null>(null);

  // IATA codes, matched exactly by the API. Free-text city search used to be
  // interpolated into a Mongo $regex (DEF-005); there is no pattern matching
  // left in the search path.
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');

  const loadBookings = useCallback(async () => {
    const { data } = await api.get<Booking[]>('/bookings');
    setBookings(data);
  }, []);

  const loadFlights = useCallback(async () => {
    const params: Record<string, string> = {};
    if (origin.trim().length === 3) params.origin = origin.trim();
    if (destination.trim().length === 3) params.destination = destination.trim();
    const { data } = await api.get<Flight[]>('/flights', { params });
    setFlights(data);
  }, [origin, destination]);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    const bootstrap = async () => {
      try {
        await Promise.all([loadFlights(), loadBookings()]);
      } catch {
        if (!cancelled) {
          setNotice({
            tone: 'critical',
            text: 'We could not load your flights. Try again shortly.',
          });
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void bootstrap();
    return () => {
      cancelled = true;
    };
    // Searching is driven by the debounce below, not by this effect.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  useEffect(() => {
    if (!user || loading) return;
    const timer = setTimeout(() => {
      loadFlights().catch(() =>
        setNotice({ tone: 'critical', text: 'Search is unavailable right now.' }),
      );
    }, 300);
    return () => clearTimeout(timer);
  }, [origin, destination, user, loading, loadFlights]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const confirmBooking = async (details: {
    fare_class_code: string;
    passenger_full_name: string;
    passenger_passport: string;
    credit_card: string;
    seat_number?: string;
  }) => {
    if (!bookingFlight) return;
    const { data } = await api.post<Booking>('/bookings', {
      flight_id: bookingFlight.id,
      ...details,
    });
    setBookingFlight(null);
    await Promise.all([loadFlights(), loadBookings()]);
    setNotice({
      tone: 'positive',
      text: `Booked. Your reference is ${data.booking_reference}.`,
    });
  };

  const cancelBooking = async (booking: Booking) => {
    if (
      !confirm(
        `Cancel booking ${booking.booking_reference} to ${booking.destination_iata}? This cannot be undone.`,
      )
    ) {
      return;
    }
    try {
      await api.delete(`/bookings/${booking.id}`);
      await Promise.all([loadFlights(), loadBookings()]);
      setNotice({ tone: 'positive', text: 'Your booking has been cancelled.' });
    } catch {
      setNotice({
        tone: 'critical',
        text: 'We could not cancel that booking. Nothing has changed.',
      });
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="af-label text-muted" role="status">
          Loading flights
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <a className="af-skip-link" href="#flights">
        Skip to flights
      </a>

      <nav className="border-b border-hairline">
        <div className="max-w-7xl mx-auto px-6 h-16 flex justify-between items-center gap-4">
          <div className="flex items-baseline gap-3">
            <span className="text-strong uppercase tracking-[-0.045em] font-black text-lg">
              DS Airlines
            </span>
            <span className="af-eyebrow hidden sm:inline">Delos Skyways</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted hidden sm:inline">{user?.full_name}</span>
            <button onClick={handleLogout} className="ds-action ds-action--secondary">
              Log out
            </button>
          </div>
        </div>
      </nav>

      {/* Search. Grain over full-bleed colour, per AF. */}
      <header className="af-grain border-b border-hairline bg-sunken">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <h1 className="af-hero" style={{ fontSize: 'var(--display-4)' }}>
            Where to next
          </h1>
          <p className="text-muted text-sm mt-3">
            Short-haul across Europe from Athens and Thessaloniki.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-xl mt-8">
            <div>
              <label htmlFor="origin" className="af-label block mb-2 text-muted">
                From
              </label>
              <input
                id="origin"
                className="ds-field af-data uppercase"
                placeholder="ATH"
                maxLength={3}
                value={origin}
                onChange={(e) => setOrigin(e.target.value.toUpperCase())}
              />
            </div>
            <div>
              <label htmlFor="destination" className="af-label block mb-2 text-muted">
                To
              </label>
              <input
                id="destination"
                className="ds-field af-data uppercase"
                placeholder="LHR"
                maxLength={3}
                value={destination}
                onChange={(e) => setDestination(e.target.value.toUpperCase())}
              />
            </div>
          </div>
          <p className="text-2xs text-faint mt-3">
            Three-letter airport codes. We fly from ATH and SKG to LHR, CDG, FRA, MUC, FCO
            and BCN.
          </p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-12">
        {notice && (
          <div
            role="status"
            className={`mb-8 p-4 border-l-2 text-sm ${
              notice.tone === 'positive'
                ? 'border-positive bg-positive-bg text-positive'
                : 'border-critical bg-critical-bg text-critical'
            }`}
          >
            {notice.text}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
          <section id="flights" className="lg:col-span-2">
            <h2 className="af-label text-muted mb-5">Available flights</h2>

            {flights.length === 0 ? (
              <div className="ds-panel p-8 text-center text-muted text-sm">
                No flights match that search. Try a different airport code.
              </div>
            ) : (
              <ul className="space-y-3">
                {flights.map((flight) => {
                  const cheapest = flight.fares.reduce<number | null>(
                    (min, f) =>
                      min === null || Number(f.price_eur) < min ? Number(f.price_eur) : min,
                    null,
                  );
                  return (
                    <li
                      key={flight.id}
                      className="ds-panel p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-5"
                    >
                      <div className="flex-1">
                        <div className="flex items-baseline gap-3 flex-wrap">
                          <span className="af-data text-lg text-strong">
                            {flight.origin_iata} → {flight.destination_iata}
                          </span>
                          <span className="af-label text-faint">
                            {flight.flight_number}
                          </span>
                        </div>
                        <p className="text-sm text-muted mt-1">
                          {flight.origin_city} to {flight.destination_city}
                        </p>
                        <p className="af-data text-xs text-muted mt-2">
                          {formatFlightDate(flight.departure_date)} ·{' '}
                          {formatTime(flight.scheduled_departure)}–
                          {formatTime(flight.scheduled_arrival)} ·{' '}
                          {formatDuration(flight.duration_minutes)}
                        </p>
                        {flight.seats_available <= 10 && (
                          <p className="af-label text-warning mt-2">
                            {flight.seats_available} seats remain
                          </p>
                        )}
                      </div>

                      <div className="flex items-center sm:flex-col sm:items-end justify-between gap-4 sm:border-l sm:border-hairline sm:pl-5">
                        <div className="sm:text-right">
                          <span className="af-label text-faint block">From</span>
                          <span className="af-data text-lg text-strong">
                            {cheapest === null ? '—' : formatFare(cheapest)}
                          </span>
                        </div>
                        <button
                          onClick={() => setBookingFlight(flight)}
                          disabled={flight.seats_available === 0}
                          className="ds-action ds-action--primary"
                        >
                          {flight.seats_available === 0 ? 'Full' : 'Select'}
                        </button>
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </section>

          <section className="lg:col-span-1">
            <h2 className="af-label text-muted mb-5">My itineraries</h2>
            {bookings.length === 0 ? (
              <div className="ds-panel p-8 text-center text-muted text-sm">
                You have not booked any flights yet.
              </div>
            ) : (
              <ul className="space-y-3">
                {bookings.map((booking) => {
                  const cancelled = booking.status === 'cancelled';
                  return (
                    <li key={booking.id} className="ds-panel p-4">
                      <div className="flex justify-between items-start gap-2">
                        <span className="af-data text-strong">
                          {booking.origin_iata} → {booking.destination_iata}
                        </span>
                        <span
                          className={`af-label px-2 py-1 ${
                            cancelled
                              ? 'bg-critical-bg text-critical'
                              : 'bg-positive-bg text-positive'
                          }`}
                        >
                          {cancelled ? 'Cancelled' : 'Confirmed'}
                        </span>
                      </div>
                      <p className="af-data text-xs text-muted mt-2">
                        {booking.flight_number} ·{' '}
                        {formatFlightDate(booking.scheduled_departure)}
                      </p>
                      <dl className="af-data text-xs text-muted mt-3 pt-3 border-t border-hairline space-y-1">
                        <div className="flex justify-between gap-2">
                          <dt className="af-label text-faint">Ref</dt>
                          <dd className="text-strong">{booking.booking_reference}</dd>
                        </div>
                        <div className="flex justify-between gap-2">
                          <dt className="af-label text-faint">Fare</dt>
                          <dd>
                            {booking.fare_class_code}
                            {booking.seat_numbers.length > 0 &&
                              ` · seat ${booking.seat_numbers.join(', ')}`}
                          </dd>
                        </div>
                        <div className="flex justify-between gap-2">
                          <dt className="af-label text-faint">Paid</dt>
                          <dd>
                            {formatFare(booking.amount_eur)} · card {booking.card_last4}
                          </dd>
                        </div>
                      </dl>
                      {!cancelled && (
                        <button
                          onClick={() => cancelBooking(booking)}
                          className="af-label text-critical mt-3 hover:underline"
                        >
                          Cancel booking
                        </button>
                      )}
                    </li>
                  );
                })}
              </ul>
            )}
          </section>
        </div>
      </main>

      {bookingFlight && (
        <BookingDialog
          flight={bookingFlight}
          defaultName={user?.full_name ?? ''}
          defaultPassport={user?.passport_number ?? ''}
          onCancel={() => setBookingFlight(null)}
          onConfirm={confirmBooking}
        />
      )}
    </div>
  );
};

export default Dashboard;
