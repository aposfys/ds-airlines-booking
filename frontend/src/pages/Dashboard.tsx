import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import BookingDialog from '../components/BookingDialog';
import { useAuth } from '../context/AuthContext';
import { formatFare, formatFlightDate } from '../lib/format';
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

  const [departure, setDeparture] = useState('');
  const [destination, setDestination] = useState('');

  const loadBookings = useCallback(async () => {
    const { data } = await api.get<Booking[]>('/bookings');
    setBookings(data);
  }, []);

  // Search runs on the server. The previous implementation fetched a page of
  // flights once and filtered that array in the browser, so anything outside
  // the first page was simply invisible to search.
  const loadFlights = useCallback(async () => {
    const params: Record<string, string> = {};
    if (departure.trim()) params.departure = departure.trim();
    if (destination.trim()) params.destination = destination.trim();
    const { data } = await api.get<Flight[]>('/flights', { params });
    setFlights(data);
  }, [departure, destination]);

  useEffect(() => {
    if (!user) return;
    Promise.all([loadFlights(), loadBookings()])
      .catch(() => setNotice({ tone: 'error', text: 'We could not load your flights. Try again shortly.' }))
      .finally(() => setLoading(false));
    // Only on mount; searching is driven by the debounce below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  useEffect(() => {
    if (!user) return;
    const timer = setTimeout(() => {
      loadFlights().catch(() =>
        setNotice({ tone: 'error', text: 'Search is unavailable right now.' }),
      );
    }, 300);
    return () => clearTimeout(timer);
  }, [departure, destination, user, loadFlights]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const confirmBooking = async (details: {
    full_name: string;
    passport_num: string;
    credit_card: string;
  }) => {
    if (!bookingFlight) return;
    await api.post('/bookings', { flight_code: bookingFlight.unique_code, ...details });
    setBookingFlight(null);
    // State is refreshed in place. The previous version called
    // window.location.reload() after every action, which threw away the
    // session's scroll position and re-ran the whole bootstrap.
    await Promise.all([loadFlights(), loadBookings()]);
    setNotice({ tone: 'success', text: 'Booked. Your itinerary is updated below.' });
  };

  const cancelBooking = async (booking: Booking) => {
    if (!confirm(`Cancel your flight to ${booking.destination}? This cannot be undone.`)) {
      return;
    }
    try {
      await api.delete(`/bookings/${booking._id}`);
      await Promise.all([loadFlights(), loadBookings()]);
      setNotice({ tone: 'success', text: 'Your booking has been cancelled.' });
    } catch {
      setNotice({ tone: 'error', text: 'We could not cancel that booking. Nothing has changed.' });
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
              <span className="text-sm font-medium">Welcome, {user?.fullname}</span>
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
                <label
                  htmlFor="from"
                  className="block text-label font-bold text-gray-500 uppercase tracking-[0.06em] mb-1"
                >
                  From
                </label>
                <input
                  id="from"
                  type="text"
                  placeholder="Departure city"
                  className="w-full text-lg border-b-2 border-gray-200 focus:border-secondary focus:outline-none py-2 transition-colors text-primary font-semibold placeholder-gray-400"
                  value={departure}
                  onChange={(e) => setDeparture(e.target.value)}
                />
              </div>
              <div>
                <label
                  htmlFor="to"
                  className="block text-label font-bold text-gray-500 uppercase tracking-[0.06em] mb-1"
                >
                  To
                </label>
                <input
                  id="to"
                  type="text"
                  placeholder="Destination city"
                  className="w-full text-lg border-b-2 border-gray-200 focus:border-secondary focus:outline-none py-2 transition-colors text-primary font-semibold placeholder-gray-400"
                  value={destination}
                  onChange={(e) => setDestination(e.target.value)}
                />
              </div>
            </div>
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
                No flights match that search. Try a different city.
              </div>
            ) : (
              <ul className="space-y-4">
                {flights.map((flight) => (
                  <li
                    key={flight.unique_code}
                    className="bg-white rounded-[12px] shadow-card p-6 flex flex-col sm:flex-row justify-between items-center hover:shadow-float transition-shadow border border-gray-100"
                  >
                    <div className="flex-1 w-full mb-4 sm:mb-0">
                      <div className="flex items-center gap-4 mb-2">
                        <span className="text-xl font-bold text-primary">{flight.departure}</span>
                        <span aria-hidden="true" className="text-secondary">
                          →
                        </span>
                        <span className="text-xl font-bold text-primary">
                          {flight.destination}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 font-medium tabular">
                        {formatFlightDate(flight.date)} · {flight.time} · {flight.duration}
                      </p>
                      {flight.availability <= 10 && (
                        <p className="text-sm text-warning font-semibold mt-1">
                          {flight.availability} seats remain at this fare
                        </p>
                      )}
                    </div>

                    <div className="flex flex-row sm:flex-col items-center sm:items-end justify-between w-full sm:w-auto sm:ml-6 border-t sm:border-t-0 sm:border-l border-gray-100 pt-4 sm:pt-0 sm:pl-6 gap-4">
                      <span className="text-section font-bold text-signal tabular">
                        {formatFare(flight.cost)}
                      </span>
                      <button
                        onClick={() => setBookingFlight(flight)}
                        disabled={flight.availability === 0}
                        className="bg-signal text-white px-6 py-2 rounded-full font-semibold hover:opacity-90 transition-opacity shadow-md disabled:opacity-50"
                      >
                        {flight.availability === 0 ? 'Full' : 'Select'}
                      </button>
                    </div>
                  </li>
                ))}
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
                      key={booking._id}
                      className="bg-accent rounded-[6px] p-4 border border-gray-100"
                    >
                      <div className="flex justify-between items-start mb-2 gap-2">
                        <div>
                          <p className="font-bold text-primary">
                            {booking.departure} → {booking.destination}
                          </p>
                          <p className="text-xs text-gray-600 mt-1 tabular">
                            {formatFlightDate(booking.flight_date)}
                          </p>
                        </div>
                        <span className="bg-green-50 text-success text-xs font-bold px-2 py-1 rounded whitespace-nowrap">
                          Confirmed
                        </span>
                      </div>
                      <p className="text-xs text-gray-600 tabular">
                        {formatFare(booking.cost)} · card ending {booking.card_last4}
                      </p>
                      <div className="mt-3 pt-3 border-t border-gray-200 text-right">
                        <button
                          onClick={() => cancelBooking(booking)}
                          className="text-danger hover:underline text-sm font-semibold"
                        >
                          Cancel booking
                        </button>
                      </div>
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
          defaultName={user?.fullname ?? ''}
          defaultPassport={user?.passport_num ?? ''}
          onCancel={() => setBookingFlight(null)}
          onConfirm={confirmBooking}
        />
      )}
    </div>
  );
};

export default Dashboard;
