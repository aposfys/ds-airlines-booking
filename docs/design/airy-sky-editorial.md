# Design system — Airy Sky Editorial

DS Airlines runs on a two-layer token system defined in
`frontend/src/design-system/tokens/tokens.css`, bridged into Tailwind by
`frontend/src/index.css`. Components never use raw colours; a hex literal in
a component is a bug.

```
1. PRIMITIVES  raw values, per theme   (--paper, --ink, --sky …)
2. SEMANTIC    role names              (--ground, --text, --accent …)
3. COMPONENTS  only ever touch layer 2
```

Themes are switched with `data-theme` on `<html>`. **Light is the default**
(`:root`); dark is the alternate remap.

## Palette — Paper & Sky

| Role | Light | Dark |
| --- | --- | --- |
| Ground | Cream paper `#F6F4EF` → `#ECE7DC` | Ink navy |
| Raised surface | White `#FFFFFF` | Navy raised |
| Text | Ink navy `#1A2E4A` | Paper white |
| Muted text | `#4A5D78` | Slate haze |
| Accent (fill) | Deep sky `#0E76A0` | Sky `#3DB7E0` |
| Accent (light) | Sky `#3DB7E0` | Sky soft `#5BC4E8` |
| Positive / warn / critical | `#10794B` / `#8A5B04` / `#C0271F` | lightened equivalents |

A soft `--bloom` gradient (three radial sky/navy washes over a paper
gradient) sits behind every page so flat areas never read as dead white.

## Typography

- **Display** — Outfit, `-0.03em` tracking, used for hero and section titles
  (`.ds-hero`, `.ds-eyebrow`).
- **Body / UI** — Figtree.
- **Numerals** — Outfit via `.v-num` for fares, times and IATA codes.
- Scale: 10 / 11 / 12 / 13 / 14 / 16 / 19 / 25 / 33 / 46 px.
- Labels use `.ds-label`: 11px, uppercase, `0.1em` tracking.

Fonts are self-hosted through `@fontsource`, imported by
`design-system/tokens/fonts.css` — never as a bare `@import` nested under
Tailwind's own, which once produced a build containing zero `.woff2` files
with everything silently falling back to Helvetica. `e2e/interface.spec.ts`
asserts both faces are actually served.

## Geometry, motion, controls

- Radii: inner `6px`, panels/controls `10px`, frames `14px`, pills `999px`.
- Spacing grid: 1.75px unit → `--sp-1 … --sp-9` (3.5 → 84px).
- Control heights: `28 / 34 / 42px`, minimum touch target `44px`.
- Motion: `90ms` / `170ms` on `cubic-bezier(0.2, 0, 0, 1)`. All auto-motion
  (hero carousel) respects `prefers-reduced-motion`.

## Glass

`.v-glass` is the signature device: a translucent surface with
`backdrop-filter: blur(18px) saturate(150%)`, a hairline border and an inner
sheen. `.v-glass-frame` adds the wider frame used by the hero search bar.
Glass is always placed over photography or the bloom — never over flat paper,
where it has nothing to refract.

## Photography and scrims

Rule: **no text ever sits on bare photography.**

- `.ds-photo` — absolutely positioned, object-fit cover image layer.
- `.ds-scrim` + one of:
  - `.ds-scrim--hero` — vertical on phones, horizontal from `md` up
  - `.ds-scrim--panel` — auth split panels
  - `.ds-scrim--card` — destination and flight thumbnails
- Scrim strength comes from the themed `--scrim-rgb` token (navy in light,
  deeper navy in dark), so contrast stays AA in both themes.

Images live in `src/assets/destinations` and are mapped to IATA codes in
`src/lib/destination-images.ts`. They are currently crops taken from the
original design comps — soft at card size, and placeholders for real licensed
photography; a station with no image falls back to `--bloom` rather than an
empty box. Every image is `decoding="async"` with a
responsive `sizes` attribute; only the first hero slide is eager and
`fetchPriority="high"` (it is the LCP element).

## Component classes

| Class | Purpose |
| --- | --- |
| `.ds-action` / `.ds-action--primary` | Buttons; one primary action per view |
| `.ds-field` | Text inputs and selects |
| `.ds-icon-button`, `.ds-dot` | Carousel controls and pagination dots |
| `.ds-editorial` | Photographic editorial container |
| `.v-glass`, `.v-glass-frame` | Glass surfaces |
| `.v-num` | Tabular/display numerals |
| `.ds-hero`, `.ds-eyebrow`, `.ds-label` | Type roles |

## Accessibility

- AA contrast verified in both themes, including over photography:
  `docs/brand/contrast_check.py` measures each scrim composited over a
  blown-out highlight, the worst an image can put beneath it, and CI fails
  below AA. 17 pairs across 2 themes.
- Decorative images use `alt=""`; interactive cards carry explicit
  `aria-label`s describing the action, not the picture.
- Weather chips expose the full condition and temperature as an accessible
  label; the featured-route strip is an `aria-live="polite"` region.
