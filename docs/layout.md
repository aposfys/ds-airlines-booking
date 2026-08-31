# Project layout

```
backend/
  main.py             App factory, CORS, /health
  app/
    config.py         Validated settings; refuses a weak or missing SECRET_KEY
    db.py             Engine and one-session-per-request
    auth.py           JWT issuance, hashing, authorisation dependencies
    models/domain.py  The relational domain — ten tables
    schemas.py        API request and response models
    routers/          auth · flights · bookings · admin · weather
    seed.py           Reference data, demo flights, the bootstrap admin
  migrations/         Alembic revisions
  scripts/seed.py     Explicit seeding, never a startup side effect
  tests/              103 tests against real PostgreSQL
frontend/
  e2e/                Playwright — booking.spec.ts and interface.spec.ts:
                      the journey, fonts, themes, accessibility
  src/
    design-system/    Airy Sky tokens, fonts, accessibility standard
    index.css         Tokens bridged into Tailwind, plus glass and scrims
    api/              Axios client and typed endpoints
    assets/           Destination and panel photography
    components/       BookingDialog · HeroCarousel · DestinationCards
                      WeatherStrip · WeatherChip · ThemeToggle
    context/          AuthContext · ThemeContext
    lib/              Fare/time formatting, the IATA image map, useWeather
    pages/            Login · Register · Dashboard
                      *.test.tsx sit beside what they test
  scripts/            screenshots.mjs — regenerates docs/screenshots
docs/
  adr/                Architecture decisions
  screenshots/        Captures of the running app, via `make screenshots`
  analysis/           Current-state assessment
  brand/              Product brand, contrast check
  design/             Airy Sky Editorial — the design system
  product/            Personas, user stories, traceability
  qa/                 Test strategy and the manual pass
```

## Test commands

```
make check       # backend + component tests, lint, build, contrast
make check-all   # the above plus end to end
```

| | |
|---|---|
| `make test` | **103** backend tests against real PostgreSQL |
| `make test-frontend` | **72** component tests (Vitest + Testing Library) |
| `make e2e` | **17** end-to-end tests in a real browser (Playwright) |
| `make contrast` | 17 colour pairs × 2 themes, WCAG 2.2 AA |

**192 automated tests**, all in CI, across four jobs.

## Regenerating the media

The walkthrough is an animated WebP — 900×562, 24 s, 869 KB — so it autoplays and loops
inline with no player and no sound. GitHub strips `autoplay`, `loop` and `muted` from
hand-written `<video>` tags, so an animated image is the only thing that moves on its own in
a README. The source recording is [`media/usage.webm`](media/usage.webm); regenerate both
with `make walkthrough`.
