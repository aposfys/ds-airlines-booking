import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import api from '../api';
import { AuthProvider } from '../context/AuthContext';
import { ThemeProvider } from '../context/ThemeContext';
import Dashboard from './Dashboard';
import type { Booking, Flight } from '../types';

vi.mock('../api', () => ({
  default: { get: vi.fn(), post: vi.fn(), delete: vi.fn() },
}));

const PROFILE = {
  id: 'u1',
  email: 'ada@example.com',
  username: 'ada',
  full_name: 'Ada Papadopoulou',
  passport_number: 'AB123456',
  is_admin: false,
  is_active: true,
};

const fare = (code: string, name: string, price: string, refundable = false) => ({
  fare_class_code: code,
  name,
  price_eur: price,
  seats_available: 220,
  cabin_bag_included: true,
  checked_bag_included: refundable,
  changeable: refundable,
  refundable,
});

const FLIGHTS: Flight[] = [
  {
    id: 'f1',
    flight_number: 'DS1040',
    origin_iata: 'ATH',
    origin_city: 'Athens',
    destination_iata: 'LHR',
    destination_city: 'London',
    departure_date: '2026-08-15',
    scheduled_departure: '2026-08-15T10:30:00Z',
    scheduled_arrival: '2026-08-15T14:15:00Z',
    duration_minutes: 225,
    aircraft_type: 'Airbus A321neo',
    seats_available: 220,
    fares: [fare('LIGHT', 'Light', '129.00'), fare('FLEX', 'Flex', '270.90', true)],
  },
  {
    id: 'f2',
    flight_number: 'DS3120',
    origin_iata: 'SKG',
    origin_city: 'Thessaloniki',
    destination_iata: 'FRA',
    destination_city: 'Frankfurt',
    departure_date: '2026-08-16',
    scheduled_departure: '2026-08-16T14:15:00Z',
    scheduled_arrival: '2026-08-16T16:55:00Z',
    duration_minutes: 160,
    aircraft_type: 'Airbus A321neo',
    seats_available: 4,
    fares: [fare('LIGHT', 'Light', '155.00')],
  },
];

const BOOKING: Booking = {
  id: 'b1',
  booking_reference: 'N8LFVH',
  status: 'confirmed',
  flight_number: 'DS1040',
  origin_iata: 'ATH',
  destination_iata: 'LHR',
  scheduled_departure: '2026-08-15T10:30:00Z',
  fare_class_code: 'FLEX',
  passenger_full_name: 'Ada Papadopoulou',
  seat_numbers: ['12A'],
  card_last4: null,
  amount_eur: '270.90',
  created_at: '2026-08-02T10:00:00Z',
};

const mockGet = (flights: Flight[] = FLIGHTS, bookings: Booking[] = []) => {
  vi.mocked(api.get).mockImplementation(((url: string) => {
    if (url === '/auth/me') return Promise.resolve({ data: PROFILE });
    if (url === '/flights') return Promise.resolve({ data: flights });
    if (url === '/bookings') return Promise.resolve({ data: bookings });
    return Promise.reject(new Error(`unexpected ${url}`));
  }) as never);
};

const renderDashboard = async () => {
  localStorage.setItem('token', 'a.b.c');
  render(
    <MemoryRouter>
      <ThemeProvider>
        <AuthProvider>
          <Dashboard />
        </AuthProvider>
      </ThemeProvider>
    </MemoryRouter>,
  );
  await screen.findByRole('heading', { name: /where to next/i });
};

