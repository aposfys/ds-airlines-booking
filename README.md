# DS Airlines · Delos Skyways

A flight booking platform for a fictional Greek short-haul carrier — built as
a business, not just a codebase. Brand, product analysis, user stories and
test strategy are first-class artefacts here, alongside the API and the
interface.

**Stack:** FastAPI · MongoDB (PostgreSQL from Phase 1) · React 19 · TypeScript
· Tailwind v4 · Docker

---

## Why this repository exists

It began as an MSc distributed-systems assignment: a Flask app that could
list flights and take a booking. Restarting it as a product meant asking the
questions coursework never does — who flies this airline, what does it
promise, what happens when a payment fails, and how would anyone know if it
broke.

The most useful document here is not the API reference. It is the
[**current-state assessment**](docs/analysis/current-state-assessment.md):
an audit of the original code recording all 30 defects found, what each one
would have cost the business, and where it was resolved.

Four of them were Critical, and they are worth stating plainly:

- **The entire admin surface was unreachable.** Tokens never carried the
  `is_admin` claim that every authorisation check read, so flight creation,
  repricing and withdrawal returned 403 to everyone — including the
  administrator the app seeded for itself. For an airline that is revenue
  management, gone.
- **Full card numbers were stored in cleartext**, in the same record as the
  passenger's passport number.
- **Every deployment shipped the same known admin password**, hardcoded, next
  to a signing key committed to this repository.
- **`docker-compose up --build` could not build**, because the frontend image
  pinned Node 18 against a toolchain requiring Node 20+.

The previous README called this "production-ready". Recording why that was
wrong is the point of the exercise.

---

## Documentation

| | |
|---|---|
| [Brand book](docs/brand/brandbook.md) | Positioning, palette, typography, voice and tone. Its tokens are wired into `frontend/src/index.css`, and [`contrast_check.py`](docs/brand/contrast_check.py) fails CI if a colour drops below WCAG 2.2 AA |
| [Current-state assessment](docs/analysis/current-state-assessment.md) | The full defect register, with business impact and resolution |
| Product & user stories | Phase 1 |
| [Test strategy](docs/qa/test-strategy.md) | Layers, entry/exit criteria, 27 mapped automated cases, 7 manual cases, and what is not covered yet |

---

## Roadmap

Each phase leaves the repository in a coherent, runnable state, and lands on
its own branch via pull request.

| Phase | Scope | Status |
|---|---|---|
| **0 · Foundation** | Brand identity, defect register, critical fixes, CI, repo hygiene | **Complete** |
| **1 · Domain** | PostgreSQL migration, airports/aircraft/routes/schedules, fare classes, seat maps | Next |
| **2 · Booking engine** | Fare-priced search, seat selection with holds, atomic booking, PNRs, cancellation policy | Planned |
| **3 · Payments & comms** | Provider-tokenised cards, email confirmations | Planned |
| **4 · Operations** | Schedule management, load factor, revenue by route | Planned |
| **5 · Presentation** | Published brand and analysis site, full story→endpoint→test traceability | Planned |

Phase 1 migrates off MongoDB. Seat holds, payment capture and PNR issuance
have to be atomic, and a single-node MongoDB cannot provide a transaction.
The reasoning will be recorded as an ADR.

---

## Running it

**Requirements:** Docker and Docker Compose. Without Docker: Python 3.13+ and
Node 22+.

```bash
git clone https://github.com/aposfys/DS-Airlines.git
cd DS-Airlines

cp .env.example .env
# SECRET_KEY is required — the app refuses to start without one:
python -c "import secrets; print(secrets.token_urlsafe(48))"

docker compose up --build
```

| | |
|---|---|
| Interface | http://localhost:3000 |
| API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |

`docker compose up` also applies `docker-compose.override.yml`, which adds
the source bind-mount and hot reload. For a production-shaped stack, run
`docker compose -f docker-compose.yml up`.

To load demo flights and an administrator, set `SEED_ON_STARTUP=true` and
supply `SEED_ADMIN_EMAIL` and `SEED_ADMIN_PASSWORD`. There are no defaults —
if either is missing the administrator is not created.

### Without Docker

```bash
# Backend
cd backend
pip install -r requirements.txt
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(48))")
uvicorn main:app --reload

# Frontend
cd frontend
npm ci
npm run dev
```

---

## Tests

```bash
cd backend && pytest              # 47 tests
cd frontend && npm run lint && npm run build
python docs/brand/contrast_check.py
```

The backend suite runs against `tests/fake_mongo.py`, an in-memory stand-in
for the Motor collection API, so **no database is required**.

That fake is a direct response to the audit. The original six tests all
exercised the same two auth endpoints, because anything touching flights,
bookings or authorization needed a live MongoDB they had no way to provide —
which is precisely why a completely dead admin surface sat in the repository
alongside a green suite. The suite is now 47 tests, and the ones that matter
most assert the defects stay fixed:

```
tests/test_authorization.py   an admin gets 200, a passenger gets 403,
                              revoking admin takes effect before expiry
tests/test_bookings.py        the card number is never persisted,
                              cancelling twice cannot credit a seat back
tests/test_flights.py         regex metacharacters are treated literally,
                              distinct routes cannot collide
```

---

## Project layout

```
backend/
  app/
    config.py         Validated settings; refuses weak or missing SECRET_KEY
    auth.py           JWT issuance, password hashing, authorization dependencies
    database.py       Motor client and index definitions
    models/schemas.py Pydantic models and validation
    routers/          auth · flights · bookings · admin
  tests/
    fake_mongo.py     In-memory Motor stand-in
frontend/
  src/
    index.css         Design tokens — the brand book's single source of truth
    components/       BookingDialog
    context/          AuthContext
    lib/format.ts     EUR formatting, Luhn
    pages/            Login · Register · Dashboard
docs/
  brand/              Brand book, logo, contrast check
  analysis/           Current-state assessment
  qa/                 Test strategy and manual cases
```

---

## Licence

[MIT](LICENSE) · Apostolos Fysekidis

DS Airlines / Delos Skyways is a fictional carrier created for this project.
It is not affiliated with any real airline or alliance.
