<h1>DS Airlines</h1>

<p>
  <a href="https://github.com/aposfys/ds-airlines-booking/actions/workflows/ci.yml">
    <img alt="CI" src="https://github.com/aposfys/ds-airlines-booking/actions/workflows/ci.yml/badge.svg">
  </a>
  <img alt="tests" src="https://img.shields.io/badge/tests-175-brightgreen">
  <img alt="python" src="https://img.shields.io/badge/python-3.13-blue">
  <img alt="node" src="https://img.shields.io/badge/node-22-blue">
  <img alt="licence" src="https://img.shields.io/badge/licence-MIT-lightgrey">
</p>

<strong>A university assignment, taken apart and rebuilt as a product.</strong>

DS Airlines started life in the **Department of Digital Systems at the
University of Piraeus** — which is where the DS comes from. It was a Flask
app that could list flights and take a booking, and it did what an assignment
is supposed to do.

This repository is what happened next: a flight booking platform for a
fictional Greek short-haul carrier, built as a business rather than a
codebase. Brand, product analysis, architecture decisions and test strategy
are first-class artefacts here, alongside the API and the interface.

**FastAPI · PostgreSQL · SQLAlchemy 2.0 · Alembic · React 19 · TypeScript ·
Tailwind v4 · Docker**

[**Run it**](#running-it) · [What was wrong](#from-assignment-to-product) ·
[What was left out](#what-was-not-built-and-why) · [Tests](#tests) ·
[Documentation](docs/README.md)

![The dashboard: search, fare-priced results, and a confirmed itinerary](docs/images/dashboard-dark.jpg)

---

## From assignment to product

An assignment is finished when it is marked. A product is never asked whether
it is finished — it is asked who flies this airline, what the airline
promises, what happens when a payment fails, and how anyone would know if it
broke.

Answering those questions meant starting with an honest look at what was
already there. The most useful document in this repository is not the API
reference; it is the
[**current-state assessment**](docs/analysis/current-state-assessment.md) — an
audit of the original code recording all 30 defects found, what each would
have cost the business, and where it was resolved.

Four were Critical:

- **The entire admin surface was unreachable.** Tokens never carried the
  `is_admin` claim that every authorisation check read, so flight creation,
  repricing and withdrawal returned 403 to everyone — including the
  administrator the app seeded for itself.
- **Full card numbers were stored in cleartext**, in the same record as the
  passenger's passport number.
- **Every deployment shipped the same known admin password**, hardcoded, next
  to a signing key committed to this repository.
- **`docker-compose up --build` could not build**, because the frontend image
  pinned Node 18 against a toolchain requiring Node 20+.

None of this reflects badly on the original. An assignment is judged on
whether it demonstrates the concept, and it did. What it was never judged on
is whether anyone could run it, sell a seat with it, or trust it with a card
number — and those are the only questions that matter once you call something
a product.

The previous README called it "production-ready". Recording precisely why
that was wrong, rather than quietly rewriting it, is the point of the
exercise — and it is the reason the section on
[what was deliberately not built](#what-was-not-built-and-why) is as long as
the section on what was.

---

## The interface

Built on **[Atlas](frontend/src/design-system/README.md)**, a design system
of my own: rounded glass over navy and chartreuse, Gabarito for the interface
and Spline Sans Mono for anything numeric — fares, times, IATA codes, booking
references. DS Airlines owns the words; Atlas owns everything you can see.

Both themes are token-complete and contrast-verified on every push: **14
colour pairs, checked in light and dark, 28 assertions against WCAG 2.2 AA.**
A hex literal in a component is a bug.

**Web**

| Log in | Register |
|---|---|
| ![The login page in the light theme, split-panel editorial layout](docs/images/login-light.jpg) | ![The register page in the dark theme](docs/images/register-dark.jpg) |

| Dashboard | Confirm booking |
|---|---|
| ![The dashboard in the light theme: search, fare-priced results, confirmed itineraries](docs/images/dashboard-light.jpg) | ![The booking dialog: three branded fares with their rules, and no card field](docs/images/booking-dialog.jpg) |

**Mobile**

| Log in | Dashboard | Confirm booking |
|---|---|---|
| ![The login page on a phone-width viewport](docs/images/mobile-login.jpg) | ![The dashboard on a phone-width viewport, single column](docs/images/mobile-dashboard.jpg) | ![The booking dialog on a phone-width viewport](docs/images/mobile-booking-dialog.jpg) |

> **No payment is taken and no card details are collected.** The booking form
> has no card field, and the API returns `422` to a request carrying one.
> Do not enter real payment information. See [SECURITY.md](SECURITY.md).

### A second direction, designed but not shipped

[**Airy Sky Editorial**](docs/design/airy-sky-editorial.md) is a later visual
direction taken as far as full comps and a click-through prototype: light-first
by default, a Paper & Sky palette over cream rather than navy, Outfit and
Figtree in place of Gabarito, and a glass search bar floating on destination
photography. It adds a hero carousel, popular-destination cards and a live
weather strip to the dashboard.

**None of it is in this codebase.** The screens and the recording below are
the prototype, not the application you get from `make dev` — the shipping
interface is the Atlas one above. The direction is documented because the
work was done and the reasoning is worth reading, not because it is pending.
Treating a comp as a feature is exactly the habit this project exists to
break.

| Dashboard — light | Dashboard — dark |
|---|---|
| ![Prototype: hero carousel with glass search bar, popular destinations, weather strip and flight results](docs/screenshots/dashboard-light.jpg) | ![The same prototype dashboard in the dark theme](docs/screenshots/dashboard-dark.jpg) |

| Search results | Register |
|---|---|
| ![Prototype flight cards with route photography, weather chips and fares](docs/screenshots/results-light.jpg) | ![Prototype editorial split registration screen](docs/screenshots/register-light.jpg) |

| Mobile — dashboard | Mobile — log in |
|---|---|
| ![The prototype dashboard on a phone](docs/screenshots/mobile-dashboard.jpg) | ![The prototype sign-in screen on a phone](docs/screenshots/mobile-login.jpg) |

A 24-second loop of the same prototype — creating an account, signing in,
browsing the carousel and the destination cards, and running an ATH → LHR
search. It plays by itself; click it for the full-resolution recording.

[![The Airy Sky prototype: registration, sign-in, the destination carousel and an ATH → LHR search](docs/media/usage.webp)](docs/media/usage.mp4)

<sup>Animated WebP — 900×562, 23.8s, 1.1 MB — so it autoplays and loops
inline with no player and no sound. GitHub strips `autoplay`, `loop` and
`muted` from hand-written `<video>` tags, so an animated image is the only
thing that moves on its own in a README. The source recording is
[`docs/media/usage.mp4`](docs/media/usage.mp4) (H.264, 1280×800).</sup>

---

## Documentation

| | |
|---|---|
| [Current-state assessment](docs/analysis/current-state-assessment.md) | The full defect register, with business impact and resolution |
| [ADR-001 · PostgreSQL over MongoDB](docs/adr/0001-postgresql-over-mongodb.md) | Why the booking engine left the document model |
| [Personas](docs/product/personas.md) · [User stories](docs/product/user-stories.md) | Who this is for, and a story → endpoint → test traceability matrix |
| [Product brand](docs/brand/brandbook.md) | Positioning, network, fare architecture, voice |
| [Atlas design system](frontend/src/design-system/README.md) | The vendored token layer, and what was deliberately not vendored |
| [Airy Sky Editorial](docs/design/airy-sky-editorial.md) | The unshipped visual direction, and the system behind it |
| [Test strategy](docs/qa/test-strategy.md) | Layers, how to run everything, and a 42-case manual pass |
| [Changelog](CHANGELOG.md) | What changed in each phase, including what was removed |
| [Security](SECURITY.md) | Why this takes no payments, how to run it safely, and known limitations |

Start at [`docs/`](docs/README.md), which orders these for a first read.

---

## Running it

### Docker — needs nothing else installed

```bash
cp .env.example .env
```

`SECRET_KEY` and `POSTGRES_PASSWORD` are required; the application refuses to
start without them. Generate a key with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Then:

```bash
make up
```

### Natively

Needs `postgresql@17`, Python 3.13 and Node 22.

```bash
make setup   # venv, npm ci, a database cluster in .pgdata, migrations
make seed    # demo flights and an administrator
make dev     # API on :8000, interface on :5173
```

The cluster lives in `.pgdata` inside the repo on port 55432, so it cannot
collide with any PostgreSQL you already run. `make db-reset` throws it away.

| | |
|---|---|
| Interface | http://localhost:5173 (`make dev`) or http://localhost:3000 (`make up`) |
| API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |

Demo data is opt-in. Nothing is seeded unless you ask, and there are no
default credentials — `make seed` supplies its own, for local use only.

**The administrative surface has no interface.** Publishing flights,
repricing and load factor all run through Swagger — see
[Scope](#what-was-not-built-and-why).

---

## Tests

```bash
make check       # backend + component tests, lint, build, contrast
make check-all   # the above plus end to end
```

| | |
|---|---|
| `make test` | **89** backend tests against real PostgreSQL |
| `make test-frontend` | **69** component tests (Vitest + Testing Library) |
| `make e2e` | **17** end-to-end tests in a real browser (Playwright) |
| `make contrast` | 14 colour pairs × 2 themes, WCAG 2.2 AA |

**175 automated tests**, all in CI, across four jobs.

The backend suite runs against a **real PostgreSQL**, and the fixtures build
the schema by running the Alembic migrations — so every run also proves the
migration chain applies. CI additionally fails on migration drift: a model
changed without a revision to match does not merge.

That matters because of what it replaced. The original six tests all
exercised the same two auth endpoints, since anything touching flights,
bookings or authorisation needed a database they had no way to provide —
which is precisely why a completely dead admin surface sat in the repository
alongside a green suite.

The tests that matter most assert the defects stay fixed:

```
tests/test_authorization.py   an admin gets 200, a passenger gets 403,
                              revoking admin takes effect before expiry
tests/test_bookings.py        payment details are refused outright,
                              cancelling twice cannot credit a seat back
tests/test_flights.py         search does no pattern matching,
                              a flight with bookings cannot be deleted
tests/test_constraints.py     the database itself refuses bad data
e2e/interface.spec.ts         the webfonts actually load
```

That last one exists because they once did not. Nested under Tailwind's
`@import`, the production build shipped **zero** `.woff2` files and the whole
typographic identity fell back to Helvetica **with no error of any kind**.
Four Phase 1 defects were invisible to a green unit suite; the end-to-end
suite is the answer to that.

---

## Scope

**Two phases, delivered.** The project is complete as scoped and stops here
deliberately.

| Phase | Scope | |
|---|---|---|
| **0 · Foundation** | Defect register, critical fixes, CI, repo hygiene | [`v0.1.0`](https://github.com/aposfys/ds-airlines-booking/releases/tag/v0.1.0) |
| **1 · Domain** | PostgreSQL, routes and schedules, fare classes, seat maps, a design system, three test suites | [`v0.2.0`](https://github.com/aposfys/ds-airlines-booking/releases/tag/v0.2.0) |

v0.2.0 shipped on the AF design system; Atlas replaced it afterwards, with no
change to the domain, the API or test behaviour. The swap and its four
recovered contrast failures are in the [changelog](CHANGELOG.md).

### What was not built, and why

An earlier plan ran to five phases: seat selection in the interface, payment
capture, an operations interface, a published brand site. They were dropped
on purpose, and the reasoning is worth stating because the omissions are
visible in the product.

What this repository argues is about **judgement** — auditing inherited code
and finding thirty defects in it, choosing a datastore and writing down what
that cost, and building tests that catch what a green suite cannot see. A
seat picker and a payment integration would demonstrate *craft*, which is not
what is in question, and would take considerably longer than what they add.

So the gaps stay, and they are named wherever they bite:

- **The administrative surface has no interface.** Publishing flights,
  repricing and load factor run through Swagger. This is the largest gap
  between what the product does and what a person could use, and it has its
  own empty row in the
  [traceability matrix](docs/product/user-stories.md#traceability).
- **No seat map.** A seat is requested by typing its number, though the
  database already knows which are window, aisle and exit row.
- **No payment capture**, by design — see [SECURITY.md](SECURITY.md).
- **Cancellation ignores refund rules.** Light is non-refundable in data and
  in the brand; cancelling it still returns the seat and records nothing
  about money owed.
- **No special-assistance booking.** A genuine passenger need this does not
  meet — an omission, not a decision.
- **The Airy Sky Editorial direction was never implemented.** It exists as
  comps, a prototype recording and a written system, and
  [is labelled as such](#a-second-direction-designed-but-not-shipped).

Versions stay pre-1.0 for the same reason. 1.0.0 would claim the product is
finished, and it is not; it is *scoped*, which is a different thing.

---

## Project layout

```
backend/
  main.py             App factory, CORS, /health
  app/
    config.py         Validated settings; refuses a weak or missing SECRET_KEY
    db.py             Engine and one-session-per-request
    auth.py           JWT issuance, hashing, authorisation dependencies
    models/domain.py  The relational domain — ten tables
    schemas.py        API request and response models
    routers/          auth · flights · bookings · admin
    seed.py           Reference data, demo flights, the bootstrap admin
  migrations/         Alembic revisions
  scripts/seed.py     Explicit seeding, never a startup side effect
  tests/              89 tests against real PostgreSQL
frontend/
  e2e/                Playwright — booking.spec.ts and interface.spec.ts:
                      the journey, fonts, themes, accessibility
  src/
    design-system/    Vendored Atlas tokens, fonts, accessibility standard
    index.css         Atlas tokens bridged into Tailwind
    api/              Axios client and typed endpoints
    components/       BookingDialog · ThemeToggle
    context/          AuthContext · ThemeContext
    lib/              Formatting for fares, times and durations
    pages/            Login · Register · Dashboard
                      *.test.tsx sit beside what they test
docs/
  adr/                Architecture decisions
  analysis/           Current-state assessment
  brand/              Product brand, contrast check
  design/             Airy Sky Editorial — designed, not shipped
  product/            Personas, user stories, traceability
  qa/                 Test strategy and the manual pass
```

---

## Licence

[MIT](LICENSE) · Apostolos Fysekidis

DS Airlines is a fictional carrier created for this project. It is not
affiliated with any real airline or alliance.
