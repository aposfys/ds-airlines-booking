# DS Airlines — Product Brand

**Version 2.0 · August 2026**

DS Airlines has no visual identity of its own. It is a product built on
**[AF](../../frontend/src/design-system/README.md)**, the design system by
Apostolos Fysekidis, and AF owns everything you can see: colour, type, space,
motion, elevation, the accessibility floor.

This document owns the other half — what the airline *is* and what it *says*.
Name, positioning, network, fare architecture, voice, and the words on
screen.

> **Version 1.0 of this document proposed a full visual identity** — a navy
> and ochre palette, Inter throughout, a light ground, two shadow levels.
> That was written before AF was on the table, and it is superseded. Where
> the two disagreed, AF won, because a house system applied to a product is a
> stronger artefact than a one-off palette invented for a fictional airline.

---

## 1 · The split

| Owned by AF | Owned here |
|---|---|
| Colour, and every semantic alias | The name, and what DS stands for |
| Type: Archivo and IBM Plex Mono | Positioning and the competitive wager |
| Space, radius, elevation, motion | Network, fleet, currency |
| Component behaviour and states | Fare architecture and what each fare promises |
| WCAG 2.2 AA floor | Voice, tone, and every string on screen |
| Dark ground, Signal, hairlines | Naming of passenger-facing concepts |

The rule for anything not listed: **if it can be seen, AF decides; if it can
be read, this document decides.**

---

## 2 · The airline

### 2.1 What DS stands for

**DS Airlines** trades as **Delos Skyways**.

Delos is the Cycladic island Greek myth names as Apollo's birthplace, and for
centuries it sat at the commercial centre of the Aegean — a small island
whose entire significance came from being the place everything passed
through. That is the airline: not the largest carrier in the market, the one
the Aegean routes through.

The initials carry the operating history. Delos Skyways is the trading name;
DS is the designator on the aircraft, in the flight numbers, and in the API.

### 2.2 Positioning

> **Delos Skyways is the dependable Aegean connector: full-service
> reliability on short-haul European routes, without the full-service price.**

The market splits in two and serves the middle badly.

| | Legacy full-service | **Delos Skyways** | Ultra-low-cost |
|---|---|---|---|
| Fare | Premium | **Mid** | Lowest headline |
| Cabin bag | Included | **Included, every fare** | Paid extra |
| Seat selection | Free | **Included from Standard** | Paid, opaque |
| Changes | Flexible | **Free on Flex** | Punitive |
| Airports | Primary | **Primary** | Secondary |

The wager: someone flying Athens–Munich twice a year does not want to gamble
on whether their bag will cost more than their seat. They want the total
knowable at the point of search. That is why every fare in §2.4 includes a
cabin bag, and why search returns a price per fare class rather than a single
teaser number.

### 2.3 Operating profile

These facts constrain the product, not just the copy.

- **Hubs:** Athens (ATH) and Thessaloniki (SKG).
- **Network:** seven point-to-point European short-haul routes. No long-haul,
  no connecting itineraries — which is why the booking engine models a single
  dated leg rather than an itinerary graph.
- **Fleet:** single-type, Airbus A321neo, 220 seats, five airframes
  (SX-DLA … SX-DLE). One type keeps crew training and spares costs down.
- **Currency:** EUR throughout. The interface once rendered fares with a `$`
  prefix, which was wrong for every route the airline flies.

### 2.4 Fare architecture

Three branded fares. The multipliers apply to the flight's base fare, so
repricing a flight moves every fare with it.

| | Light | Standard | Flex |
|---|---|---|---|
| Multiplier | ×1.00 | ×1.45 | ×2.10 |
| Cabin bag | ✓ | ✓ | ✓ |
| Checked bag | — | ✓ | ✓ |
| Seat selection | — | ✓ | ✓ |
| Changeable | — | ✓ (€35) | ✓ (free) |
| Refundable | — | — | ✓ |

One rule is enforced by the database rather than by policy: **a refundable
fare must also be changeable.** A fare you can get money back from but cannot
move is not a product we sell, so `ck_fare_class_refundable_implies_change`
makes it unrepresentable.

