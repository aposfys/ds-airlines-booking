# Test Strategy

**DS Airlines · v1.0, Phase 0**

Replaces the previous `TESTING.md`, which was a list of manual click-through
steps and documented a mock-database mode (`USE_MOCK_DB=true`) that did not
exist anywhere in the source.

---

## 1. What went wrong, and what this strategy answers

The original suite was six tests. All six exercised the same two auth
endpoints. Nothing touched flights, bookings, or authorization — because
those needed a live MongoDB the tests had no way to provide.

The suite was green while the entire administrative surface returned 403 to
every caller (DEF-001). It was not a weak assertion that missed the bug; the
test suite could not reach the code the bug was in.

So the first principle here is **reachability before coverage**. A percentage
means nothing if whole domains are unreachable by construction.

---

## 2. Layers

| Layer | Tool | Runs against | Owns |
|---|---|---|---|
| **Unit** | pytest | Pure functions | Luhn, flight-code generation, password rules, contrast |
| **Service** | pytest + httpx ASGI | `tests/fake_mongo.py` | Endpoints, authorization, validation, inventory |
| **Component** *(Phase 2)* | Vitest + RTL | Mocked API | Forms, dialogs, error states |
| **End-to-end** *(Phase 2)* | Playwright | Full Docker stack | Register → search → book → cancel |
| **Accessibility** | `contrast_check.py`, axe *(Phase 2)* | Tokens, rendered pages | WCAG 2.2 AA |

### The in-memory database

`tests/fake_mongo.py` implements only the Motor surface the application
actually uses — `$gt`, `$regex`, `$inc`, `$set`, unique-index behaviour — and
deliberately nothing more. It exists so the booking domain is testable
without infrastructure, which is what makes the service layer viable at all.

**Its limits, stated plainly.** It is not MongoDB. It cannot catch driver
behaviour, real index semantics, or genuine concurrency. Tests that pass here
are evidence about *our* logic, not about the database. Phase 1's PostgreSQL
migration replaces it with a real database in a transactional fixture, which
is strictly better; the fake is a bridge, not a destination.

---

## 3. Entry and exit criteria

**A change may merge when:** CI is green (backend tests, frontend lint and
build, contrast check); every new endpoint has an authorization test for both
the permitted and the forbidden caller; and every Critical or High defect
fixed carries a regression test that fails against the old code.

**A release requires additionally:** the manual suite in §5 passing against a
full Docker stack, and no open Critical or High defects.

---

## 4. Automated cases

47 tests. Those tied to audit findings:

| ID | Case | Defect | File |
|---|---|---|---|
| TC-A01 | An administrator receives 200 from the admin dashboard | DEF-001 | `test_authorization.py` |
| TC-A02 | A passenger receives 403 from the admin dashboard | DEF-001 | `test_authorization.py` |
| TC-A03 | An anonymous caller receives 401 | DEF-001 | `test_authorization.py` |
| TC-A04 | An administrator can create a flight | DEF-001 | `test_authorization.py` |
| TC-A05 | A passenger cannot create a flight | DEF-001 | `test_authorization.py` |
| TC-A06 | Revoking admin takes effect before the token expires | DEF-002 | `test_authorization.py` |
| TC-A07 | A deactivated account loses access immediately | DEF-002 | `test_authorization.py` |
| TC-A08 | A deleted account loses access immediately | DEF-002 | `test_authorization.py` |
| TC-B01 | The full card number is never persisted | DEF-003 | `test_bookings.py` |
| TC-B02 | The response never echoes the card number | DEF-003 | `test_bookings.py` |
| TC-B03 | A card failing the Luhn checksum is rejected | DEF-003 | `test_bookings.py` |
| TC-B04 | Booking a full flight is rejected | DEF-007 | `test_bookings.py` |
| TC-B05 | Cancelling returns exactly one seat | DEF-007 | `test_bookings.py` |
| TC-B06 | Cancelling twice cannot credit a second seat | DEF-007 | `test_bookings.py` |
| TC-B07 | A passenger cannot cancel another's booking | — | `test_bookings.py` |
| TC-B08 | Bookings are scoped to the caller | — | `test_bookings.py` |
| TC-F01 | Regex metacharacters in search are treated literally | DEF-005 | `test_flights.py` |
| TC-F02 | Distinct routes cannot produce the same designator | DEF-006 | `test_flights.py` |
| TC-F03 | Pagination bounds are enforced | DEF-030 | `test_flights.py` |
| TC-F04 | A flight with bookings cannot be deleted | DEF-019 | `test_flights.py` |
| TC-U01 | The plaintext password is never stored | — | `test_auth.py` |
| TC-U02 | The response never exposes the hash | — | `test_auth.py` |
| TC-U03 | `is_admin` cannot be self-assigned at registration | — | `test_auth.py` |
| TC-U04 | A password without a digit is rejected | DEF-012 | `test_auth.py` |
| TC-U05 | A duplicate username is rejected | DEF-013 | `test_auth.py` |
| TC-U06 | Login errors do not reveal whether a user exists | — | `test_auth.py` |
| TC-U07 | `/auth/me` returns the real profile | DEF-016 | `test_auth.py` |

---

## 5. Manual cases

Run against a full Docker stack before release. Each is written so that a
tester who has never seen the code can execute it.

### TC-M01 · Registration rejects a weak password
**Pre:** app running, not signed in.
**Steps:** Go to `/register`; complete every field; enter `password` (no
digit); submit.
**Expected:** The account is not created; the message names the missing
requirement; the entered details are retained.

### TC-M02 · A booking shows only the last four digits
**Pre:** signed in, at least one flight available.
**Steps:** Select a flight; enter `4242 4242 4242 4242`; confirm; look at the
itinerary panel.
**Expected:** The booking appears reading `card ending 4242`. The full number
appears nowhere in the interface, and nowhere in the API response — check the
network panel.

### TC-M03 · A mistyped card is caught before submission
**Steps:** Select a flight; enter `4242 4242 4242 4243`; confirm.
**Expected:** An inline message asks the passenger to check the digits. No
request is sent.

### TC-M04 · Cancellation returns the seat
**Steps:** Note a flight's remaining seats; book it; observe the count drop
by one; cancel from the itinerary panel.
**Expected:** The count returns to its original value. The booking leaves the
panel without a page reload.

### TC-M05 · The interface makes no false affiliation claims
**Steps:** Read `/login`, `/register` and `/dashboard`.
**Expected:** No reference to Star Alliance, Miles+Bonus, or any real
airline, alliance or programme. Fares display in EUR.

### TC-M06 · Keyboard-only booking
**Steps:** Using only the keyboard, tab from the search field to a flight,
open the booking dialog, complete it, and confirm. Then reopen and press
Escape.
**Expected:** Focus is always visible; focus moves into the dialog on open;
Escape closes it. The whole flow is completable without a mouse.

### TC-M07 · The app refuses to start without a signing key
**Steps:** Unset `SECRET_KEY`; start the backend.
**Expected:** Startup fails with a message naming the variable and giving the
command to generate one. It does not start with a fallback key.

---

## 6. Not covered yet

Stated so that the gaps are known rather than implied.

- **No frontend tests.** Phase 2, with the booking-engine UI.
- **No load or concurrency testing.** The seat-oversell guard is tested
  logically, not under real contention — the fake database is single-threaded.
  Phase 1, against PostgreSQL.
- **No security scanning** in CI. Dependency and container scanning belong in
  Phase 1.
- **No contract testing** between frontend and API. TypeScript types are
  hand-written and can drift; generating them from the OpenAPI schema is the
  intended fix.
