import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import BookingDialog from '../components/BookingDialog';
import { useAuth } from '../context/AuthContext';
import {
  formatDuration,
  formatFare,
  formatFlightDate,
  formatTime,
} from '../lib/format';
import type { Booking, Flight } from '../types';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [flights, setFlights] = useState<Flight[]>([]);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState<{ tone: 'success' | 'error'; text: string } | null>(
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
            tone: 'error',
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
        setNotice({ tone: 'error', text: 'Search is unavailable right now.' }),
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
      tone: 'success',
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
      setNotice({ tone: 'success', text: 'Your booking has been cancelled.' });
    } catch {
      setNotice({
        tone: 'error',
        text: 'We could not cancel that booking. Nothing has changed.',
      });
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-accent flex items-center justify-center">
        <p className="text-primary text-xl font-semibold" role="status">
          Loading flights…
        </p>
      </div>
    );
  }

  const searchField =
    'w-full text-lg border-b-2 border-gray-200 focus:border-secondary focus:outline-none py-2 transition-colors text-primary font-semibold placeholder-gray-400 uppercase tabular';
  const searchLabel =
    'block text-label font-bold text-gray-500 uppercase tracking-[0.06em] mb-1';

  return (
    <div className="min-h-screen bg-accent font-sans text-dark">
      <nav className="bg-primary text-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-baseline gap-3">
              <span className="text-2xl font-bold tracking-wider">DS Airlines</span>
              <span className="hidden sm:inline text-label font-light uppercase tracking-[0.3em] opacity-70">
                Delos Skyways
              </span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm font-medium">Welcome, {user?.full_name}</span>
              <button
                onClick={handleLogout}
                className="border border-white hover:bg-white hover:text-primary px-4 py-1.5 rounded-full text-sm font-semibold transition-colors"
              >
                Log out
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="bg-primary relative overflow-hidden pb-12 pt-8">
        <div className="absolute inset-0 bg-gradient-to-br from-primary via-primary to-secondary opacity-90"></div>
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <h1 className="text-display text-white mb-2 text-center">Where to next?</h1>
          <p className="text-center text-white/70 text-sm">
            Short-haul across Europe from Athens and Thessaloniki
          </p>

          <div className="bg-white rounded-[12px] shadow-float p-6 md:p-8 mt-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="origin" className={searchLabel}>
                  From
                </label>
                <input
                  id="origin"
                  className={searchField}
                  placeholder="ATH"
                  maxLength={3}
                  value={origin}
                  onChange={(e) => setOrigin(e.target.value.toUpperCase())}
                />
              </div>
              <div>
                <label htmlFor="destination" className={searchLabel}>
                  To
                </label>
                <input
                  id="destination"
                  className={searchField}
                  placeholder="LHR"
                  maxLength={3}
                  value={destination}
                  onChange={(e) => setDestination(e.target.value.toUpperCase())}
                />
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-3">
              Three-letter airport codes. We fly from ATH and SKG to LHR, CDG, FRA, MUC,
              FCO and BCN.
            </p>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {notice && (
          <div
            role="status"
            className={`mb-8 p-4 rounded-[6px] border-l-4 text-sm font-medium ${
              notice.tone === 'success'
                ? 'bg-green-50 border-success text-success'
                : 'bg-red-50 border-danger text-danger'
            }`}
          >
            {notice.text}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
          <section className="lg:col-span-2">
            <h2 className="text-section font-bold text-primary mb-6">Available flights</h2>

            {flights.length === 0 ? (
              <div className="bg-white rounded-[12px] p-8 text-center text-gray-600 shadow-card">
                No flights match that search. Try a different airport code.
              </div>
            ) : (
              <ul className="space-y-4">
                {flights.map((flight) => {
                  const cheapest = flight.fares.reduce<number | null>(
                    (min, f) =>
                      min === null || Number(f.price_eur) < min ? Number(f.price_eur) : min,
                    null,
                  );
                  return (
                    <li
                      key={flight.id}
                      className="bg-white rounded-[12px] shadow-card p-6 flex flex-col sm:flex-row justify-between items-center hover:shadow-float transition-shadow border border-gray-100"
                    >
                      <div className="flex-1 w-full mb-4 sm:mb-0">
                        <div className="flex items-center gap-3 mb-2 flex-wrap">
                          <span className="text-xl font-bold text-primary tabular">
                            {flight.origin_iata}
                          </span>
                          <span aria-hidden="true" className="text-secondary">
                            →
                          </span>
                          <span className="text-xl font-bold text-primary tabular">
                            {flight.destination_iata}
                          </span>
                          <span className="text-xs text-gray-500 font-semibold tabular">
                            {flight.flight_number}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600">
                          {flight.origin_city} to {flight.destination_city}
                        </p>
                        <p className="text-sm text-gray-600 font-medium tabular mt-1">
                          {formatFlightDate(flight.departure_date)} ·{' '}
                          {formatTime(flight.scheduled_departure)} –{' '}
                          {formatTime(flight.scheduled_arrival)} ·{' '}
                          {formatDuration(flight.duration_minutes)}
                        </p>
                        {flight.seats_available <= 10 && (
                          <p className="text-sm text-warning font-semibold mt-1">
                            {flight.seats_available} seats remain
                          </p>
                        )}
                      </div>

                      <div className="flex flex-row sm:flex-col items-center sm:items-end justify-between w-full sm:w-auto sm:ml-6 border-t sm:border-t-0 sm:border-l border-gray-100 pt-4 sm:pt-0 sm:pl-6 gap-4">
                        <div className="text-right">
                          <div className="text-label uppercase tracking-[0.06em] text-gray-500 font-bold">
                            From
                          </div>
                          <span className="text-section font-bold text-signal tabular">
                            {cheapest === null ? '—' : formatFare(cheapest)}
                          </span>
                        </div>
                        <button
                          onClick={() => setBookingFlight(flight)}
                          disabled={flight.seats_available === 0}
                          className="bg-signal text-white px-6 py-2 rounded-full font-semibold hover:opacity-90 transition-opacity shadow-md disabled:opacity-50"
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
            <div className="bg-white rounded-[12px] shadow-card p-6 border-t-4 border-secondary sticky top-6">
              <h2 className="text-xl font-bold text-primary mb-6">My itineraries</h2>
              {bookings.length === 0 ? (
                <p className="text-gray-600 text-sm text-center py-8">
                  You haven't booked any flights yet.
                </p>
              ) : (
                <ul className="space-y-4">
                  {bookings.map((booking) => (
                    <li
                      key={booking.id}
                      className="bg-accent rounded-[6px] p-4 border border-gray-100"
                    >
                      <div className="flex justify-between items-start mb-2 gap-2">
                        <div>
                          <p className="font-bold text-primary tabular">
                            {booking.origin_iata} → {booking.destination_iata}
                          </p>
                          <p className="text-xs text-gray-600 mt-1 tabular">
                            {booking.flight_number} ·{' '}
                            {formatFlightDate(booking.scheduled_departure)}
                          </p>
                        </div>
                        <span
                          className={`text-xs font-bold px-2 py-1 rounded whitespace-nowrap ${
                            booking.status === 'cancelled'
                              ? 'bg-red-50 text-danger'
                              : 'bg-green-50 text-success'
                          }`}
                        >
                          {booking.status === 'cancelled' ? 'Cancelled' : 'Confirmed'}
                        </span>
                      </div>
                      <p className="text-xs text-gray-600 tabular">
                        Ref <strong>{booking.booking_reference}</strong> ·{' '}
                        {booking.fare_class_code}
                        {booking.seat_numbers.length > 0 &&
                          ` · seat ${booking.seat_numbers.join(', ')}`}
                      </p>
                      <p className="text-xs text-gray-600 tabular mt-1">
                        {formatFare(booking.amount_eur)} · card ending {booking.card_last4}
                      </p>
                      {booking.status !== 'cancelled' && (
                        <div className="mt-3 pt-3 border-t border-gray-200 text-right">
                          <button
                            onClick={() => cancelBooking(booking)}
                            className="text-danger hover:underline text-sm font-semibold"
                          >
                            Cancel booking
                          </button>
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </section>
        </div>
      </div>

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
