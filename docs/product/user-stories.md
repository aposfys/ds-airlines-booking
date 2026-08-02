# User Stories

**DS Airlines · v1.0, August 2026**

Stories for what is built, with Gherkin acceptance criteria and a
traceability matrix mapping each to the endpoint that serves it and the test
that proves it.

Personas are [P1–P4](personas.md). Status is honest: **Done** means shipped
*and* covered by a named test; **Partial** means shipped with a stated
limitation; **Not started** means exactly that.

---

## Epic A · Account

### A1 · Register — P1, P2 · **Done**

> As a traveller, I want to create an account with my passport details, so
> that I do not have to re-enter them on every booking.

```gherkin
Scenario: Registering with valid details
  Given I am not signed in
  When I submit a valid email, username, full name, passport number
   and a password of 8+ characters containing a letter and a digit
  Then my account is created
   And I am returned to the sign-in page
   And my password is never stored in a readable form

Scenario: A password the interface promised to require
  When I submit the password "passwordonly"
  Then registration is refused
   And the message names the missing requirement

Scenario: An email that differs only in case
  Given an account exists for "ada@example.com"
  When I register with "ADA@EXAMPLE.COM"
  Then registration is refused as already registered

Scenario: Privilege cannot be claimed
  When I submit a registration including "is_admin": true
  Then the account is created without administrative privilege
```

### A2 · Sign in — P1, P2 · **Done**

> As a registered traveller, I want to sign in, so that I can see my
> itineraries.

```gherkin
Scenario: Correct credentials
  When I sign in with my username and password
  Then I receive a bearer token
   And the dashboard greets me by my real name

Scenario: Wrong credentials do not reveal which accounts exist
  When I sign in with a username that does not exist
   And separately with a real username and a wrong password
  Then both responses are identical in message and status

Scenario: A deactivated account
  Given my account has been deactivated
  When I sign in with correct credentials
  Then I am refused with an explanation
```

### A3 · See my own profile — P1, P2 · **Done**

> As a signed-in traveller, I want the interface to know who I am, so that it
> does not ask me for details it already has.

```gherkin
Scenario: The profile comes from the server
  Given I am signed in
  When the dashboard loads
  Then my full name and passport number come from my account record
   And are pre-filled when I book
```

---

## Epic B · Search

### B1 · Browse scheduled flights — P1, P2 · **Done**

> As a traveller, I want to see what DS flies, so that I can plan without
> signing in.

```gherkin
Scenario: Anonymous browsing
  Given I am not signed in
  When I request the flight list
  Then I see scheduled flights with route, date, times and duration

Scenario: Cancelled flights are not offered
  Given a flight has been cancelled
  Then it does not appear in search results
```

### B2 · Filter by route — P1, P2 · **Done**

> As a traveller, I want to filter by airport, so that I only see flights I
> could take.

```gherkin
Scenario: Filtering by origin and destination
  When I search with origin "ATH" and destination "LHR"
  Then I see only Athens to London flights

Scenario: Codes are case-insensitive
  When I search with origin "ath"
  Then I see the same results as "ATH"

Scenario: Search terms are not patterns
  When I search with origin ".*"
  Then I see no results
```

### B3 · Compare fares before choosing — P1, P2 · **Done**

> As a traveller, I want to see what each fare includes, so that I can judge
> the total rather than the headline.

```gherkin
Scenario: A price per fare class
  When I view a flight
  Then I see Light, Standard and Flex, each with its own price
   And each states whether bags, changes and refunds are included
   And every fare includes a cabin bag

Scenario: Prices follow the flight's base fare
  Given Light is x1.00, Standard x1.45 and Flex x2.10
  When the base fare is EUR 129.00
  Then the fares are EUR 129.00, EUR 187.05 and EUR 270.90
```

---

## Epic C · Booking

### C1 · Book a seat — P1, P2 · **Done**

> As a signed-in traveller, I want to book a seat on a chosen fare, so that I
> can fly.

```gherkin
Scenario: A confirmed booking
  Given I am signed in and a flight has seats available
  When I confirm a booking with a fare, passenger name and passport
  Then the booking is confirmed with a six-character reference
   And exactly one seat is consumed
   And the reference contains none of I, O, 0 or 1

Scenario: No payment details are accepted
  When I submit a booking including a card number
  Then the request is refused
   And no card data is stored in any form

Scenario: The last seat cannot be sold twice
  Given one seat remains
  When two bookings are attempted concurrently
  Then exactly one succeeds and the other is told the flight is full
```

### C2 · Choose a specific seat — P1, P2 · **Partial**

> As a traveller, I want to pick my seat, so that I am not assigned one I do
> not want.

```gherkin
Scenario: Requesting a seat by number
  When I request seat "12A" and it is available
  Then my booking holds seat 12A

Scenario: A seat already taken
  Given seat 12A is booked
  When I request seat 12A
  Then I am told it is not available
```

**Limitation:** a seat is requested by typing its number. There is no seat
map, so a traveller cannot see which seats are free, or which are window,
aisle or exit row — all of which the database already knows
(`seat_map_entries`). Phase 2.

### C3 · See my itineraries — P1, P2 · **Done**

> As a traveller, I want to see what I have booked, so that I can check the
> details before I travel.

```gherkin
Scenario: My bookings and only mine
  Given another traveller has bookings
  When I view my itineraries
  Then I see only my own

Scenario: What each itinerary shows
  Then I see the route, flight number, date, reference, fare and amount paid
   And no payment card information anywhere
```

### C4 · Cancel a booking — P1, P2 · **Done**

