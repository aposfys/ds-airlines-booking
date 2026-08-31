# From assignment to product, and where it stops

## What changed

An assignment is finished when it is marked. A product is never asked whether it is
finished — it is asked who flies this airline, what the airline promises, what happens when
a payment fails, and how anyone would know if it broke.

Answering those questions meant starting with an honest look at what was already there. The
most useful document in this repository is not the API reference; it is the
[**current-state assessment**](analysis/current-state-assessment.md) — an audit of the
original code recording all 30 defects found, what each would have cost the business, and
where it was resolved.

Four were Critical:

- **The entire admin surface was unreachable.** Tokens never carried the `is_admin` claim
  that every authorisation check read, so flight creation, repricing and withdrawal returned
  403 to everyone — including the administrator the app seeded for itself.
- **Full card numbers were stored in cleartext**, in the same record as the passenger's
  passport number.
- **Every deployment shipped the same known admin password**, hardcoded, next to a signing
  key committed to this repository.
- **`docker-compose up --build` could not build**, because the frontend image pinned Node 18
  against a toolchain requiring Node 20+.

None of this reflects badly on the original. An assignment is judged on whether it
demonstrates the concept, and it did. What it was never judged on is whether anyone could
run it, sell a seat with it, or trust it with a card number — and those are the only
questions that matter once you call something a product.

The previous README called it "production-ready". Recording precisely why that was wrong,
rather than quietly rewriting it, is the point of the exercise.

## The interface

Built on **[Airy Sky Editorial](design/airy-sky-editorial.md)**, a design system of my own:
light-first, a Paper & Sky palette over cream rather than white, Outfit for display and
numerals, Figtree for the interface. DS Airlines owns the words; the design system owns
everything you can see.

Both themes are token-complete and contrast-verified on every push: **17 colour pairs,
checked in light and dark, 34 assertions against WCAG 2.2 AA.** A hex literal in a component
is a bug.

Three of those pairs are new, and they are the ones the design rests on. The rule is that
**no text ever sits on bare photography**, so what CI measures is the scrim — composited over
a blown-out highlight, the worst a photograph can put underneath it. If the scrims hold
there, the rule holds for any image.

Every image and frame in the README is a capture of the running application, taken by
`make screenshots` and `make walkthrough` against a live stack. Those targets exist because
these files were once design comps and a prototype recording instead: the README described a
hero carousel, destination cards and live weather that the code did not contain, and nothing
caught it, because nothing connected the pictures to the product.

**Live weather** on the destination cards, the flight cards and the dashboard strip comes
from [Open-Meteo](https://open-meteo.com/) — current conditions plus a three-day forecast,
proxied server-side and cached for thirty minutes. It fails quietly by design: a station the
provider does not answer for simply has no chip. See
[ADR-002](adr/0002-server-side-weather-proxy.md).

**On the photography.** The destination and panel images are crops lifted out of the
original design comps, which is the only place they existed. They are small, already
recompressed, and soft at card size. They are honest placeholders for real licensed
photography, and replacing one is a single line in
[`destination-images.ts`](../frontend/src/lib/destination-images.ts).

## Phases delivered

The project is complete as scoped and stops here deliberately.

| Phase | Scope | |
|---|---|---|
| **0 · Foundation** | Defect register, critical fixes, CI, repo hygiene | [`v0.1.0`](https://github.com/aposfys/ds-airlines-booking/releases/tag/v0.1.0) |
| **1 · Domain** | PostgreSQL, routes and schedules, fare classes, seat maps, a design system, three test suites | [`v0.2.0`](https://github.com/aposfys/ds-airlines-booking/releases/tag/v0.2.0) |
| **2 · Interface** | Airy Sky Editorial, hero carousel, destination cards, live weather, coordinates on stations | unreleased |

The design system has been replaced twice. v0.2.0 shipped on AF; Atlas replaced it; Airy Sky
Editorial replaced Atlas and is what the product runs on now. Each swap left the domain, the
API and test behaviour alone — the [changelog](../CHANGELOG.md) has what moved and what it
recovered.

## What was not built, and why

An earlier plan ran to five phases: seat selection in the interface, payment capture, an
operations interface, a published brand site. They were dropped on purpose, and the
reasoning is worth stating because the omissions are visible in the product.

What this repository argues is about **judgement** — auditing inherited code and finding
thirty defects in it, choosing a datastore and writing down what that cost, and building
tests that catch what a green suite cannot see. A seat picker and a payment integration
would demonstrate *craft*, which is not what is in question, and would take considerably
longer than what they add.

So the gaps stay, and they are named wherever they bite:

- **The administrative surface has no interface.** Publishing flights, repricing and load
  factor run through Swagger. This is the largest gap between what the product does and what
  a person could use, and it has its own empty row in the
  [traceability matrix](product/user-stories.md#traceability).
- **No seat map.** A seat is requested by typing its number, though the database already
  knows which are window, aisle and exit row.
- **No payment capture**, by design — see [SECURITY.md](../SECURITY.md).
- **Cancellation ignores refund rules.** Light is non-refundable in data and in the brand;
  cancelling it still returns the seat and records nothing about money owed.
- **No special-assistance booking.** A genuine passenger need this does not meet — an
  omission, not a decision.
- **The photography is placeholder.** Real licensed images would replace the comp crops;
  nothing else changes.

Versions stay pre-1.0 for the same reason. 1.0.0 would claim the product is finished, and it
is not; it is *scoped*, which is a different thing.

## What the tests are for

The backend suite runs against a **real PostgreSQL**, and the fixtures build the schema by
running the Alembic migrations — so every run also proves the migration chain applies. CI
additionally fails on migration drift: a model changed without a revision to match does not
merge.

That matters because of what it replaced. The original six tests all exercised the same two
auth endpoints, since anything touching flights, bookings or authorisation needed a database
they had no way to provide — which is precisely why a completely dead admin surface sat in
the repository alongside a green suite.

The tests that matter most assert the defects stay fixed:

```
tests/test_authorization.py   an admin gets 200, a passenger gets 403,
                              revoking admin takes effect before expiry
tests/test_bookings.py        payment details are refused outright,
                              cancelling twice cannot credit a seat back
tests/test_flights.py         search does no pattern matching,
                              a flight with bookings cannot be deleted
tests/test_constraints.py     the database itself refuses bad data,
                              and a station cannot exist without a position
tests/test_weather.py         a dead forecast provider still returns 200
e2e/interface.spec.ts         the webfonts actually load
```

The weather tests are worth a word. Every one of them asserts a **200** — an upstream that
returns nothing, an upstream that raises, and a station outside the network must each leave
the dashboard rendering. None of them touch Open-Meteo: a suite that reached a third party
could go red because someone else was having a bad afternoon, which is the same mistake in
the tests that the proxy exists to avoid in the product.

The font test exists because the fonts once did not load. Nested under Tailwind's `@import`,
the production build shipped **zero** `.woff2` files and the whole typographic identity fell
back to Helvetica **with no error of any kind**. Four Phase 1 defects were invisible to a
green unit suite; the end-to-end suite is the answer to that.
