# VANE Accessibility Standard

**Target: WCAG 2.2 Level AA.** Adapted from the vendored system's own readme
(`Atlas design system setup/readme.md`, § Accessibility), plus how this
product applies it. AA is the floor: VANE's signature 10px mono label is what
forced most pairs well past it, since that label was never going to be
enlarged and the colours had to carry it instead.

## 1 · Contrast, both themes

All four text roles clear AA for normal text at 10px:

| Role | Dark | Light |
| --- | --- | --- |
| `--text-primary` | 15.3:1 | 15.1:1 |
| `--text-secondary` | 8.8:1 | 6.6:1 |
| `--text-tertiary` | 5.9:1 | 5.1:1 |
| `--text-placeholder` | 4.8:1 | 5.0:1 |

Status text clears AA in both themes: light-theme success 5.0:1, warning
5.2:1, danger 5.4:1. The light theme's tertiary, placeholder and status
tones were all re-derived from the dark originals — the first pass failed at
4.35:1, 4.06:1 and below, so this is measured, not assumed.
`docs/brand/contrast_check.py` re-derives these from the vendored token file
this application actually loads and fails CI below AA.

## 2 · Focus

One global rule, in `tokens/base.css`: a 2px chartreuse (`--focus-ring`)
outline at 2px offset on every interactive element, never removed.

## 3 · Colour is never the only carrier

Trend direction pairs colour with a sign. Tags pair a tint with a word — this
product's booking status renders `Confirmed` / `Cancelled` as text, not just
a coloured dot. Invalid fields pair the border with error copy and
`aria-invalid`. The "N seats remain" notice and the demonstration notice both
carry a word, not just a border colour.

## 4 · Touch targets

Floor at 44px (`--touch`). The 34px control height VANE also defines is for
pointer surfaces only and is not used anywhere in this product — every
button and field here uses `--touch`, matching AF's standard before it.

## 5 · Motion

`prefers-reduced-motion: reduce` collapses both VANE durations (`--d-1`,
`--d-2`) to 1ms, defined once in `tokens/tokens.css`.

## 6 · Icons (Phosphor, regular weight)

- Regular weight only, sized in `em` via `.v-icon` so a glyph tracks the
  label beside it.
- Inherits `currentColor` — never given its own colour.
- Never the sole carrier of meaning, and never unlabelled: this product's
  icon-only controls (the theme toggle) carry `aria-label` and `title`;
  decorative glyphs (the nav wordmark's plane, the demonstration notice's
  info glyph) carry `aria-hidden`.

## 7 · Glass caveats that double as accessibility notes

Backdrop blur needs light behind it or a panel reads as flat mush — handled
globally by `body::before` painting the bloom, so no component needs to
worry about it. The light theme's frosted glass has less contrast against
its ground than the dark theme's tinted glass, so every glass panel keeps
its 1px hairline border regardless of theme — the edge is what actually
defines the boundary, not the fill.

## 8 · Rules that follow from this palette

1. **`--fill-accent` for backgrounds, `--text-accent` for type.** Chartreuse
   as *text* on a pale ground measures 1.3:1; `--text-accent` on light drops
   to a deep lime instead. Reaching for the wrong one of the pair is the
   fastest way to fail 1.4.3 in the light theme specifically.
2. **Hairlines invert between themes**, and VANE's semantic layer already
   does this (`--border-subtle` etc.) — a raw white/navy literal in product
   code would not.
3. **Never nest a blurred panel inside another blurred panel.** Beyond the
   GPU cost VANE's readme flags, a second blur compounds the contrast loss
   the first one already spent.

## 9 · Not yet done — needs a real audit

This document is a design standard, not a compliance certificate. Before
this product claims conformance it needs an axe/WAVE automated pass, a
manual NVDA + VoiceOver run, and a keyboard-only task walkthrough of the
booking flow specifically (dialog focus trap, Escape-to-close, focus return
to the trigger).
