# Current-State Assessment

**DS Airlines · assessed 29 July 2026 against commit `f1f732d`**
**Resolution status updated 2 August 2026, after Phase 1.**

An audit of the codebase as it stood before Phase 0, recording every defect
found, its business consequence, and where it was resolved.

It is written plainly, including where the project's own README was wrong,
because the value of this document is the accounting — not the reassurance.

---

## 1. Summary

The repository described itself as *"a university project refactored into a
modern, production-ready full-stack application."* It was a competent
skeleton of one. It was not production-ready, and the gap was not cosmetic:

- **The entire administrative surface was unreachable.** Every privileged
  endpoint returned 403 to every caller, including the administrator the
  application seeded for itself. Flights could not be created, updated or
  deleted through the API by anybody.
- **Full payment card numbers were stored in cleartext**, in the same
  document as the passenger's passport number.
- **Every deployment shipped with the same known administrator password**,
  hardcoded in the source, created automatically on first startup.
- **The documented setup path could not run.** `docker-compose up --build` —
  the README's recommended route — could not build the frontend image.

Of 30 defects recorded, 4 are Critical and 6 are High.

The root cause of the most serious ones is uniform and worth stating
directly: **the test suite could not reach the code that was broken.** Six
tests existed. All six exercised the two auth endpoints. Nothing touched
flights, bookings, or authorization, because doing so required a live
MongoDB that the tests had no way to provide. A single test asserting that
an administrator receives 200 from `/api/admin/dashboard` would have caught
DEF-001 immediately.

### By severity

| Severity | Count | Meaning |
|---|---|---|
| **Critical** | 4 | Data exposure, or a core capability that cannot function |
| **High** | 6 | Exploitable, or breaks a documented path |
| **Medium** | 12 | Incorrect behaviour, or materially misleads |
| **Low** | 8 | Hygiene, maintainability, drag on future work |

### By resolution

| Status | Count |
|---|---|
| Fixed in Phase 0 | 24 |
| Deferred to a later phase, by design | 5 |
| Accepted, documented | 1 |

---

## 2. Critical

### DEF-001 · The admin surface was unreachable

**Impact:** No flight could be created, repriced or withdrawn through the
API. For an airline, that is the revenue-management function in its
entirety. The system could only ever sell the three flights inserted by the
seed script.

`create_access_token` wrote a payload of `sub` and `exp` only:

```python
to_encode.update({"exp": expire})
encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

Every authorisation check then read a key that was never written:

```python
# app/auth.py:70, and repeated inline in flights.py:41, 76, 96
if not current_user.get("is_admin"):
    raise HTTPException(status_code=403, ...)
