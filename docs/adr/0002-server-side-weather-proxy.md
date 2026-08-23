# ADR-002 · The browser never calls the forecast provider

**Status** Accepted
**Date** 2026-08-23

## Context

The dashboard shows current conditions and a three-day forecast for every
destination: a chip on each card, and a strip beneath them. The data comes
from [Open-Meteo](https://open-meteo.com/), which is free, keyless and
CORS-permissive — so calling it straight from the browser would work, and
would be less code than anything else considered here.

Weather is also the first thing in this product that depends on a third party
staying up. Everything else it does is answerable from its own database.

## Options

**1. Call Open-Meteo from the browser.** Least code. No new endpoint, no new
dependency, no cache to reason about. Each visitor's browser makes six
requests on load, one per destination; a slow provider is a slow dashboard,
and an outage is a console full of failed cross-origin requests with the
interface deciding what to do about it in `catch` blocks scattered across
components.

**2. Proxy it, uncached.** One endpoint, one place to handle failure. Still
six upstream calls per page load, now made by us rather than by the visitor,
which is worse for the provider and no better for the passenger.

**3. Proxy it, cached.** One endpoint, one failure path, and one cache
entry per station shared by every visitor.

## Decision

Option 3. `GET /api/weather` proxies Open-Meteo server-side with a
thirty-minute TTL keyed by IATA code.

Thirty minutes because conditions do not move faster than that and the
dashboard is the kind of page people reload repeatedly. The cache is a plain
dict in the process, not a caching tier: it sits in front of a free public
API, and a second worker keeping its own copy costs one extra upstream call
per half hour.

The endpoint is unauthenticated. Weather is not passenger data, and requiring
a token would mean the dashboard could not paint until login resolved.

**The failure mode is the decision.** Every path returns `200` with whatever
could be gathered. A station the provider did not answer for is simply absent
from the response; the interface draws no chip and says nothing. There is no
error state to handle, because a forecast API having a bad afternoon must not
be capable of taking down a booking dashboard. Unknown WMO codes degrade to
"Unsettled" rather than raising — the provider is free to add more.

## Consequences

- `airports` gains `latitude` and `longitude`. A provider needs a position,
  and an airport's position is airport reference data, so it belongs in that
  row next to the IANA zone rather than in a lookup table in code. Range
  constraints and a NOT NULL come with it: a station with no position would
  otherwise be silently skipped or defaulted to 0,0, which is in the Atlantic.
- `httpx` moves from a test-only to a runtime dependency.
- The tests never call Open-Meteo. Each substitutes the router's own `_fetch`,
  because a suite that reached a third party could go red for reasons that
  have nothing to do with this repository — the same mistake in the tests that
  the proxy exists to avoid in the product.
- The cache is per-process, so a multi-worker deployment holds several copies.
  Accepted at this size; a shared cache is the change if that stops being true.