> As a traveller, I want to cancel, so that the seat is released and my plans
> can change.

```gherkin
Scenario: Cancelling
  When I cancel a confirmed booking
  Then it is marked cancelled rather than deleted
   And its seat returns to inventory

Scenario: Cancelling twice
  When I cancel the same booking again
  Then I am told it is already cancelled
   And no second seat is credited back

Scenario: Someone else's booking
  When I attempt to cancel a booking that is not mine
  Then I receive a not-found response
```

**Limitation:** cancellation ignores the fare's refund rules. Light is
non-refundable in data and in the brand, but cancelling it returns the seat
and records nothing about money owed. Refund policy is Phase 2; charging and
returning money is Phase 3.

---

## Epic D · Operations — P3

### D1 · Publish a flight — **Done (API only)**

> As revenue and operations, I want to publish a flight on an existing route,
> so that it can be sold.

```gherkin
Scenario: Publishing
  Given I am an administrator
  When I publish a flight number on a route, date, time and aircraft
  Then the flight is created with its full cabin available
   And arrival is derived from the route's scheduled duration

Scenario: The same number twice in one day
  Then the second is refused

Scenario: A passenger attempting the same
  Then the request is refused as unauthorised
```

### D2 · Reprice a flight — **Done (API only)**

```gherkin
Scenario: Repricing an empty flight
  Then the new base fare applies and every fare class moves with it

Scenario: Repricing a flight with passengers
  Then the request is refused
```

### D3 · Withdraw a flight — **Done (API only)**

```gherkin
Scenario: Deleting an empty flight
  Then it is removed

Scenario: Deleting a flight with bookings
  Then the request is refused and I am told to cancel it instead

Scenario: Cancelling a flight
  Then it disappears from search and can no longer be booked
```

### D4 · See how the airline is selling — **Done (API only)**

```gherkin
Scenario: The operations summary
  Then I see flights, confirmed bookings, revenue, seats sold and load factor
```

### D5 · An interface for any of the above — **Not started**

> As revenue and operations, I want to do my job without Swagger.

Phase 4. Everything in D1–D4 is reachable only through the API documentation
page. This is the largest gap between what the product does and what a person
could use.

---

## Epic E · Cross-cutting

### E1 · Read the interface in either theme — all · **Done**

```gherkin
Scenario: Choosing a theme
  When I press the theme control
  Then the interface switches between dark and light
   And my choice persists across reloads and pages

Scenario: Following the system
  Given I have not chosen a theme
  Then the interface follows the operating system's preference

Scenario: Contrast in both
  Then every shipped colour pair meets WCAG 2.2 AA in both themes
```

### E2 · Book without a mouse — all · **Partial**

```gherkin
Scenario: Keyboard-only booking
  When I complete a booking using only the keyboard
  Then focus is always visible
   And focus moves into the booking dialog when it opens
   And Escape closes it
```

**Limitation:** verified by hand (TC-M41), not automated. Focus is not
trapped inside the dialog — tabbing past the last control leaves it. Phase 2.

### E3 · Not lose work to a failure — all · **Done**

```gherkin
Scenario: A failed booking
  When a booking cannot be completed
  Then I am told what happened and that nothing has been charged
   And no seat is consumed
   And no internal error detail is exposed to me
```

---

## Traceability

Story → endpoint → the test that proves it. Manual cases (TC-M*) are in
[the test strategy](../qa/test-strategy.md).

| Story | Endpoint | Automated | Manual |
|---|---|---|---|
| A1 | `POST /api/auth/register` | `test_auth.py::TestRegistration` | TC-M06–M10 |
| A2 | `POST /api/auth/login` | `test_auth.py::TestLogin` | TC-M01–M03 |
| A3 | `GET /api/auth/me` | `test_auth.py::TestCurrentUser` | TC-M01 |
| B1 | `GET /api/flights/` | `test_flights.py::TestSearch` | TC-M11 |
| B2 | `GET /api/flights/?origin=&destination=` | `test_flights.py::TestSearch` | TC-M12–M14 |
| B3 | `GET /api/flights/` | `test_flights.py::TestSearch::test_search_returns_a_price_per_fare_class` | TC-M15, M17–M18 |
| C1 | `POST /api/bookings/` | `test_bookings.py::TestSeatInventory`, `TestCardHandling`, `TestBookingReference` | TC-M19–M22 |
| C2 | `POST /api/bookings/` | `test_bookings.py::test_a_specific_seat_can_be_requested` | TC-M23 |
| C3 | `GET /api/bookings/` | `test_bookings.py::TestOwnership` | TC-M26 |
| C4 | `DELETE /api/bookings/{id}` | `test_bookings.py::TestCancellation` | TC-M24–M25 |
| D1 | `POST /api/flights/` | `test_flights.py::TestFlightCreation`, `test_authorization.py` | TC-M30–M31 |
| D2 | `PATCH /api/flights/{id}` | `test_flights.py::TestRepricing` | — |
| D3 | `DELETE /api/flights/{id}` | `test_flights.py::TestDeletion` | TC-M32 |
| D4 | `GET /api/admin/dashboard` | `test_authorization.py::TestAdminAccess` | TC-M27–M29 |
| D5 | — | — | — |
| E1 | — | `contrast_check.py` | TC-M05, M39–M40 |
| E2 | — | — | TC-M41 |
| E3 | all | `test_bookings.py`, `test_auth.py` | — |

**Rows worth reading as gaps:** D2 has no manual case because there is no
interface to exercise it in. D5 has nothing at all. E2 has no automated
coverage, and E1's automated coverage checks the palette, not the pages.