```

`.get()` on a missing key returns `None`, so the branch was taken
unconditionally. There was no code path by which any caller could pass it.

**Resolved:** Phase 0. Privileges are read from the stored user record via a
`get_current_admin` dependency. Regression tests in
`tests/test_authorization.py`.

---

### DEF-002 · The token was treated as the user record

**Impact:** Deactivating or deleting an account had no effect until its
token expired — up to 30 minutes of continued full access. `is_active` was
declared on the model and enforced nowhere. Offboarding a compromised or
departing staff account was not possible.

`get_current_user` returned the decoded JWT payload and said so:

```python
# Normally we would fetch user from DB here to confirm existence,
# but for simplicity we rely on JWT content or inject DB dependency if needed.
return payload
```

**Resolved:** Phase 0. Every request resolves the caller against the
database; the record, not the token, determines privilege and status.

---

### DEF-003 · Cleartext card numbers stored beside passport numbers

**Impact:** The most serious finding. `BookingCreate.credit_card` was
persisted verbatim:

```python
booking_dict = booking.model_dump()   # includes the full PAN
new_booking = await db.bookings.insert_one(booking_dict)
```

Each booking document therefore held a full payment card number, the
passenger's full name, and their passport number together. Any read access
to the `bookings` collection — a leaked connection string, a backup, an
injection, an over-broad support query — yields everything needed for both
payment fraud and identity fraud on every passenger at once.

This is a PCI-DSS violation on the card data alone (Req. 3: do not store
sensitive authentication data; render the PAN unreadable). Combined with
passport numbers it is a failure of GDPR Art. 32 to apply appropriate
technical measures, and a breach here would very likely meet the Art. 33
notification threshold.

Compounding it, the database port was published to the host without
authentication (DEF-021).

**Resolved: fully, in Phase 1.** Phase 0 stopped *storing* the PAN —
validated, reduced to four digits, discarded. Phase 1 stopped *accepting*
one.

The Phase 0 fix was an improvement that left the real problem standing: this
is a public demonstration with no payment provider behind it, and an
ordinary-looking card field will eventually be handed a real card by someone
who did not read the page. A live PAN still crossed the network, sat in
request memory, and would have landed in anything logging the request body.

`BookingCreate` now declares `extra="forbid"`, so a client sending
`credit_card` receives a 422 rather than having the field silently ignored —
nothing can quietly start posting card numbers again. `bookings.card_last4`
is nullable and null for every booking the application creates.

This is stronger than the Phase 3 plan, which was provider tokenisation, and
arrived two phases earlier. Tokenisation is still what a real integration
would use; it is no longer what closes this defect.

---

### DEF-004 · Known administrator credentials in every deployment

**Impact:** `seed_data()` ran unconditionally on every application startup,
production included, and created an administrator with the password `admin`:

```python
password = "admin"
...
"username": "admin@unipi.gr", "is_admin": True
```

Alongside it, the signing key fell back to a placeholder committed to the
repository:

```python
SECRET_KEY = os.environ.get("SECRET_KEY", "your-super-secret-key-change-this-in-prod")
```

Anyone reading this public repository could forge a valid token for any
deployment that had not overridden the variable. The two defects reinforce
each other: the seeded account gives a target, the known key gives entry
without one.

That DEF-001 made admin privileges useless is the only reason this was not
immediately exploitable — one bug masking another is not a control.

**Resolved:** Phase 0. Seeding is opt-in with no default credentials, and
`app/config.py` refuses to start on a missing, weak, or placeholder key.

---

## 3. High

### DEF-005 · Regex injection into an unauthenticated endpoint

Search terms went into a MongoDB `$regex` unescaped:

```python
query["departure"] = {"$regex": departure, "$options": "i"}
```

`.*` matched every record; a catastrophically backtracking pattern such as
`(a+)+$` pins a CPU core with a single unauthenticated GET, and repeated
requests are a denial-of-service with no account required.
**Resolved:** Phase 0 — `re.escape`, plus enforced pagination bounds.

### DEF-006 · Flight designators collided by construction

Codes were built from the *first letter* of each city name, so Athens→Berlin
and Amsterdam→Brussels on the same date and hour produced the same code and
the second flight was rejected as a duplicate. The seeded flights used codes
(`AEE123`) that the generator could never produce, so seeded and
API-created data followed different schemes.
**Resolved:** Phase 0 — IATA station codes. Phase 1 replaces this with a
proper schedule model.

### DEF-007 · Failed bookings silently destroyed inventory

Availability was decremented before the booking was inserted, with no
compensation if the insert failed. Seat count drifted only downwards; over
time an aircraft would show as full while flying empty — unsellable
inventory, invisible in the data.
**Resolved:** Phase 0 — the seat is released on failure. Phase 1 makes it a
real transaction.

### DEF-008 · Accounts created by an administrator could never log in

`admin.py` wrote the digest to `hashed_password`; `auth.py` read
`user["password"]`. Every such login raised `KeyError` and returned 500 —
permanently, with no recovery path short of editing the database.
**Resolved:** Phase 0 — one shared constant.

### DEF-009 · The documented setup could not build

`frontend/Dockerfile` used `node:18-alpine`. The lockfile pins Vite 7.3.1
(`engines: ^20.19.0 || >=22.12.0`) and react-router-dom 7.13.1
(`>=20.0.0`). The README's recommended path, `docker-compose up --build`,
therefore could not produce a frontend image — the first thing any evaluator
would try.
**Resolved:** Phase 0 — `node:22-alpine`, `npm ci`.
*Verified from the lockfile's declared engine constraints; Docker was not
available in the assessment environment to reproduce the failing build.*

### DEF-010 · Internal exception text returned to clients

```python
detail=f"Internal Server Error: {str(e)}"
```
Any unhandled error was reflected to the caller, leaking schema and driver
detail useful for probing.
**Resolved:** Phase 0 — logged server-side, generic message returned.

---

## 4. Medium

| ID | Finding | Business impact | Status |
|---|---|---|---|
| DEF-011 | `docker-compose` passed `VITE_API_URL` as a build arg the Dockerfile never declared, so it was silently discarded | Every build hardcoded `localhost`; no deployable configuration existed | Fixed |
| DEF-012 | The UI promised "8+ characters and a number"; the API enforced neither | `"a"` was an acceptable password | Fixed |
| DEF-013 | Uniqueness of email and username rested on a read-then-write check | Two concurrent registrations could both pass it | Fixed — unique indexes |
| DEF-014 | UI claimed "A Star Alliance Member" and offered "Miles+Bonus" | Star Alliance is a real alliance; Miles+Bonus is Aegean Airlines' registered programme. Trademark appropriation in a public repo | Fixed |
| DEF-015 | Fares rendered as `${flight.cost}` | USD shown for a carrier operating exclusively in the eurozone | Fixed |
| DEF-016 | The frontend invented the user profile from the JWT — `fullname: 'User'` | Every passenger was greeted "Welcome, User"; no `/me` endpoint existed to ask | Fixed |
| DEF-017 | No booking form. The dashboard posted a hardcoded card, the account name, and `passport_num: 'N/A'` | Bookings could not carry real passenger data — and the hardcoded number fails the Luhn check added in Phase 0, so booking broke outright | Fixed |
| DEF-018 | Search filtered one already-fetched page in the browser | Anything past the first 100 records was invisible to search | Fixed |
| DEF-019 | Deleting a flight orphaned its bookings | Passengers held bookings referencing a flight that no longer existed | Fixed |
| DEF-020 | `python:3.9-slim` (EOL Oct 2025); `--reload` in the image CMD; container ran as root | No security patches; the dev auto-reloader in production; breakout gets host root | Fixed |
| DEF-021 | `mongo:latest`; database port published to the host with no authentication | Unreproducible builds; the collection in DEF-003 reachable from the host | Fixed |
| DEF-022 | Only `pymongo` was pinned | Two builds of the same commit could install different code | Fixed |

---

## 5. Low

| ID | Finding | Status |
|---|---|---|
| DEF-023 | `__pycache__/` and a stray `flask.log` from the 2022 Flask original committed | Fixed |
| DEF-024 | Deprecated `@app.on_event` startup hooks | Fixed — lifespan |
| DEF-025 | No CI; no frontend tests; the backend suite could not reach the booking domain | Fixed — CI added, 6 tests → 47. Frontend tests deferred to Phase 2 |
| DEF-026 | Hero images hotlinked from Unsplash on every render | Fixed |
| DEF-027 | Calls to action were the same blue as links and headings | Fixed — see brandbook §3 |
| DEF-028 | No LICENSE | Fixed |
| DEF-029 | README claimed "production-ready" | Fixed — rewritten |
| DEF-030 | No pagination; every query hard-capped at 100 with no way to reach the rest | Fixed |

---

## 6. Deferred, by design

Not fixed in Phase 0, deliberately, because the Phase 1 migration to
PostgreSQL replaces the code they live in and fixing them twice is waste.

| Finding | Why deferred |
|---|---|
| ~~No true transaction around booking~~ | **Resolved in Phase 1.** Seat lock, seat state change and booking insert are one transaction; the compensating write is deleted |
| ~~No seat inventory model — only a scalar counter~~ | **Resolved in Phase 1.** `flight_seats` rows replace the counter; seat selection in the interface is Phase 2 |
| ~~No fare classes; one price per flight~~ | **Resolved in Phase 1.** Light, Standard and Flex, with their rules in data |
| No frontend test suite | Phase 2, alongside the booking-engine UI it would cover |

## 7. Accepted

| Finding | Rationale |
|---|---|
| `user_id` on bookings changed from email to the user's `_id` | A breaking change to existing booking documents. Accepted without a migration: the only data affected is demo seed data. Keying bookings to a mutable email was the actual defect |

---

## 8. What this changes about how the project is run

Three practices come out of the audit, and matter more than any individual
fix above.

**A test that cannot reach the code proves nothing.** Six passing tests
coexisted with a completely dead admin surface. The suite passed because it
only asked about the parts that worked. Coverage of the booking domain came
first in Phase 0, before any feature work.

**Configuration must fail loudly.** Every defect in DEF-004 was a silent
fallback — a default secret, an unconditional seed, a default password. The
application now refuses to start rather than start insecurely.

**Claims in the README are part of the deliverable.** "Production-ready"
was checkable, and false. Anything asserted about this project should be
verifiable by the reader; where it is not yet true, the roadmap says so.
