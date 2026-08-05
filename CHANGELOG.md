# Changelog

Notable changes to DS Airlines. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

**The project is complete at v0.2.0 and stops there deliberately.** Versions
stay pre-1.0 because payment capture and the operations interface were never
built; 1.0.0 would claim the product is finished rather than scoped. What was
left out, and why, is in [the README](README.md#what-was-not-built-and-why).

Defect identifiers (DEF-*) refer to
[the current-state assessment](docs/analysis/current-state-assessment.md).

---

## [Unreleased]

The interface is rebuilt on **Atlas**, replacing AF. Same relationship as
before — the design system owns everything visual, DS Airlines owns only the
words — different system: "rounded glass" over navy and chartreuse, Gabarito
and Spline Sans Mono in place of Archivo and IBM Plex Mono. No domain, API or
test behaviour changed; this is the visual layer and its documentation only.

Internally, the vendored token files carry the codename `VANE` in their own
header comments — that's the vendor's own working title, kept because
`tokens.css` and `base.css` are byte-identical to source. The design system's
name is Atlas throughout this product's own docs and code.

### Changed
- **Token layer** — `tokens/{color,typography,space,elevation,motion,base}.css`
  (AF, six files) replaced with `tokens/{tokens,base}.css` (Atlas, two
  files), vendored byte-identical to source. Webfonts switched from
  self-hosted Archivo / IBM Plex Mono / Instrument Serif `.woff2` files to
  `@fontsource` packages for Gabarito and Spline Sans Mono.
- **Every component re-skinned** — Login, Register, Dashboard, BookingDialog
  and ThemeToggle now use Atlas's three devices (the index label, the glass
  panel, mono figures) instead of AF's utility classes. Phosphor icons
  (regular weight only) added where they support a label, never replacing
  one: the theme toggle, the nav wordmark, search fields, the demonstration
  notice.
- **`contrast_check.py` rewritten** for Atlas's hex/rgba tokens in place of
  AF's OKLCH, and re-based on 14 pairs that reflect what this product
  actually renders (28 checks total across both themes, down from 34 — some
  AF-specific pairs no longer apply; see `docs/brand/brandbook.md` §4 for
  what replaced them).

