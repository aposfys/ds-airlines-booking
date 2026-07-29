# DS Airlines — Brand Book

**Version 1.0 · July 2026**

This document is the single source of truth for how DS Airlines looks, sounds
and behaves. It is not decoration: the colour, type and spacing values below
are defined once in [`frontend/src/index.css`](../../frontend/src/index.css)
as CSS custom properties and consumed everywhere through Tailwind utilities.
Changing a value here means changing it there — and nowhere else.

---

## 1. The brand

### 1.1 What DS stands for

**DS Airlines** trades as **Delos Skyways**.

Delos is the Cycladic island that Greek myth names as the birthplace of
Apollo, and it sat for centuries at the commercial centre of the Aegean — a
small island whose entire significance came from being the place everything
passed through. That is the airline: not the largest carrier in the market,
but the one the Aegean routes through.

The initials are retained because they carry the operating history. Delos
Skyways is the trading name; DS is the IATA-style designator and the name
that appears in code, on the aircraft and in the API.

### 1.2 Positioning

> **Delos Skyways is the dependable Aegean connector: full-service
> reliability on short-haul European routes, without the full-service price.**

The market splits into two camps and serves the middle badly.

| | Legacy full-service | **Delos Skyways** | Ultra-low-cost |
|---|---|---|---|
| Fare | Premium | **Mid** | Lowest headline |
| Bag included | Yes | **Yes, cabin bag** | Paid extra |
| Seat selection | Free | **Paid, transparent** | Paid, opaque |
| Change policy | Flexible | **Flexible on Flex fare** | Punitive |
| Schedule | Dense | **Point-to-point, reliable** | Off-peak slots |
| Airports | Primary | **Primary** | Secondary |

The strategic wager is that a traveller flying Athens–Munich twice a year
does not want to gamble on whether their bag will cost more than their seat.
They want the total to be knowable at the point of search.

### 1.3 Operating profile

These facts are load-bearing — they constrain the product, not just the copy.

- **Hubs:** Athens (ATH) and Thessaloniki (SKG).
- **Network:** point-to-point European short-haul. No long-haul, no
  connecting itineraries in v1 — which is why the booking engine models a
  single flight leg rather than an itinerary graph.
- **Fleet:** single-type, Airbus A321neo, 220 seats. One aircraft type keeps
  crew training, spares and maintenance costs down; it is also why
  `DEFAULT_SEAT_CAPACITY` is a constant rather than a per-aircraft lookup.
- **Currency:** EUR throughout. The interface previously displayed fares
  with a `$` prefix, which is wrong for every route the airline operates.

### 1.4 Brand values

**Legible.** The passenger always knows what they have bought. Total price,
change rules and baggage allowance are visible before payment, not after.

**Composed.** Aviation is stressful enough. Nothing in the product shouts,
uses urgency countdowns, or manufactures scarcity.

**Grounded.** Mediterranean, not generic-corporate. The airline is from
somewhere specific, and the identity should be unmistakable about where.

### 1.5 What we never claim

The interface previously described DS Airlines as **"A Star Alliance
Member"** and advertised a loyalty programme called **"Miles+Bonus"**. Both
were removed in Phase 0.

Star Alliance is a real alliance with real members, and Miles+Bonus is the
registered loyalty programme of Aegean Airlines. A fictional carrier
displaying either is trademark appropriation, and in a public portfolio
repository it reads as copied rather than designed. DS Airlines belongs to no
alliance. Its loyalty programme, when one exists, is **Meltemi Club**.

---

## 2. Logo

The wordmark is `DS` in Inter SemiBold with `0.08em` letter-spacing, set
beside the mark, with `Delos Skyways` available as a descender line in
Inter Light for contexts where the full name needs to appear.

The mark is a **stylised wing over a horizon line** — a single stroke that
reads as both a wing and the island rising out of the sea.

- Master asset: [`logo.svg`](logo.svg)
- Minimum clear space on all sides: the height of the `D`.
- Minimum size: 24 px tall for the mark alone, 96 px wide for the lockup.

