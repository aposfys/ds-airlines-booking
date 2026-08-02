# Security

DS Airlines is a **demonstration project**. It is not deployed, it serves no
real passengers, and it must never be treated as a live booking system.

## It takes no payments

There is no payment provider behind this application and no card field in the
interface. The API refuses payment details outright — a booking request
carrying `credit_card` receives `422`, rather than having the field silently
ignored.

**Do not enter real payment information anywhere in this application.**

This was not always true, and the history is documented rather than hidden:

- The original code stored **full card numbers in cleartext**, in the same
  record as the passenger's passport number
  ([DEF-003](docs/analysis/current-state-assessment.md)).
- Phase 0 stopped storing them — validated, reduced to four digits, discarded.
- Phase 1 stopped accepting them. A field that looks like an ordinary card
  input will eventually be given a real card by someone who did not read the
  page, and the safest cardholder data is the kind that never arrives.

## Running it safely

- **`SECRET_KEY` is required.** The application refuses to start without one,
  rejects known placeholder values, and rejects anything under 32 characters.
  The original code fell back to a placeholder committed to this repository.
- **Seeding is opt-in and has no default credentials.** `SEED_ON_STARTUP`
  must be set, and both `SEED_ADMIN_EMAIL` and `SEED_ADMIN_PASSWORD` must be
  supplied or the administrator is not created. The original code seeded an
  administrator with the password `admin` on every startup, production
  included.
- **The database port is not published** by `docker-compose.yml`. The
  development override publishes it for convenience; do not use that override
  anywhere but a local machine.
- **`CORS_ORIGINS` must be set explicitly** for any real deployment. The
  default permits localhost only.

If you fork this and deploy it, read
[the assessment](docs/analysis/current-state-assessment.md) first — it lists
what is fixed, what is deferred, and what is accepted.

## Known limitations

Stated plainly rather than implied:

- **No rate limiting.** Login and registration accept unlimited attempts.
- **No refresh tokens.** Access tokens last 30 minutes and cannot be revoked
  before expiry, though privilege and account status are read from the
  database on every request, so deactivation takes effect immediately.
- **No audit log.** Administrative actions are not recorded.
- **No dependency or container scanning** in CI.
- **Passport numbers are stored in plaintext.** They are personal data under
  GDPR and would need encryption at rest in anything real.

## Reporting

If you find a vulnerability, open an issue at
https://github.com/aposfys/ds-airlines-booking/issues — this is a demonstration
project, so there is no private disclosure process and nothing here is at
risk in production.
