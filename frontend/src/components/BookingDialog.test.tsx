import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import BookingDialog from './BookingDialog';
import type { Flight } from '../types';

const FLIGHT: Flight = {
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
  fares: [
    {
      fare_class_code: 'LIGHT',
      name: 'Light',
      price_eur: '129.00',
      seats_available: 220,
      cabin_bag_included: true,
      checked_bag_included: false,
      changeable: false,
      refundable: false,
    },
    {
      fare_class_code: 'FLEX',
      name: 'Flex',
      price_eur: '270.90',
      seats_available: 220,
      cabin_bag_included: true,
      checked_bag_included: true,
      changeable: true,
      refundable: true,
    },
  ],
};

const setup = (overrides: Partial<React.ComponentProps<typeof BookingDialog>> = {}) => {
  const onConfirm = vi.fn().mockResolvedValue(undefined);
  const onCancel = vi.fn();
  render(
    <BookingDialog
      flight={FLIGHT}
      defaultName="Ada Papadopoulou"
      defaultPassport="AB123456"
      onConfirm={onConfirm}
      onCancel={onCancel}
      {...overrides}
    />,
  );
  return { onConfirm, onCancel };
};

describe('BookingDialog', () => {
  describe('payment', () => {
    it('has no card field at all', async () => {
      setup();
      // DEF-003, resolved in full. A demonstration with no payment provider
      // must not present anything that looks like a card input, because it
      // will eventually be given a real card.
      expect(screen.queryByLabelText(/card/i)).not.toBeInTheDocument();
      expect(screen.queryByPlaceholderText(/4242/)).not.toBeInTheDocument();
      expect(document.querySelector('[autocomplete="cc-number"]')).toBeNull();
    });

    it('says plainly that nothing is charged', () => {
      setup();
      expect(screen.getByText(/no payment is taken/i)).toBeInTheDocument();
      expect(screen.getByText(/do not enter real payment information/i)).toBeInTheDocument();
    });

    it('never sends a card field to the caller', async () => {
      const { onConfirm } = setup();
      await userEvent.click(screen.getByRole('button', { name: /confirm/i }));
      await waitFor(() => expect(onConfirm).toHaveBeenCalled());
      expect(onConfirm.mock.calls[0][0]).not.toHaveProperty('credit_card');
    });
  });

  describe('fares', () => {
    it('offers every fare with its price', () => {
      setup();
      expect(screen.getByRole('radio', { name: /light/i })).toBeInTheDocument();
      expect(screen.getByRole('radio', { name: /flex/i })).toBeInTheDocument();
      // Each price appears twice — once on its fare, once as the total when
      // that fare is selected — so assert within the radio itself.
      expect(screen.getByRole('radio', { name: /129[.,]00/ })).toBeInTheDocument();
      expect(screen.getByRole('radio', { name: /270[.,]90/ })).toBeInTheDocument();
    });

    it('states what each fare includes', () => {
      setup();
      expect(screen.getByRole('radio', { name: /refundable/i })).toBeInTheDocument();
    });

    it('preselects the first fare', () => {
      setup();
      expect(screen.getByRole('radio', { name: /light/i })).toBeChecked();
    });

    it('updates the total when a different fare is chosen', async () => {
      setup();
      await userEvent.click(screen.getByRole('radio', { name: /flex/i }));
      const total = screen.getByText(/270[.,]90/, { selector: 'p' });
      expect(total).toBeInTheDocument();
    });

    it('submits the chosen fare', async () => {
      const { onConfirm } = setup();
      await userEvent.click(screen.getByRole('radio', { name: /flex/i }));
      await userEvent.click(screen.getByRole('button', { name: /confirm/i }));
      await waitFor(() =>
        expect(onConfirm).toHaveBeenCalledWith(
          expect.objectContaining({ fare_class_code: 'FLEX' }),
        ),
      );
    });
  });

  describe('passenger details', () => {
    it('pre-fills from the account', () => {
      setup();
      expect(screen.getByLabelText(/passenger name/i)).toHaveValue('Ada Papadopoulou');
      expect(screen.getByLabelText(/passport number/i)).toHaveValue('AB123456');
    });

    it('refuses an empty name, without calling the API', async () => {
      const { onConfirm } = setup({ defaultName: '' });
      await userEvent.click(screen.getByRole('button', { name: /confirm/i }));
      expect(await screen.findByRole('alert')).toHaveTextContent(/passenger name/i);
      expect(onConfirm).not.toHaveBeenCalled();
    });

    it('refuses a passport number that is too short', async () => {
      const { onConfirm } = setup({ defaultPassport: 'AB' });
      await userEvent.click(screen.getByRole('button', { name: /confirm/i }));
      expect(await screen.findByRole('alert')).toHaveTextContent(/passport number/i);
      expect(onConfirm).not.toHaveBeenCalled();
    });

    it('uppercases the passport number', async () => {
      const { onConfirm } = setup({ defaultPassport: '' });
      await userEvent.type(screen.getByLabelText(/passport number/i), 'ab123456');
      await userEvent.click(screen.getByRole('button', { name: /confirm/i }));
      await waitFor(() =>
        expect(onConfirm).toHaveBeenCalledWith(
          expect.objectContaining({ passenger_passport: 'AB123456' }),
        ),
      );
    });

    it('omits the seat when none is requested', async () => {
      const { onConfirm } = setup();
      await userEvent.click(screen.getByRole('button', { name: /confirm/i }));
      await waitFor(() => expect(onConfirm).toHaveBeenCalled());
      expect(onConfirm.mock.calls[0][0]).not.toHaveProperty('seat_number');
    });

    it('sends a requested seat, uppercased', async () => {
      const { onConfirm } = setup();
      await userEvent.type(screen.getByLabelText(/seat/i), '12a');
      await userEvent.click(screen.getByRole('button', { name: /confirm/i }));
      await waitFor(() =>
        expect(onConfirm).toHaveBeenCalledWith(
          expect.objectContaining({ seat_number: '12A' }),
        ),
      );
    });
  });

  describe('failure', () => {
    it('surfaces the server message', async () => {
      const onConfirm = vi
        .fn()
        .mockRejectedValue({ response: { data: { detail: 'Seat 12A is not available' } } });
      render(
        <BookingDialog
          flight={FLIGHT}
          defaultName="Ada"
          defaultPassport="AB123456"
          onConfirm={onConfirm}
          onCancel={vi.fn()}
        />,
      );
      await userEvent.click(screen.getByRole('button', { name: /confirm/i }));
      expect(await screen.findByRole('alert')).toHaveTextContent('Seat 12A is not available');
    });

    it('states the money position when the server says nothing useful', async () => {
      const onConfirm = vi.fn().mockRejectedValue(new Error('network'));
      render(
        <BookingDialog
          flight={FLIGHT}
          defaultName="Ada"
          defaultPassport="AB123456"
          onConfirm={onConfirm}
          onCancel={vi.fn()}
        />,
      );
      await userEvent.click(screen.getByRole('button', { name: /confirm/i }));
      // "Nothing has been charged" is the sentence people look for.
      expect(await screen.findByRole('alert')).toHaveTextContent(/nothing has been charged/i);
    });
  });

  describe('accessibility and dismissal', () => {
    it('is a labelled modal dialog', () => {
      setup();
      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-modal', 'true');
      expect(dialog).toHaveAccessibleName();
    });

    it('moves focus into the dialog when it opens', async () => {
      setup();
      await waitFor(() =>
        expect(screen.getByLabelText(/passenger name/i)).toHaveFocus(),
      );
    });

    it('closes on Escape', async () => {
      const { onCancel } = setup();
      await userEvent.keyboard('{Escape}');
      expect(onCancel).toHaveBeenCalled();
    });

    it('closes when the backdrop is clicked', async () => {
      const { onCancel } = setup();
      await userEvent.click(screen.getByRole('dialog').parentElement!);
      expect(onCancel).toHaveBeenCalled();
    });

    it('does not close when the dialog itself is clicked', async () => {
      const { onCancel } = setup();
      await userEvent.click(screen.getByRole('dialog'));
      expect(onCancel).not.toHaveBeenCalled();
    });

    it('offers exactly one primary action', () => {
      setup();
      // VANE allows one primary action per view; Confirm is it.
      const primaries = document.querySelectorAll('.ds-action--primary');
      expect(primaries).toHaveLength(1);
      expect(primaries[0]).toHaveTextContent(/confirm/i);
    });
  });
});