**Do not:** stretch it, rotate it, apply gradients or drop shadows,
recolour it outside the palette below, or place the navy lockup on any
background darker than Aegean Mist. On dark backgrounds use the Cycladic
White version.

---

## 3. Colour

### 3.1 Core palette

| Token | Name | Hex | Use |
|---|---|---|---|
| `--color-primary` | Delos Navy | `#002A5C` | Headers, nav, primary text on light, brand surfaces |
| `--color-secondary` | Meltemi Blue | `#0072C6` | Links, focus rings, secondary actions |
| `--color-signal` | Kouros Ochre | `#A8530C` | Primary call to action, price emphasis |
| `--color-signal-light` | Kouros Ochre Light | `#E0752D` | The same role, on navy surfaces only |
| `--color-surface` | Cycladic White | `#FFFFFF` | Cards, form fields |
| `--color-accent` | Aegean Mist | `#F0F4F8` | Page background, inset panels |
| `--color-dark` | Marble | `#1A1A1A` | Body copy |

Navy and Meltemi Blue were inherited from the original build and kept: a
Greek carrier in blue is convention, not accident. **Kouros Ochre is the
addition that does the work.** An all-blue interface has no way to
distinguish "this is our brand" from "press this" — every previous call to
action was the same blue as every link and every heading. The ochre is drawn
from Cycladic terracotta and appears sparingly, which is what makes it
legible as *the* action colour.

### 3.2 Semantic palette

| Token | Name | Hex | Use |
|---|---|---|---|
| `--color-success` | Olive | `#2E7D5B` | Confirmed bookings, positive state |
| `--color-warning` | Amber | `#A05F00` | Approaching a limit, degraded state |
| `--color-danger` | Rust | `#C62828` | Errors, destructive actions, cancellation |

Semantic colour is never the only carrier of meaning. Every status also
carries a text label or an icon, so that the roughly 1 in 12 men with a
colour-vision deficiency reads the same information everyone else does.

### 3.3 Contrast

Every combination in shipped use meets **WCAG 2.2 AA** (4.5:1 for body text,
3:1 for large text and interactive boundaries).

Ratios below are computed, not estimated — see
[`contrast_check.py`](contrast_check.py), which is run in CI and fails the
build if any pair regresses.

| Foreground | Background | Ratio | Verdict |
|---|---|---|---|
| Marble `#1A1A1A` | Cycladic White | 17.40:1 | Pass AAA |
| Marble `#1A1A1A` | Aegean Mist | 15.75:1 | Pass AAA |
| Delos Navy `#002A5C` | Cycladic White | 14.13:1 | Pass AAA |
| Cycladic White | Delos Navy | 14.13:1 | Pass AAA |
| Cycladic White | Meltemi Blue `#0072C6` | 4.97:1 | Pass AA |
| Cycladic White | Kouros Ochre `#A8530C` | 5.37:1 | Pass AA |
| Kouros Ochre Light `#E0752D` | Delos Navy | 4.54:1 | Pass AA |
| Rust `#C62828` | Cycladic White | 5.62:1 | Pass AA |
| Olive `#2E7D5B` | Cycladic White | 5.00:1 | Pass AA |
| Amber `#A05F00` | Cycladic White | 5.08:1 | Pass AA |

Two notes on how these were arrived at, because the failures are more
instructive than the passes.

Kouros Ochre began as `#E0752D`, chosen by eye. On white that is **3.11:1 —
a clear AA failure** for the button labels it was meant to carry. Darkening
to `#A8530C` clears the threshold at 5.37:1. But the darkened value then
measures only **2.63:1 against Delos Navy**, so it is unusable on the navy
hero and nav bar — which is why the palette carries two ochres rather than
one, and why the light variant is scoped to dark surfaces only. A single
"brand accent" could not satisfy both surfaces.

The inherited Meltemi Blue `#0072C6` was checked on the assumption it would
fail. It does not — 4.97:1 passes AA, with little margin. It is kept, but it
is not a safe base for further darkening or tinting without re-measuring.

