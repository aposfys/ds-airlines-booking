# ADR-001 · Move the booking engine from MongoDB to PostgreSQL

- **Status:** Accepted
- **Date:** 2026-07-29
- **Supersedes:** the MongoDB choice inherited from the original coursework
- **Affects:** Phase 1 onward

---

## Context

The original project stored everything in MongoDB. That was a reasonable
choice for coursework — it needs no schema, no migrations, and no DDL to get
a flight list on screen. It is the wrong choice for the product described in
the roadmap, and Phase 1 is the last cheap moment to change it.

Three forces make the decision now rather than later.

### 1. Booking is a transaction, and we cannot express one

Confirming a booking has to do four things atomically: hold the seat,
decrement inventory, record the payment, and issue a booking reference.
Either all four happen or none do.

Single-node MongoDB has no multi-document transactions. Transactions require
a replica set even for local development. The Phase 0 code therefore does
this:

```python
claim = await db.availableFlights.update_one(
    {"unique_code": ..., "availability": {"$gt": 0}},
    {"$inc": {"availability": -1}},
)
...
try:
    result = await db.bookings.insert_one(booking_doc)
except Exception:
    await db.availableFlights.update_one(..., {"$inc": {"availability": 1}})
```

A compensating write. It narrows the window; it does not close it. If the
process dies between the claim and the compensation — a deploy, an OOM kill,
a lost connection — the seat is gone from inventory with no booking against
it, permanently, and nothing in the system knows. That is a seat the airline
can never sell, invisible in the data. DEF-007 is the same class of bug,
already observed once.

Adding fare classes and payment capture in Phases 2 and 3 multiplies the
number of writes that must agree. The compensating-write pattern does not
scale to that; it just produces more ways to end up half-done.

### 2. The data is relational, and pretending otherwise costs us

The domain is: airports have routes, routes are flown by scheduled flights,
scheduled flights are operated by aircraft, aircraft have seat maps, seats
are sold in fare classes, fare classes have rules, bookings reference all of
it.

That is a graph of foreign keys. In documents it becomes either deep nesting
that cannot be queried across, or manual references with no integrity
guarantee. The Phase 0 code shows both failure modes: `bookings` duplicates
`cost`, `departure`, `destination` and `flight_date` off the flight with
nothing keeping them consistent, and deleting a flight orphaned its bookings
(DEF-019) because nothing could enforce the reference.

Ops questions are relational too. *Load factor by route this quarter.
Revenue per available seat kilometre. Which flights are selling below
forecast.* These are joins and aggregates. Phase 4 is built on them.

### 3. Integrity should be the database's job

Every constraint in Phase 0 is enforced in application code, which means it
is enforced only on the paths that remembered to. Seats cannot go negative —
enforced by a query filter. Emails are unique — enforced by an index added
in Phase 0, after a read-then-write check was found racing (DEF-013). A
booking must reference a real flight — not enforced at all.

PostgreSQL expresses these as `CHECK`, `UNIQUE`, `FOREIGN KEY` and exclusion
constraints. They then hold for every writer, including migrations, admin
scripts, and a future service we have not written.

---

## Options considered

### A. Keep MongoDB, add a replica set

Configure a single-node replica set in `docker-compose` to unlock
transactions. Least disruptive: Motor stays, the data layer survives.

Rejected. It solves only the first force. Modelling seat maps and fare rules
in documents stays awkward, referential integrity stays unenforceable, and
the ops queries in Phase 4 stay painful. It also adds real operational
complexity — a replica set is not free to run or reason about — to buy back
something a relational database has by default.

### B. PostgreSQL

Transactions, foreign keys, check constraints, `SELECT … FOR UPDATE` for
seat holds, and window functions for the ops reporting. SQLAlchemy 2.0 with
async support, Alembic for migrations.

Costs: rewriting the data layer, learning Alembic, and losing the ability to
change shape without a migration — which is a cost in Phase 1 and a benefit
from Phase 2 on.

### C. PostgreSQL plus Redis

B, plus Redis for seat-hold TTLs and search caching.

Deferred rather than rejected. Seat holds with an expiry are genuinely a
good fit for Redis. But a `held_until timestamptz` column with a periodic
sweep is sufficient at this scale, and it keeps holds inside the same
transaction as the booking. Introducing a second datastore to expire rows is
complexity bought before it is needed. Revisit if hold contention becomes
real.

---

## Decision

**PostgreSQL 17, via SQLAlchemy 2.0 (async, `asyncpg`) with Alembic
migrations.** Option B.

Redis is explicitly deferred; seat holds are a timestamp column until
measurement says otherwise.

---

## Consequences

### Gained

- Booking becomes one transaction. The compensating write is deleted, not
  improved.
- Referential integrity is enforced by the database, so DEF-019 becomes
  structurally impossible rather than fixed by a check.
- Denormalised fields on bookings are replaced by joins, removing the
  consistency drift.
- Phase 4's reporting becomes ordinary SQL.
- Tests run against a real database. The `tests/fake_mongo.py` stand-in built
  in Phase 0 — honest about being a bridge — is retired. Its limitation was
  that passing tests were evidence about our logic, not about the database;
  that stops being true.

### Paid

- The entire data layer is rewritten. This is the expensive phase.
- Schema changes now need migrations. Deliberate: the absence of that
  discipline is why the `password` / `hashed_password` mismatch (DEF-008)
  could exist in the first place.
- Local development and CI both need a running PostgreSQL, where the Phase 0
  suite needed nothing.
- Existing MongoDB data is not migrated. It is demo seed data; a migration
  script would be theatre. Stated so the omission is deliberate and visible.

### Risks

- **Async SQLAlchemy has sharper edges than Motor** — lazy loading raises
  rather than blocks, and sessions must not be shared across tasks. Mitigated
  by eager loading at the query site and one session per request.
- **Migration drift** between models and Alembic revisions. Mitigated by a CI
  check that fails if the models and the migration chain disagree.
