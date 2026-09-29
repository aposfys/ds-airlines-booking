# Airy Sky Accessibility Standard

**Target: WCAG 2.2 Level AA.** This is the standard the Airy Sky Editorial
token layer is held to, and how this product applies it. AA is the floor.
The 10px uppercase `.ds-label` is what pushes most pairs past it, since that
label is not going to be enlarged and the colours have to carry it instead.

It replaces the Atlas standard this file held from 5 August 2026. The Atlas
measurements are in the changelog.

## 1 · Contrast, both themes

The three text roles clear AA for normal text on the page ground, as
`docs/brand/contrast_check.py` measures them from `tokens/tokens.css`.

| Role | Light | Dark |
| --- | --- | --- |
| `--text-primary` | 12.46:1 | 15.11:1 |
| `--text-secondary` | 6.11:1 | 8.41:1 |
| `--text-tertiary` | 4.80:1 | 6.23:1 |

Status text clears AA on its own tint in both themes. In the light theme
success measures 4.51:1, danger 4.60:1 and info 5.99:1, and warning measures
5.64:1 on a glass panel. Success is the pair closest to the floor. White
text over photography sits on a navy scrim in both themes and is measured
over a blown-out highlight, the worst a photograph can put underneath it.

The checker covers 17 pairs in each theme and fails CI below AA. The numbers
above are its output, not targets.

## 2 · Focus

One global rule, in `tokens/base.css`. A 2px `--focus-ring` outline at 2px
offset on every interactive element, never removed. `--focus-ring` is deep
sky in the light theme and sky in the dark, and it measures at least 4.6:1
against the page ground and a glass panel in both.

## 3 · Colour is never the only carrier

Tags pair a tint with a word. This product's booking status renders
`Confirmed` / `Cancelled` as text, not just a coloured dot. Invalid fields
pair the border with error copy and `aria-invalid`. The "N seats remain"
notice and the demonstration notice both carry a word, not just a border
colour.

## 4 · Touch targets

Floor at 44px (`--touch`). The 28px and 34px control heights the token layer
also defines are for pointer surfaces only. Buttons, fields and the carousel
controls in this product use `--touch`.

## 5 · Motion

`prefers-reduced-motion: reduce` collapses both durations (`--d-1`, `--d-2`)
to 1ms, defined once in `tokens/tokens.css`. The hero carousel reads the same
preference live and does not auto-advance while it is set.

## 6 · Icons (Phosphor, regular weight)

- Regular weight only, sized in `em` via `.v-icon` so a glyph tracks the
  label beside it.
- Inherits `currentColor` and is never given its own colour.
- Never the sole carrier of meaning, and never unlabelled. This product's
  icon-only controls (the theme toggle, the carousel arrows) carry an
  accessible name. Decorative glyphs carry `aria-hidden`.

## 7 · Glass and photography

Backdrop blur needs light behind it or a panel reads as flat. That is
handled globally by `body::before` painting the bloom, so no component needs
to worry about it. Every glass panel keeps its 1px hairline border in both
themes, because the edge, not the fill, defines the boundary.

No text ever sits on bare photography. Text over an image always sits on one
of the three scrims, and the scrims are what the checker measures.

## 8 · Rules that follow from this palette

1. **`--fill-accent` for backgrounds, `--text-accent` for type.** In Airy
   Sky the two resolve to the same colour in each theme, deep sky in light
   and sky in dark, but they are separate roles and a palette is free to
   split them. Atlas did, and there the wrong one of the pair failed 1.4.3.
2. **Hairlines invert between themes**, and the semantic layer already does
   this (`--border-subtle` and the rest). A raw white or navy literal in
   product code would not.
3. **Never nest a blurred panel inside another blurred panel.** Beyond the
   GPU cost, a second blur compounds the contrast loss the first one already
   spent.

## 9 · Not yet done, needs a real audit

This document is a design standard, not a compliance certificate. Before
this product claims conformance it needs an axe or WAVE automated pass, a
manual NVDA and VoiceOver run, and a keyboard-only walkthrough of the
booking flow specifically (dialog focus trap, Escape to close, focus return
to the trigger).