---

## 4. Typography

**Inter** throughout, at four weights: 300, 400, 600, 700. One family keeps
the page weight down, and Inter's tabular figures matter for a product that
displays fares, times and flight numbers in columns.

| Role | Size / line-height | Weight | Tracking |
|---|---|---|---|
| Display | 48 / 52 px | 700 | −0.02em |
| Page title | 32 / 38 px | 700 | −0.01em |
| Section | 24 / 30 px | 600 | 0 |
| Body large | 18 / 28 px | 400 | 0 |
| Body | 16 / 24 px | 400 | 0 |
| Small | 14 / 20 px | 400 | 0 |
| Label | 12 / 16 px | 700 | 0.06em, uppercase |

**Numerals.** Fares, times, dates and flight designators are set with
`font-variant-numeric: tabular-nums` so figures align vertically in lists
and do not shift as they update.

---

## 5. Space, shape and elevation

A **4 px base unit**. Spacing steps: 4, 8, 12, 16, 24, 32, 48, 64.

Radii: `6px` inputs and small controls, `12px` cards, `9999px` pills.

Two elevations only, because a booking interface with more reads as
cluttered:

- `--shadow-card` — resting cards
- `--shadow-float` — hover, modals, the search widget over the hero

---

## 6. Voice and tone

Calm, specific, and in the passenger's terms. Say what happened and what to
do next. Never blame the user, never use an exclamation mark, and never use
urgency as a sales device.

| Instead of | Write |
|---|---|
| "Booking successful!" | "Booked. Your reference is **DS4K2P**." |
| "Error!" | "That card was declined. Try another, or contact your bank." |
| "Invalid input" | "Enter the passport number exactly as printed, without spaces." |
| "Only 2 seats left — book now!" | "2 seats remain at this fare." |
| "Oops! Something went wrong :(" | "We couldn't reach the payment provider. Nothing has been charged." |

### 6.1 Rules for failure messages

1. **State what happened**, in the passenger's terms, not the system's.
2. **State the money position** whenever payment is involved. "Nothing has
   been charged" is the sentence people are looking for.
3. **Give one next action.** If recovery is impossible, say who to contact.
4. **Never expose internals.** The API previously returned
   `Internal Server Error: {exception}` straight to the client, leaking stack
   detail to anyone who could trigger a 500.

### 6.2 Naming things

Passenger-facing terms are fixed, because inconsistency between them is how
an interface starts to feel untrustworthy:

**booking** (not reservation or order) · **fare** (not price or cost) ·
**passenger** (not user or customer) · **itinerary** (the set of a
passenger's booked flights) · **flight** (a single dated leg) ·
**booking reference** (not PNR, which is internal vocabulary).

---

## 7. Applying it

Tokens live in `frontend/src/index.css` inside Tailwind v4's `@theme` block
and are used as `bg-primary`, `text-signal`, `shadow-card`, and so on. There
are no hex literals in component files — a hardcoded colour in a component is
a bug, and reviewable as one.

```css
@theme {
  --color-primary:      #002A5C;  /* Delos Navy         */
  --color-secondary:    #0072C6;  /* Meltemi Blue       */
  --color-signal:       #A8530C;  /* Kouros Ochre       */
  --color-signal-light: #E0752D;  /* Kouros Ochre Light */
  ...
}
```

### Open items

- **Dark mode** is not defined. The palette needs a second set of surface and
  text values before it can be claimed, and shipping a half-inverted
  interface is worse than shipping none.
- **Motion** has no duration or easing scale yet, so animation beyond hover
  states should wait. A `prefers-reduced-motion` rule is already in place in
  `index.css`, so honouring the setting is not the blocker — consistency is.
- **Photography** direction is unwritten. The current pages hotlink a stock
  aerial photograph from Unsplash on every render, which is an availability
  dependency on a third party, an uncredited use, and a tracking vector.
  Phase 5 replaces it with owned or properly licensed assets served locally.
