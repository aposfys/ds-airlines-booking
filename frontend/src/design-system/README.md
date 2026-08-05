# VANE (Atlas) — vendored token layer

DS Airlines does not have its own visual identity. It is a product built on
**VANE**, a personal design system by Apostolos Fysekidis also referred to as
Atlas — a "rounded glass" interface language over a navy-and-chartreuse
palette. VANE supplies the visual system, and DS Airlines supplies the verbal
one — the positioning, the fare names and the words on screen. See
[`docs/brand/brandbook.md`](../../../docs/brand/brandbook.md) for the split.

VANE replaced this project's first design system, AF, on 5 August 2026. AF's
28-component kit was never vendored here in the first place — this
application always built its own components against a token layer — so the
swap is a token-layer replacement plus a re-skin of the four components that
reach for it, not a component migration.

## What is here, and what is not

**Vendored:** the token layer (`tokens/tokens.css`, `tokens/base.css`), the
webfont imports (`tokens/fonts.css`), and the accessibility standard
(`accessibility.md`, adapted from the vendor's own readme).

**Not vendored:** VANE ships no component set at all — its own readme states
this plainly ("No components built. This is the language and the token
system."). Every product-level shape (`ds-field`, `ds-action`, `ds-hero`,
`ds-label`, `ds-eyebrow`, `ds-skip-link`) is this application's own, built in
`src/index.css` against VANE's semantic tokens and its three vendored
devices — `.v-idx` (the index label), `.v-glass` (the panel), `.v-num` (mono
figures) — rather than reimplemented differently.

## Provenance

| | |
|---|---|
| Source | `Atlas design system setup` (codename VANE), local working copy |
| Vendored | 5 August 2026 |
| Files | `tokens/{tokens,base,fonts}.css`, `accessibility.md` |
| Modifications | `tokens.css` and `base.css` are byte-identical to source; `overrides.css` carries this product's corrections on top, same as AF before it. `fonts.css` is new — the source ships CDN font links; this vendors the same families via `@fontsource` instead, matching how AF's fonts were self-hosted here previously. |

`tokens.css` and `base.css` are unmodified deliberately, so they can be
re-copied over the top when VANE changes without a merge. Re-syncing means
re-copying those two files and re-running
`python docs/brand/contrast_check.py`, which reads the palette from
`tokens/tokens.css` **and** `overrides.css` in that order and fails CI on any
pair below WCAG 2.2 AA.

`overrides.css` exists because four token pairs, measured as this product
actually composites them — status text on its own tint, and the
selected-fare-card border against a glass panel — landed under AA once
rendered, not in the abstract. Each correction is documented at the token
with the measured before/after ratio; see the file itself. This is the same
role AF's `overrides.css` played, and the same discipline: two real defects
found in AF's light theme, four found here.

## Using it

`src/main.tsx` imports `tokens/index.css` — which pulls in `fonts.css`, then
`tokens.css`, then `base.css`, matching the vendor's own `styles.css` order
— *before* `src/index.css`, which bridges the tokens into Tailwind's
`@theme` so they are reachable as utilities (`bg-card`, `text-strong`,
`border-hairline`).

**The import must stay in `main.tsx`.** Reaching the token entry through an
`@import` inside `src/index.css`, nested under Tailwind's own `@import`,
risks Vite not rebasing the `@font-face` urls the same way — this broke
silently under AF and is why the entry point is still kept as its own CSS
module rather than folded in.

Two rules from VANE's brief that the review checks for:

1. **Never use a primitive directly.** `--navy-900` and `--lime-400` do not
   belong in component code; use the semantic alias — `--surface`,
   `--fill-accent`. Re-theming works only if this holds — it is exactly what
   broke before the accent was split into `--fill-accent` (backgrounds) and
   `--text-accent` (type).
2. **One primary action per view.** Chartreuse fill means "act"; a list of
   options gets one Signal button at most, and it is never spent on N
   equally-weighted rows.
