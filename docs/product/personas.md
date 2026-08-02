# Personas

**DS Airlines · v1.0, August 2026**

Four people the product is built for. Each exists because a real design
decision in this codebase turns on them; a persona that changes nothing is
decoration, so the entries below end with what they cost us.

The network — Athens and Thessaloniki to seven European cities, single
A321neo fleet, point-to-point only — constrains all of them. See
[the product brand](../brand/brandbook.md#23-operating-profile).

---

## P1 · Eleni — the leisure traveller

**35, teacher, Athens. Flies 2–3 times a year, always paying her own money.**

Books six to ten weeks ahead for a summer trip to Barcelona or a long weekend
in Rome. Compares DS against Aegean and Ryanair on total price, not headline
price, because she has been caught before by a bag that cost more than the
seat.

Travels with one cabin bag and occasionally a checked one. Does not care
where she sits as long as it is not the middle seat. Books on a laptop in the
evening, sometimes finishing on a phone.

> "I don't mind paying a bit more. I mind finding out at the airport."

**What she needs:** the real total before committing; to know whether a bag
is included without opening a second page; confidence the booking is
confirmed.

**What she fears:** hidden fees; a fare that changes between search and
payment; losing the money if plans change.

**What she costs us:** Light fare includes a cabin bag, so the headline price
is closer to the real one. Search returns a price per fare class rather than
one teaser number. Fares are derived from the flight's base fare by
multiplier, so repricing moves every class together and cannot leave one
inconsistent.

---

## P2 · Dimitris — the SME business traveller

**48, sales director for a Thessaloniki manufacturer. Flies SKG–Frankfurt or
SKG–Munich eight to twelve times a year.**

Books late, often two or three days out, and his plans change. Not a
corporate-travel-policy flyer — a small company where he books it himself and
the cost is visible to him. He will pay materially more for the ability to
move a flight, because a wasted trip costs far more than the fare.

Wants a seat near the front and an aisle. Needs the booking reference where
he can find it, fast, standing at a desk.

> "Just tell me whether I can change it."

**What he needs:** to see change and refund rules while choosing, not after;
seat selection; a reference he can read out over the phone.

**What he fears:** a non-changeable fare bought by accident; discovering the
change fee exceeds the fare.

**What he costs us:** fare rules travel with the fare in search results, so
`changeable` and `refundable` are visible at the point of choice. Booking
references avoid I, O, 0 and 1, because he reads them aloud. A refundable
fare must also be changeable — enforced by
`ck_fare_class_refundable_implies_change`, so the combination that would
confuse him is unrepresentable.

---

## P3 · Sofia — revenue and operations

**41, works for the airline. The only persona with an account that matters.**

Owns the schedule and the fares. Publishes flights, adjusts pricing against
booking curves, and cancels when an aircraft goes technical. Needs to know
load factor by route without asking anyone.

Her tolerance for a broken tool is zero, because the alternative is a
spreadsheet and a phone call.

> "If I can't reprice before the curve moves, the seat sells at the wrong
> price."

**What she needs:** to publish and withdraw flights; to reprice; load factor
and revenue by route; certainty that an action either happened or did not.

**What she fears:** repricing a flight that already carries passengers;
deleting something that turns out to have bookings; a change that half
applied.

**What she costs us:** repricing a flight with booked seats is refused (409).
Deleting a flight with bookings is refused *by the database*, not by a check
that could race. Booking is one transaction. Admin privilege is read from her
record on every request, so revoking it takes effect immediately.

**She is also the largest open gap in the product.** Sofia has no interface —
every one of her tasks runs through Swagger. Phase 4.

---

## P4 · Yannis — the reviewer

**Not a passenger. A hiring manager or engineer opening this repository.**

Reads the README, skims the tests, opens one or two source files, and forms a
judgement in under ten minutes. He is the reason the defect register exists
and the reason claims in this repository have to be checkable.

> "It says production-ready. Is it?"

**What he needs:** to run it in one command; to find the reasoning behind
decisions; to see honest accounting of what is not done.

**What he fears:** wasting time on a project that overstates itself.

**What he costs us:** `make check` runs everything CI runs. Every phase is
described with what it did *not* cover. The README no longer claims the
project is production-ready, because that claim was checkable and false.

---

## Explicitly not served

Naming these keeps scope honest.

| | Why not |
|---|---|
| **Connecting passengers** | The network is point-to-point and the schema models a single dated leg. An itinerary graph is a different product. |
| **Families and groups** | One booking is one passenger in one seat. Group booking needs a party model and shared payment. |
| **Corporate travel managers** | Needs policy enforcement, cost centres and consolidated invoicing. |
| **Cabin crew and dispatch** | Crew rostering and weight-and-balance are airline operations, not booking. |
| **Accessibility-assistance requests** | Wheelchair and special-assistance booking is a genuine passenger need this product does not yet meet — an omission, not a decision. It belongs in Phase 2 alongside seat selection. |
