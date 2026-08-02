# Test Strategy

**DS Airlines · v2.0, Phase 1**

Replaces v1.0, which described `tests/fake_mongo.py` — the in-memory stand-in
built in Phase 0 and retired in Phase 1, as ADR-001 promised.

---

## 1 · What went wrong, and what this answers

The original suite was six tests. All six exercised the same two auth
endpoints. Nothing touched flights, bookings, or authorization — because
those needed a live MongoDB the tests had no way to provide.

The suite was green while the entire administrative surface returned 403 to
every caller (DEF-001). It was not a weak assertion that missed the bug: the
test suite could not reach the code the bug was in.

So the first principle is **reachability before coverage**. A percentage
means nothing if whole domains are unreachable by construction.

The second, learned in Phase 1: **a test that never renders the page cannot
see the page.** Four defects in this phase were found only by opening a
browser — see §5.

---

## 2 · Layers

| Layer | Tool | Runs against | Owns |
|---|---|---|---|
| **Unit** | pytest | Pure functions | Booking-reference alphabet, fare arithmetic, password rules |
| **Service** | pytest + httpx ASGI | **Real PostgreSQL** | Endpoints, authorization, validation, seat inventory |
| **Integrity** | pytest | **Real PostgreSQL** | Constraints, asserted by attempting the violation |
| **Accessibility** | `contrast_check.py` | The shipped token files | WCAG 2.2 AA, both themes |
| **Manual** | A browser | Full stack | Everything in §4 |
| **Component** | Vitest + RTL | Mocked API | Forms, dialogs, contexts, formatting |
| **End-to-end** | Playwright | **The real stack** | The passenger journey, fonts, themes, routing, a11y |

### Why the fake is gone

`fake_mongo.py` was honest about being a bridge: tests passing against it
were evidence about *our logic*, not about the database. It could not catch
driver behaviour, real index semantics, or genuine concurrency.

Fixtures now build the schema by **running the Alembic migrations**, so every
test run also proves the migration chain applies — which is the drift risk
ADR-001 names. Each test runs inside a transaction that is rolled back, with
`join_transaction_mode="create_savepoint"` so the application's own commit
takes its normal path and is still undone.

---

## 3 · Running everything

```bash
make check       # backend + component tests, lint, build, contrast
make check-all   # the above plus the end-to-end suite
```

Individually:

```bash
make test       # 89 backend tests against real PostgreSQL
make lint       # eslint
make build      # tsc + vite, also proves the fonts resolve
make contrast   # 34 colour pairs, both themes
```

First time on a machine:

```bash
make setup      # venv, npm ci, database cluster, migrations
make seed       # demo flights and an administrator
make dev        # API on :8000, interface on :5173
```

`make up` runs the whole thing in Docker instead and needs nothing installed.

---

## 4 · Manual pass — every page

Run against `make dev` with `make seed` already applied. Each case is written
so a tester who has never seen the code can execute it.

The application has **four routes**. The administrative surface has **no
interface at all** — it is API-only, so §4.5 drives it through Swagger. That
is a real gap, not an oversight in this document.

### 4.1 · `/login`

| ID | Case | Expected |
|---|---|---|
| TC-M01 | Sign in with `ada` / `password123` | Lands on `/dashboard`, nav shows the real full name — not the literal "User" (DEF-016) |
| TC-M02 | Sign in with a wrong password | "That username and password do not match." Stays on the page, username retained |
| TC-M03 | Sign in with a username that does not exist | **The same message as TC-M02.** A different one would confirm which accounts exist |
| TC-M04 | Read the editorial panel | No reference to Star Alliance, Miles+Bonus, or any real airline or alliance (DEF-014) |
| TC-M05 | Press the theme toggle | Whole page inverts; the button label switches between LIGHT and DARK |

### 4.2 · `/register`

| ID | Case | Expected |
|---|---|---|
| TC-M06 | Register with password `password` (no digit) | Rejected, message names the missing requirement. The UI once promised this rule while the API enforced nothing (DEF-012) |
| TC-M07 | Register with password `12345678` (no letter) | Rejected |
| TC-M08 | Register with an existing username | "Email or username is already registered" |
| TC-M09 | Register with `ADA@EXAMPLE.COM` when `ada@example.com` exists | Rejected. Uniqueness is case-insensitive; the Mongo index was not |
| TC-M10 | Register successfully | Redirected to `/login`, new credentials work |

### 4.3 · `/dashboard` — search and results

| ID | Case | Expected |
|---|---|---|
| TC-M11 | Load with no filters | Seven demo flights, each with IATA pair, flight number, date, times, duration |
| TC-M12 | Type `ATH` in From | List narrows to Athens departures within ~300ms, without a page reload |
| TC-M13 | Type `.*` in From | **No results.** Not "everything". Search takes IATA codes and does no pattern matching (DEF-005) |
| TC-M14 | Type `ath` lowercase | Same results as `ATH` |
| TC-M15 | Check fares on a card | A "from" price showing the cheapest fare, in **EUR** — never `$` (DEF-015) |
| TC-M16 | Count primary buttons | Exactly zero vermilion buttons in the list. Row actions are secondary; AF allows one primary per view |

### 4.4 · `/dashboard` — booking and itineraries

