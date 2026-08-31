# DS Airlines
A university assignment, taken apart and rebuilt as a product.

[![CI](https://github.com/aposfys/ds-airlines-booking/actions/workflows/ci.yml/badge.svg)](https://github.com/aposfys/ds-airlines-booking/actions/workflows/ci.yml)
![tests](https://img.shields.io/badge/tests-192-brightgreen)
![licence](https://img.shields.io/badge/licence-MIT-lightgrey)

DS Airlines started life in the Department of Digital Systems at the University of Piraeus — which is where the DS comes from. It was a Flask app that could list flights and take a booking. This repository is a flight booking platform for a fictional Greek short-haul carrier, built as a business rather than a codebase.

**FastAPI · PostgreSQL · SQLAlchemy 2.0 · Alembic · React 19 · TypeScript · Tailwind v4 · Docker**

![The dashboard: hero carousel, popular destinations, live weather and fare-priced results](docs/screenshots/dashboard-light.jpg)

| Search results | Register |
|---|---|
| ![Flight cards with route photography, weather chips and fares](docs/screenshots/results-light.jpg) | ![Editorial split registration screen over the aircraft panel](docs/screenshots/register-light.jpg) |

[![Registering, signing in, browsing destinations and searching ATH to LHR](docs/media/usage.webp)](docs/media/usage.webm)

> **No payment is taken and no card details are collected.** The booking form has no card field, and the API returns `422` to a request carrying one. Do not enter real payment information. See [SECURITY.md](SECURITY.md).

### Running it

Docker, needing nothing else installed:

```
cp .env.example .env
make up
```

`SECRET_KEY` and `POSTGRES_PASSWORD` are required; the application refuses to start without them. Generate a key with `python -c "import secrets; print(secrets.token_urlsafe(48))"`.

Natively, with `postgresql@17`, Python 3.13 and Node 22:

```
make setup   # venv, npm ci, a database cluster in .pgdata, migrations
make seed    # demo flights and an administrator
make dev     # API on :8000, interface on :5173
```

The cluster lives in `.pgdata` inside the repo on port 55432, so it cannot collide with any PostgreSQL you already run. Demo data is opt-in and there are no default credentials. Swagger UI is at http://localhost:8000/docs — the administrative surface has no interface and runs through it.

### Tests

```
make check       # backend + component tests, lint, build, contrast
make check-all   # the above plus end to end
```

**192 automated tests** across four CI jobs: 103 backend against real PostgreSQL, 72 component (Vitest), 17 end-to-end (Playwright), plus 17 colour pairs × 2 themes against WCAG 2.2 AA.

### More

- [Documentation index](docs/README.md) — start here
- [Current-state assessment](docs/analysis/current-state-assessment.md) — the 30 defects found in the original, with business impact and resolution
- [What was built and what deliberately was not](docs/scope.md)
- [Test strategy and what the tests are for](docs/qa/test-strategy.md)
- [Airy Sky Editorial](docs/design/airy-sky-editorial.md) — the design system
- [Project layout](docs/layout.md)

---

[MIT](LICENSE) · Apostolos Fysekidis

DS Airlines is a fictional carrier created for this project. It is not affiliated with any real airline or alliance.
