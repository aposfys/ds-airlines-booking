# Airy Sky Editorial — the token layer

DS Airlines does not have its own visual identity. It is a product built on
**Airy Sky Editorial**, a personal design system by Apostolos Fysekidis — a
light-first editorial language over a Paper & Sky palette, with glass and
scrimmed photography as its two structural devices. The design system
supplies the visual language; DS Airlines supplies the verbal one — the
positioning, the fare names and the words on screen. See
[`docs/brand/brandbook.md`](../../../docs/brand/brandbook.md) for the split,
and [`docs/design/airy-sky-editorial.md`](../../../docs/design/airy-sky-editorial.md)
for the system itself.

This is the third token layer this project has run on: AF, then Atlas from
5 August 2026, then Airy Sky. None of them ever vendored a component kit —
this application has always built its own components against a token layer —
so each swap has been a token-layer replacement plus a re-skin, not a
component migration.

Airy Sky inherits Atlas's geometry outright: the 1.75px grid, the 10–46px
type scale, radii 6/10/14 and control heights 28/34/42 are unchanged. What
changed is the palette, the type, and which theme is the default — **light
is the default here**, declared on a bare `:root`, with dark as the remap.
`docs/brand/contrast_check.py` classifies blocks by that selector shape, so
the two must stay in step.

`tokens/tokens.css` and `tokens/fonts.css` are authored here rather than
vendored, so corrections go directly into them. `tokens/base.css` is still
the Atlas file vendored on 5 August 2026, unchanged, because its glass,
index label and numeral devices carried over as they were. `overrides.css`
is kept, and kept in the checker's sources, but is currently empty.

## What is here, and what is not

**Here:** the token layer (`tokens/tokens.css`, `tokens/base.css`), the
webfont imports (`tokens/fonts.css` — Outfit and Figtree via `@fontsource`),
and the accessibility standard (`accessibility.md`).

**Not here:** no component set. Every product-level shape (`ds-field`,
`ds-action`, `ds-hero`, `ds-label`, `ds-eyebrow`, `ds-skip-link`,
`ds-photo`, `ds-scrim`, `ds-card-photo`, `ds-icon-button`, `ds-dot`) is this
application's
own, built in `src/index.css` against the semantic tokens and the three
devices `base.css` supplies, `.v-idx` (the index label), `.v-glass` (the
panel) and `.v-num` (figures), rather than reimplemented differently.

## Provenance

| File | Origin |
|---|---|
| `tokens/tokens.css` | Airy Sky Editorial, authored here |
| `tokens/fonts.css` | Outfit and Figtree via `@fontsource`, authored here |
| `tokens/base.css` | Atlas, vendored byte-identical on 5 August 2026 and not modified since |
| `tokens/index.css` | Import order for the three files above, authored here |
| `overrides.css` | Product corrections on top of the tokens, currently empty |
| `accessibility.md` | This product's accessibility standard, rewritten for Airy Sky |

`python docs/brand/contrast_check.py` reads the palette from
`tokens/tokens.css` **and** `overrides.css` in that order and fails CI on any
pair below WCAG 2.2 AA. Any change to either file is checked on the next
push.

`overrides.css` once held four Atlas corrections, status text on its own
tint and the selected-fare-card border against a glass panel, each of which
landed under AA once rendered. Airy Sky's tints were chosen against these
grounds in the first place, so the file is empty now. The Atlas-era
measurements are in the [changelog](../../../CHANGELOG.md).

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

**`base.css` stays unlayered, deliberately — as does `.ds-hero`.** Wrapping
`base.css`'s import in a Tailwind `@layer` block, so its plain `h1 { }` rule
would lose to `.ds-hero` on layer order instead of specificity, reliably
made the Vite/Lightning CSS production build drop the imported file's
content outright — sometimes just its `::before` rules (the bloom behind the
glass, the sheen on every panel), sometimes the whole file. Left unlayered,
as the vendor ships it, `base.css` bundles correctly. The one real
conflict this creates — `base.css`'s `h1 { font-weight: 600 }` versus this
product's `.ds-hero` at 700 — is resolved the other way instead: `.ds-hero`
is declared unlayered too, so a class selector beats an element selector on
plain CSS specificity, no layer required. See the comments in
`tokens/index.css` and `../../index.css`.

Two rules the design system sets, and that review checks for:

1. **Never use a primitive directly.** `--paper`, `--ink` and `--deep-sky`
   do not belong in component code. Use the semantic alias, `--ground`,
   `--text-primary`, `--fill-accent`. Re-theming works only if this holds,
   and it is exactly what broke under Atlas before the accent was split into
   `--fill-accent` (backgrounds) and `--text-accent` (type).
2. **One primary action per view.** The deep sky fill of
   `.ds-action--primary` means "act". A list of options gets one primary
   button at most, and it is never spent on N equally weighted rows.
