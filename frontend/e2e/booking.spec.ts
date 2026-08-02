import { expect, test, type Page } from '@playwright/test';

/**
 * The passenger journey, end to end: register, sign in, search, book, cancel.
 *
 * Each run registers a fresh account so the suite is idempotent against a
 * database that keeps its data between runs.
 */

const unique = () => Math.random().toString(36).slice(2, 10);

async function registerAndSignIn(page: Page) {
  const username = `e2e${unique()}`;
  const password = 'password123';

  await page.goto('/register');
  await page.getByLabel('Full name').fill('Ada Papadopoulou');
  await page.getByLabel('Username').fill(username);
  await page.getByLabel('Email address').fill(`${username}@example.com`);
  await page.getByLabel('Passport number').fill('AB123456');
  await page.getByLabel('Password').fill(password);
  await page.getByRole('button', { name: 'Create account' }).click();

  await expect(page).toHaveURL(/\/login/);

  await page.getByLabel('Username').fill(username);
  await page.getByLabel('Password').fill(password);
  await page.getByRole('button', { name: 'Sign in' }).click();

  await expect(page).toHaveURL(/\/dashboard/);
  return { username, password };
}

test.describe('the passenger journey', () => {
  test('register, sign in, book a seat, then cancel it', async ({ page }) => {
    await registerAndSignIn(page);

    // The dashboard greets by real name, not the literal "User" (DEF-016).
    await expect(page.getByText('Ada Papadopoulou')).toBeVisible();

    const firstFlight = page.getByRole('listitem').first();
    await expect(firstFlight).toBeVisible();

    await firstFlight.getByRole('button', { name: 'Select' }).click();
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();

    // The passenger's own details are pre-filled from the account.
    await expect(dialog.getByLabel('Passenger name')).toHaveValue('Ada Papadopoulou');
    await expect(dialog.getByLabel('Passport number')).toHaveValue('AB123456');

    await dialog.getByRole('button', { name: 'Confirm' }).click();

    const notice = page.getByRole('status');
    await expect(notice).toContainText('Booked. Your reference is');

    const reference = (await notice.textContent())!.match(/([A-Z0-9]{6})/)![1];
    expect(reference).toHaveLength(6);
    // I, O, 0 and 1 are excluded: a reference gets read aloud and written down.
    expect(reference).not.toMatch(/[IO01]/);

    const itinerary = page.getByRole('listitem').filter({ hasText: reference });
    await expect(itinerary).toBeVisible();
    await expect(itinerary).toContainText('Confirmed');

    page.once('dialog', (d) => d.accept());
    await itinerary.getByRole('button', { name: 'Cancel booking' }).click();

    await expect(page.getByRole('status')).toContainText('has been cancelled');
    await expect(
      page.getByRole('listitem').filter({ hasText: reference }),
    ).toContainText('Cancelled');
  });

  test('a seat already taken cannot be taken again', async ({ page }) => {
    await registerAndSignIn(page);

    // Let the server assign a seat, then try to claim that exact one. Picking
    // a seat number up front is not safe: this database keeps its data
    // between runs, so any given seat may already be sold and the test would
    // fail on its own setup rather than on what it is checking.
    await page.getByRole('listitem').first().getByRole('button', { name: 'Select' }).click();
    await page.getByRole('dialog').getByRole('button', { name: 'Confirm' }).click();
    await expect(page.getByRole('status')).toContainText('Booked');

    const reference = (await page.getByRole('status').textContent())!.match(
      /([A-Z0-9]{6})/,
    )![1];
    const itinerary = page.getByRole('listitem').filter({ hasText: reference });
    const seat = (await itinerary.textContent())!.match(/seat ([0-9]{1,2}[A-F])/)![1];

    await page.getByRole('listitem').first().getByRole('button', { name: 'Select' }).click();
    const dialog = page.getByRole('dialog');
    await dialog.getByLabel(/Seat/).fill(seat);
    await dialog.getByRole('button', { name: 'Confirm' }).click();

    // The seat lock refuses the second claim; the dialog stays open and says so.
    await expect(dialog.getByRole('alert')).toContainText(`Seat ${seat} is not available`);
  });

  test('the fare a passenger picks is the fare they are charged', async ({ page }) => {
    await registerAndSignIn(page);

    await page.getByRole('listitem').first().getByRole('button', { name: 'Select' }).click();
    const dialog = page.getByRole('dialog');

    const flex = dialog.getByRole('radio', { name: /Flex/ });
    await flex.click();
    const total = await dialog.locator('p').filter({ hasText: /€/ }).last().textContent();

    await dialog.getByRole('button', { name: 'Confirm' }).click();
    await expect(page.getByRole('status')).toContainText('Booked');

    const reference = (await page.getByRole('status').textContent())!.match(
      /([A-Z0-9]{6})/,
    )![1];
    const itinerary = page.getByRole('listitem').filter({ hasText: reference });
    await expect(itinerary).toContainText('FLEX');
    await expect(itinerary).toContainText(total!.replace(/\s/g, ' ').trim());
  });
});

test.describe('payment', () => {
  test('the booking form offers no way to enter a card', async ({ page }) => {
    await registerAndSignIn(page);
    await page.getByRole('listitem').first().getByRole('button', { name: 'Select' }).click();

    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();

    // DEF-003, resolved in full: a demonstration with no payment provider must
    // present nothing that could receive a real card.
    await expect(dialog.locator('[autocomplete="cc-number"]')).toHaveCount(0);
    await expect(dialog.getByLabel(/card/i)).toHaveCount(0);
    await expect(dialog.getByText('No payment is taken')).toBeVisible();
  });

  test('the API refuses a card number outright', async ({ page, request }) => {
    const { username, password } = await registerAndSignIn(page);

    const login = await request.post('http://localhost:8000/api/auth/login', {
      data: { username, password },
    });
    const token = (await login.json()).access_token;

    const flights = await request.get('http://localhost:8000/api/flights/');
    const flightId = (await flights.json())[0].id;

    const response = await request.post('http://localhost:8000/api/bookings/', {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        flight_id: flightId,
        fare_class_code: 'LIGHT',
        passenger_full_name: 'Ada Papadopoulou',
        passenger_passport: 'AB123456',
        credit_card: '4242424242424242',
      },
    });

    // Refused, not silently ignored — otherwise a client could keep posting
    // live card numbers to a server that merely chose not to read them.
    expect(response.status()).toBe(422);
  });
});