### Fixed
- **Four WCAG 2.2 AA failures**, found the same way AF's were: two in the
  dark theme (`--tint-danger` 3.73:1, `--tint-info` 4.48:1), two in the light
  theme (`--tint-success` 4.50:1 — at the floor, not over it —
  `--border-accent` 1.37:1, functionally invisible as the selected-fare
  card's outline). Corrected in `overrides.css`, all candidates to upstream.
  Full measurements in `docs/brand/brandbook.md` §4.
- **Index-label text on a glass panel** measured 3.10:1 in the dark theme — a
  real pair, correctly flagged, but the fix was in the application, not the
  palette: those instances now use `--text-secondary` instead of
  `--text-tertiary`, which clears AA on glass.
- **The selected-fare border was wired to the wrong token** — `--fill-accent`
  (the solid button colour) instead of `--border-accent`, measuring 1.16:1 in
  the light theme. Solid chartreuse on a near-white ground is not a visible
  line.
- **The README's mobile login screenshot was a desktop screenshot.** The
  browser automation used to capture it silently failed to resize the
  viewport for that one shot — same pixel dimensions as the desktop login
  image, byte-for-byte the wrong picture, caught on review rather than by
  anything automated. Re-captured at a verified narrow viewport
  (`window.innerWidth` checked directly, not inferred from the tool's
  success message) along with the other two mobile shots, which were
  already correct.
- **A stale "AF" comment** survived the sweep in `vitest.config.ts`.

---

## [0.2.0] — 2026-08-02 · Phase 1, Domain

The document model is gone. The booking engine now runs on PostgreSQL, and
the interface is built on the AF design system.

### Added
- **Relational domain** — ten tables replacing three collections: airports,
  aircraft types, aircraft, seat maps, routes, fare classes, flights, flight
  seats, users, bookings. Rationale in
  [ADR-001](docs/adr/0001-postgresql-over-mongodb.md).
- **Branded fares** — Light, Standard and Flex, with baggage, change and
  refund rules held in data rather than in copy. Search returns a price per
  fare class.
- **Seat inventory** — `flight_seats` rows replace a scalar counter, so a
  booking holds a key to the specific seat it occupies.
- **Booking references** — six characters from an alphabet with I, O, 0 and 1
  removed, because a reference gets read aloud and written down.
- **AF design system** — token layer, webfonts and accessibility standard
  vendored byte-identical; components rebuilt against the tokens.
- **Dark and light themes**, resolving stored choice → OS preference → AF's
  default. Both are contrast-verified.
- **Alembic migrations**, with a CI check that fails on drift between the
  models and the revision chain.
- **`make`** — `up`, `setup`, `seed`, `dev`, `check`. Docker or native.
- **Personas and user stories** with story → endpoint → test traceability.
- **42-case manual test pass** covering every page.

### Changed
- Booking is **one transaction**. The Mongo version claimed a seat, inserted
  the booking, and undid the claim by hand on failure — a compensating write
  that leaked a seat permanently if the process died in between (DEF-007).
- Search does **no pattern matching**. Origin and destination are IATA codes
  matched exactly, so the regex injection surface of DEF-005 does not exist
  rather than being escaped.
- Flight deletion relies on `ON DELETE RESTRICT` instead of a count-then-
  delete check that could race (DEF-019).
- Cancellation marks a booking cancelled rather than deleting it, and a
  second attempt is refused so it cannot credit a second seat back.
- Tests: 47 → 89, against **real PostgreSQL**. The Phase 0 in-memory fake is
  retired as ADR-001 promised.

### Removed
- **Payment details are no longer accepted.** Phase 0 stopped storing the
  card number; this stops accepting one. `extra="forbid"` means a client
  still sending `credit_card` receives a 422 rather than having it silently
  ignored. This closes DEF-003 more completely than the Phase 3 tokenisation
  plan, two phases earlier.
- **"Meltemi Club"** — a loyalty programme invented to replace the
  trademarked "Miles+Bonus", promising points nothing awarded and nothing
  could spend. Replacing a borrowed claim with a fabricated one is not a fix.
- The "Delos Skyways" trading name, which gave the interface two labels where
  it needed one.

### Fixed
- Two **WCAG 2.2 AA failures in AF's own light theme**, found by the contrast
  checker: `--status-warning-fg` at 4.18:1, and `--action-secondary-border`
  at 1.56:1 — the outline of a transparent button, where SC 1.4.11 requires
  3:1. Corrected in `overrides.css`; both are candidates to upstream.
- **Webfonts did not resolve in the production build.** Nested under
  Tailwind's `@import`, Vite emitted `../assets/fonts/…` verbatim and shipped
  no `.woff2` at all, so Archivo and Plex Mono fell back to Helvetica with no
  build error — the entire typographic identity, silently absent.
- Every flight row carried a primary action, against AF's rule of one per
  view.
- A selective `--spacing-*` bridge left `p-7` and `p-8` both at 2rem.

---

## [0.1.0] — 2026-07-29 · Phase 0, Foundation

An audit of the original university project code, and the fixes it
demanded. 30
defects recorded — 4 Critical, 6 High.

### Fixed
- **DEF-001 · The entire admin surface was unreachable.** Tokens carried only
  `sub` and `exp` while every authorisation check read `is_admin`, a key that
  never existed. Flight creation, repricing and withdrawal returned 403 to
  every caller, including the administrator the app seeded for itself.
- **DEF-002 · The token was treated as the user record.** A deactivated or
  deleted account kept access until expiry; `is_active` was enforced nowhere.
- **DEF-003 · Full card numbers stored in cleartext** beside passport
  numbers.
- **DEF-004 · Every deployment shipped a known admin password**, hardcoded,
  next to a signing key committed to the repository.
- **DEF-005** · Unauthenticated search input interpolated into a Mongo
  `$regex`.
- **DEF-006** · Flight designators built from the first letter of each city,
  so distinct routes collided.
- **DEF-008** · Accounts created by an administrator could never log in — one
  handler wrote `hashed_password`, the other read `password`.
- **DEF-009** · `docker-compose up --build` could not build the frontend
  image: Node 18 against a toolchain requiring Node 20+.
- **DEF-014** · The interface claimed "A Star Alliance Member" and advertised
  "Miles+Bonus", Aegean's registered programme.
- Plus 20 further defects — see the assessment.

### Added
- The defect register, a brand book, a test strategy, and CI.
- Tests: 6 → 47. The original six all exercised the same two auth endpoints,
  because anything else needed a database they had no way to provide — which
  is precisely why a dead admin surface sat beside a green suite.

### Removed
- The claim that the project was "production-ready". It was checkable, and
  false.

---

[0.2.0]: https://github.com/aposfys/ds-airlines-booking/releases/tag/v0.2.0
[0.1.0]: https://github.com/aposfys/ds-airlines-booking/releases/tag/v0.1.0