describe('Dashboard', () => {
  beforeEach(() => {
    vi.mocked(api.get).mockReset();
    vi.mocked(api.post).mockReset();
    vi.mocked(api.delete).mockReset();
  });

  describe('flight list', () => {
    it('shows each flight with route, number and duration', async () => {
      mockGet();
      await renderDashboard();

      expect(await screen.findByText('ATH → LHR')).toBeInTheDocument();
      expect(screen.getByText('DS1040')).toBeInTheDocument();
      expect(screen.getByText(/3h 45m/)).toBeInTheDocument();
      expect(screen.getByText('Athens to London')).toBeInTheDocument();
    });

    it('shows the cheapest fare as the headline price, in EUR', async () => {
      mockGet();
      await renderDashboard();
      // Light 129.00 is cheaper than Flex 270.90.
      expect(await screen.findByText(/129[.,]00/)).toBeInTheDocument();
      expect(screen.queryByText(/\$/)).not.toBeInTheDocument();
    });

    it('warns only when seats are genuinely low', async () => {
      mockGet();
      await renderDashboard();
      expect(await screen.findByText(/4 seats remain/i)).toBeInTheDocument();
      expect(screen.queryByText(/220 seats remain/i)).not.toBeInTheDocument();
    });

    it('uses no primary action in the list', async () => {
      mockGet();
      await renderDashboard();
      await screen.findByText('ATH → LHR');
      // VANE allows one primary per view; N flights must not mean N of them.
      expect(document.querySelectorAll('.ds-action--primary')).toHaveLength(0);
    });

    it('says so when nothing matches', async () => {
      mockGet([]);
      await renderDashboard();
      expect(await screen.findByText(/no flights match that search/i)).toBeInTheDocument();
    });
  });

  describe('search', () => {
    it('sends complete IATA codes to the API', async () => {
      mockGet();
      await renderDashboard();

      await userEvent.type(screen.getByLabelText(/^from$/i), 'ATH');
      await waitFor(
        () =>
          expect(api.get).toHaveBeenCalledWith('/flights', {
            params: { origin: 'ATH' },
          }),
        { timeout: 2000 },
      );
    });

    it('does not query on a partial code', async () => {
      mockGet();
      await renderDashboard();
      vi.mocked(api.get).mockClear();

      await userEvent.type(screen.getByLabelText(/^from$/i), 'AT');
      await new Promise((r) => setTimeout(r, 500));

      const originParams = vi
        .mocked(api.get)
        .mock.calls.filter(([url]) => url === '/flights')
        .map(([, config]) => (config as { params?: Record<string, string> })?.params?.origin);
      expect(originParams.every((value) => value === undefined)).toBe(true);
    });

    it('uppercases what the passenger types', async () => {
      mockGet();
      await renderDashboard();

      const from = screen.getByLabelText(/^from$/i);
      await userEvent.type(from, 'ath');
      expect(from).toHaveValue('ATH');
    });
  });

  describe('itineraries', () => {
    it('shows an empty state before anything is booked', async () => {
      mockGet();
      await renderDashboard();
      expect(await screen.findByText(/have not booked any flights/i)).toBeInTheDocument();
    });

    it('shows reference, fare, seat and amount — and no card digits', async () => {
      mockGet(FLIGHTS, [BOOKING]);
      await renderDashboard();

      const panel = (await screen.findByText('N8LFVH')).closest('li')!;
      expect(within(panel).getByText(/FLEX · seat 12A/)).toBeInTheDocument();
      expect(within(panel).getByText(/270[.,]90/)).toBeInTheDocument();
      expect(within(panel).getByText(/confirmed/i)).toBeInTheDocument();
      expect(panel.textContent).not.toMatch(/card/i);
    });

    it('offers no cancel control on an already-cancelled booking', async () => {
      mockGet(FLIGHTS, [{ ...BOOKING, status: 'cancelled' }]);
      await renderDashboard();

      const panel = (await screen.findByText('N8LFVH')).closest('li')!;
      expect(within(panel).getByText(/cancelled/i)).toBeInTheDocument();
      expect(within(panel).queryByRole('button', { name: /cancel booking/i })).toBeNull();
    });
  });

  describe('booking', () => {
    it('books the selected flight and reports the reference', async () => {
      mockGet();
      vi.mocked(api.post).mockResolvedValue({ data: BOOKING });
      await renderDashboard();

      await userEvent.click((await screen.findAllByRole('button', { name: /select/i }))[0]);
      await userEvent.click(await screen.findByRole('button', { name: /confirm/i }));

      await waitFor(() =>
        expect(api.post).toHaveBeenCalledWith(
          '/bookings',
          expect.objectContaining({ flight_id: 'f1', fare_class_code: 'LIGHT' }),
        ),
      );
      expect(await screen.findByRole('status')).toHaveTextContent('N8LFVH');
    });

    it('refreshes both lists after booking, so seat counts are current', async () => {
      mockGet();
      vi.mocked(api.post).mockResolvedValue({ data: BOOKING });
      await renderDashboard();
      vi.mocked(api.get).mockClear();

      await userEvent.click((await screen.findAllByRole('button', { name: /select/i }))[0]);
      await userEvent.click(await screen.findByRole('button', { name: /confirm/i }));

      await waitFor(() => {
        const urls = vi.mocked(api.get).mock.calls.map(([u]) => u);
        expect(urls).toContain('/flights');
        expect(urls).toContain('/bookings');
      });
    });

    it('closes the dialog on cancel without booking', async () => {
      mockGet();
      await renderDashboard();

      await userEvent.click((await screen.findAllByRole('button', { name: /select/i }))[0]);
      await userEvent.click(await screen.findByRole('button', { name: /^cancel$/i }));

      await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
      expect(api.post).not.toHaveBeenCalled();
    });
  });

  describe('cancellation', () => {
    it('cancels after confirmation and reports it', async () => {
      mockGet(FLIGHTS, [BOOKING]);
      vi.mocked(api.delete).mockResolvedValue({ data: null });
      vi.stubGlobal('confirm', vi.fn().mockReturnValue(true));
      await renderDashboard();

      await userEvent.click(await screen.findByRole('button', { name: /cancel booking/i }));

      await waitFor(() => expect(api.delete).toHaveBeenCalledWith('/bookings/b1'));
      expect(await screen.findByRole('status')).toHaveTextContent(/has been cancelled/i);
    });

    it('does nothing when the passenger declines the confirmation', async () => {
      mockGet(FLIGHTS, [BOOKING]);
      vi.stubGlobal('confirm', vi.fn().mockReturnValue(false));
      await renderDashboard();

      await userEvent.click(await screen.findByRole('button', { name: /cancel booking/i }));
      expect(api.delete).not.toHaveBeenCalled();
    });

    it('states that nothing changed when cancelling fails', async () => {
      mockGet(FLIGHTS, [BOOKING]);
      vi.mocked(api.delete).mockRejectedValue(new Error('409'));
      vi.stubGlobal('confirm', vi.fn().mockReturnValue(true));
      await renderDashboard();

      await userEvent.click(await screen.findByRole('button', { name: /cancel booking/i }));
      expect(await screen.findByRole('status')).toHaveTextContent(/nothing has changed/i);
    });
  });

  it('offers a route past the header for keyboard and screen-reader users', async () => {
    mockGet();
    await renderDashboard();
    expect(screen.getByRole('link', { name: /skip to flights/i })).toHaveAttribute(
      'href',
      '#flights',
    );
  });
});