| ID | Case | Expected |
|---|---|---|
| TC-M17 | Press Select | Dialog opens showing three fares with prices and what each includes |
| TC-M18 | Compare Light and Flex | Flex costs 2.10× Light and is the only one marked refundable |
| TC-M19 | Look for a card field | **There is none.** A demonstration notice states no payment is taken. Do not enter real payment details anywhere (DEF-003) |
| TC-M20 | Confirm a booking | Dialog closes; a confirmation names the six-character reference; it appears under My itineraries |
| TC-M21 | Read the reference | Six characters, none of them I, O, 0 or 1 — those are where transcription fails |
| TC-M22 | Note seats, book, re-check | Seat count drops by exactly one |
| TC-M23 | Request seat `12A`, then request it again | Second attempt refused: "Seat 12A is not available" |
| TC-M24 | Cancel a booking | Status becomes Cancelled, seat count returns to its original value |
| TC-M25 | Cancel the same booking again | Refused. The seat count does **not** increase a second time |
| TC-M26 | Check the itinerary panel | Shows reference, fare, seat and fare paid. **No card digits anywhere** |

### 4.5 · Administration — Swagger only

There is no admin interface. Open `http://localhost:8000/docs`, press
**Authorize**, and sign in as the seeded administrator.

| ID | Case | Expected |
|---|---|---|
| TC-M27 | `GET /api/admin/dashboard` as the administrator | **200**, with flight count, bookings, revenue and load factor. This returned 403 to everyone before Phase 0 (DEF-001) |
| TC-M28 | The same call authorised as `ada` | 403 |
| TC-M29 | The same call with no token | 401 |
| TC-M30 | `POST /api/flights/` as the administrator | 201, and `seats_available` is 220 — the cabin is materialised |
| TC-M31 | Repeat with the same number and date | 409 |
| TC-M32 | `DELETE` a flight that has bookings | 409, "cancel it instead". The database refuses this, not a handler (DEF-019) |
| TC-M33 | `POST /api/bookings/` with an extra `credit_card` field | **422.** Payment details are refused, not silently ignored |
| TC-M34 | `POST /api/admin/admins`, then log in as that account | Login succeeds. It returned 500 forever before (DEF-008) |

### 4.6 · Routing, session and theme

| ID | Case | Expected |
|---|---|---|
| TC-M35 | Visit `/dashboard` signed out | Redirected to `/login` |
| TC-M36 | Visit `/` signed in | Redirected to `/dashboard` |
| TC-M37 | Delete the `token` key from localStorage, reload | Treated as signed out |
| TC-M38 | Wait past 30 minutes, then act | Session ends and returns to `/login` |
| TC-M39 | Set theme to light, reload, navigate | Choice persists across reloads and routes |
| TC-M40 | Clear `ds-theme`, set the OS to light, reload | Follows the system preference |
| TC-M41 | Book a flight using only the keyboard | Focus always visible; focus enters the dialog on open; Escape closes it; the flow completes without a mouse |
| TC-M42 | Start the API with `SECRET_KEY` unset | Refuses to start, naming the variable and how to generate one (DEF-004) |

---

## 5 · Why the manual pass exists

Everything in §4.3–4.4 concerning appearance was found by rendering the
pages, after the automated suite was already green. Phase 1 alone:

- Every flight row carried a primary vermilion button — N rows meant N
  equally urgent calls to action, spending the colour that means "act".
- The demonstration notice used the `info` role, which AF derives from the
  Signal ramp, so it rendered vermilion and read as an error.
- The `@theme` bridge aliased spacing selectively, and AF's scale diverges
  from Tailwind's above step 6, so `p-7` and `p-8` both resolved to 2rem.
- The webfonts did not resolve in the production build. Archivo and Plex Mono
  fell back to Helvetica **with no build error** — the entire typographic
  identity, silently absent.

None of these are expressible as a passing or failing assertion in the
unit suite. The end-to-end suite in §6 is the answer to most of them; §4
remains the control for the rest.

---

## 6 · The automated suites

**175 automated tests across three suites**, all running in CI.

| Suite | Count | What it can see |
|---|---|---|
| Backend (pytest) | 89 | Endpoints, authorization, inventory, database constraints |
| Component (Vitest) | 69 | Rendering, state, validation, formatting, contexts |
| End-to-end (Playwright) | 17 | Everything only a real browser can observe |

The end-to-end suite exists because of §5. It asserts the things that were
silently broken while every other suite was green:

- **Fonts actually load.** It counts `.woff2` responses and calls
  `document.fonts.check()`. Nothing else catches the identity falling back
  to Helvetica.
- **Nothing 404s** on any page.
- **Both themes apply**, persist across a reload, and follow the OS.
- **The focus ring is visible**, targets clear 44px, every input has an
  accessible name, and the page declares a language.
- **The card field does not exist**, and the API returns 422 to one.

---

## 7 · Not covered yet

Stated so the gaps are known rather than implied.

- **No load or concurrency testing.** The seat guard uses `SELECT … FOR
  UPDATE` and is correct by construction, but it has not been tested under
  real contention. The end-to-end suite runs single-worker against one
  database for the same reason.
- **No admin interface**, so §4.5 runs through Swagger. Not built — see the
  README on scope.
- **No automated axe scan.** The accessibility cases here are hand-written
  checks of specific rules, not a full audit.
- **One browser.** Playwright runs Chromium only; Firefox and WebKit are a
  config change away but are not run.
- **No security scanning** in CI. Dependency and container scanning were not
  added.
- **No contract testing** between frontend and API. The TypeScript types are
  hand-written and can drift — the `card_last4` type said `string` while the
  API had started returning `null`, and only the build caught it. Generating
  them from the OpenAPI schema is the intended fix.