### 2.5 What we never claim

The interface previously described DS Airlines as **"A Star Alliance Member"**
and advertised **"Miles+Bonus"**. Both were removed in Phase 0.

Star Alliance is a real alliance with real members; Miles+Bonus is the
registered loyalty programme of Aegean Airlines. A fictional carrier
displaying either is trademark appropriation, and in a public repository it
reads as copied rather than designed.

DS Airlines belongs to no alliance. Its loyalty programme is **Meltemi Club**.

---

## 3 · Voice

AF's content rules apply — short declarative sentences, concrete nouns, no
salesmanship, no emoji, no Title Case. What follows is what that sounds like
when an airline says it.

Calm, specific, in the passenger's terms. Say what happened and what to do
next. Never blame the passenger, never use an exclamation mark, never use
urgency as a sales device.

| Instead of | Write |
|---|---|
| "Booking successful!" | "Booked. Your reference is RGLG3K." |
| "Error!" | "That card was declined. Try another, or contact your bank." |
| "Invalid input" | "Enter the passport number exactly as printed, without spaces." |
| "Only 2 seats left — book now!" | "2 seats remain." |
| "Oops! Something went wrong :(" | "We couldn't reach the payment provider. Nothing has been charged." |

### 3.1 Rules for failure messages

1. **State what happened**, in the passenger's terms, not the system's.
2. **State the money position** whenever payment is involved. "Nothing has
   been charged" is the sentence people are looking for.
3. **Give one next action.** If recovery is impossible, say who to contact.
4. **Never expose internals.** The API once returned
   `Internal Server Error: {exception}` straight to the client (DEF-010).

### 3.2 Naming things

Passenger-facing terms are fixed. Inconsistency between them is how an
interface starts to feel untrustworthy.

**booking** (not reservation or order) · **fare** (not price or cost) ·
**passenger** (not user or customer) · **itinerary** (a passenger's set of
booked flights) · **flight** (a single dated leg) · **booking reference**
(not PNR, which is internal vocabulary).

**Booking references** are six characters from a 32-symbol alphabet with
**I, O, 0 and 1 removed**. A reference gets read aloud over the phone and
written on paper; those four are where transcription goes wrong.

---

## 4 · Accessibility

AF's standard — [`accessibility.md`](../../frontend/src/design-system/accessibility.md),
WCAG 2.2 AA, non-negotiable — is inherited whole. Two things are enforced
mechanically rather than by review:

**Contrast.** [`contrast_check.py`](contrast_check.py) reads the palette out
of the token files the application actually loads, converts OKLCH to linear
sRGB, composites translucent values over their background, and checks 17
pairs in **both** themes. It runs in CI and fails the build.

It found two real failures in AF's light theme, both now corrected in
[`overrides.css`](../../frontend/src/design-system/overrides.css) and both
candidates to upstream:

- `--status-warning-fg` measured **4.18:1** on the warning surface, under the
  4.5:1 floor for the "N seats remain" notice. Darkened to 4.95:1.
- `--action-secondary-border` measured **1.56:1** over paper. That token is
  the outline of a transparent button — the only thing marking where the
  control is — so WCAG 2.2 SC 1.4.11 requires 3:1. Raised to 3.45:1, keeping
  the translucent treatment. Deliberately *not* applied to `--border-strong`,
  which carries dividers and is exempt.

The dark theme, which is what ships today, passed every pair unaided.

**Targets and focus.** Controls are 44px minimum; the focus ring is AF's,
2px, and never removed. `prefers-reduced-motion` collapses motion in AF's
base layer.

### Open items

- **Theme switching** is not exposed. Both themes are token-complete and both
  pass contrast, but nothing in the interface toggles `data-theme`.
- **Photography** direction is unwritten. The pages once hotlinked a stock
  photograph from Unsplash on every render; that is gone, and AF's grain over
  full-bleed colour stands in until owned or licensed assets exist.
- **No logo.** AF ships no mark by design, and DS Airlines has not been given
  one. The name is set in type — Archivo 800, uppercase — wherever a mark
  would go.
