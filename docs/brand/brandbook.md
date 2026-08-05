# DS Airlines — Product Brand

**Version 3.0 · August 2026**

DS Airlines has no visual identity of its own. It is a product built on
**[Atlas](../../frontend/src/design-system/README.md)**, a design system by
Apostolos Fysekidis, and Atlas owns everything you can see: colour, type,
space, motion, elevation, the accessibility floor.

This document owns the other half — what the airline *is* and what it *says*.
Name, positioning, network, fare architecture, voice, and the words on
screen.

> **Version 1.0 of this document proposed a full visual identity** — a navy
> and ochre palette, Inter throughout, a light ground, two shadow levels.
> That was written before AF was on the table, and it is superseded.
>
> **Version 2.0 built on AF** — a dark-first system with a vermilion signal
> colour, Archivo and IBM Plex Mono, hairlines and 6px radii. AF was replaced
> by Atlas on 5 August 2026: same relationship (a house system applied
> wholesale, the product supplying only the words), different system —
> "rounded glass" over navy and chartreuse, Gabarito and Spline Sans Mono.
> Nothing in this document's split changed, only which system sits on the
> other side of it. (The vendored token files carry the codename `VANE` in
> their own header comments — the vendor's own working title, kept because
> those two files are byte-identical to source. The system's name is Atlas.)

---

## 1 · The split

| Owned by Atlas | Owned here |
|---|---|
| Colour, and every semantic alias | The name, and how it is written |
| Type: Gabarito and Spline Sans Mono | Positioning and the competitive wager |
| Space, radius, blur, motion | Network, fleet, currency |
| The three devices — index label, glass, hairline | Fare architecture and what each fare promises |
| WCAG 2.2 AA floor | Voice, tone, and every string on screen |
| Dark ground by default, chartreuse accent | Naming of passenger-facing concepts |

The rule for anything not listed: **if it can be seen, Atlas decides; if it
can be read, this document decides.**

---

## 2 · The airline

### 2.1 The name

**DS Airlines.** One name, used everywhere — on the aircraft, in the flight
numbers (`DS1040`), in the API, and in every string a passenger reads.

**DS is not expanded.** There is no trading name behind the initials and no
backronym to reveal; the two letters are the carrier's designator and the
brand at once. An earlier draft of this document invented a trading name and
an origin story for it, which added a second thing to say the airline's name
and gave the interface two labels where it needed one. Airlines are known by
their designator — the expansion, where one exists at all, is trivia.

Written **DS Airlines** in prose and **DS** where the context is already the
airline (a flight number, a fare code, a seat map). Never "D.S.", never
"ds airlines".

### 2.1.1 Why it stayed

The name was reviewed against alternatives in August 2026 — Greek-rooted
candidates including *Alkyon* (the halcyon; the calm windless days), *Meltemi*
(the Aegean summer wind) and *Nefeli* (cloud). None was adopted.

The initials come from the **Department of Digital Systems at the University
of Piraeus**, where this project was originally built. That is the honest origin, and it is a better reason to
keep them than any invented one: the name records where the work came from,
which is the same instinct that produced the defect register rather than a
quiet rewrite.

Two of the rejected candidates are worth recording, because the reasoning
generalises. *Meltemi* was the most recognisable and the most unmistakably
Greek — and wrong: the meltemi is the wind that grounds ferries and closes
island airports every August. An airline whose entire promise is
dependability should not be named after the regional cause of delay.
*Halcyon* was semantically ideal and commercially crowded — a Cape Verde
carrier traded under it until 2013, and several aviation businesses still do.

If the name is ever revisited, the bar is the one this document already
applies to a loyalty programme: a candidate needs to survive a trademark
check and mean something the airline can actually deliver.

### 2.2 Positioning

> **DS Airlines is the dependable Aegean connector: full-service reliability
> on short-haul European routes, without the full-service price.**

The market splits in two and serves the middle badly.

| | Legacy full-service | **DS Airlines** | Ultra-low-cost |
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

DS Airlines belongs to no alliance.

**It has no loyalty programme either.** The register page briefly advertised
one — "Meltemi Club", invented to fill the space Miles+Bonus vacated,
promising points on every flight. Nothing awarded them and nothing could
spend them. Replacing a borrowed claim with a fabricated one is not a fix:
the same reader who would have caught the trademark would catch a scheme
that does not exist. The copy now describes only what registering does.

If a programme is ever built, it needs an accrual model, an expiry policy and
a redemption path before it gets a name.

---

## 3 · Voice

This document's own content rules apply — short declarative sentences,
concrete nouns, no salesmanship, no emoji, no Title Case. Atlas, unlike AF
before it, ships no copy guidance of its own; it is tokens and glass, not
words. What follows is what these rules sound like when an airline says
them.

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

Atlas's standard — [`accessibility.md`](../../frontend/src/design-system/accessibility.md),
WCAG 2.2 AA, non-negotiable — is inherited whole. Two things are enforced
mechanically rather than by review:

**Contrast.** [`contrast_check.py`](contrast_check.py) reads the palette out
of the token files the application actually loads, converts hex/rgba to
linear sRGB, composites translucent values over their background, and checks
14 pairs in **both** themes. It runs in CI and fails the build.

It found four real failures, both themes this time, now corrected in
[`overrides.css`](../../frontend/src/design-system/overrides.css) and all
candidates to upstream:

- `--tint-danger` and `--tint-info`, in the **dark** theme, measured
  **3.73:1** and **4.48:1** under their own status text — under the 4.5:1
  floor for the cancelled badge and the booking dialog's demonstration
  notice. Lowered to 0.06 and 0.10 alpha for 4.78:1 and 5.10:1.
- `--tint-success`, in the **light** theme, measured **4.50:1** — at the
  floor, not over it. Lowered to 0.09 alpha for 4.62:1, so a rounding
  difference cannot flip it.
- `--border-accent`, in the **light** theme, measured **1.37:1** on the
  selected-fare card's outline — close to invisible, and SC 1.4.11 requires
  3:1 for a control boundary. No alpha of Atlas's own hue clears 3:1 against
  a ground this pale; re-based on `--lime-700`, the same deep lime already
  used for `--text-accent` in this theme, for 3.6:1.

A fifth change, in the dark theme, is headroom rather than a failure:
`--border-accent` there measured 3.05:1, over the floor by 0.05 with no
margin for a rounding difference, so it was raised the same way to 3.5:1.

Two further findings were fixed in the application rather than the palette,
because the palette pair itself was fine — the product was reaching for the
wrong one. Index-label text (Atlas's `--text-tertiary`) measures 3.10:1 on a
glass panel in the dark theme; every place that combination occurred now
reads `--text-secondary` instead, which clears 4.6:1 there. And the
selected-fare border was wired to `--fill-accent` (the solid button colour)
rather than `--border-accent`, which is 1.16:1 in light — solid chartreuse on
a near-white ground.

**Targets and focus.** Controls are 44px minimum; the focus ring is Atlas's,
2px, and never removed. `prefers-reduced-motion` collapses motion in Atlas's
base layer.

### Open items

- **Theme switching** is not exposed. Both themes are token-complete and both
  pass contrast, but nothing in the interface toggles `data-theme`.
- **Photography** direction is unwritten. The pages once hotlinked a stock
  photograph from Unsplash on every render; that is gone, and Atlas's glass
  over the bloom stands in until owned or licensed assets exist.
- **No logo.** Atlas ships no mark by design, and DS Airlines has not been
  given one. The name is set in type — Gabarito 700 — wherever a mark would
  go.
