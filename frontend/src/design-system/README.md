# AF Design System — vendored token layer

DS Airlines does not have its own visual identity. It is a product built on
**AF**, the design system by Apostolos Fysekidis: AF supplies the visual
system, and Delos Skyways supplies the verbal one — the name, the
positioning, the fare names and the words on screen. See
[`docs/brand/brandbook.md`](../../../docs/brand/brandbook.md) for the split.

## What is here, and what is not

**Vendored:** the token layer (`tokens/*.css`), the webfonts they reference
(`assets/fonts/`), and the accessibility standard (`accessibility.md`).

**Not vendored:** AF's 28 React components. This application builds its own
components against these tokens instead. The reason is fit — an airline
booking surface needs a fare selector and a seat field, not a
`SidebarNav` and a `MiniBarChart` — and the token layer is where the brand
actually lives. Components that duplicate AF's role (`Button`, `Field`,
`Dialog`) follow AF's documented behaviour rather than reimplementing it
differently.

## Provenance

| | |
|---|---|
| Source | `AF Design System`, local working copy |
| Vendored | 1 August 2026 |
| Files | `tokens/{base,color,elevation,fonts,motion,space,typography}.css`, 10 `.woff2`, `accessibility.md` |
| Modifications | **None.** Every file is byte-identical to source. |

The token files are unmodified deliberately. `tokens/fonts.css` resolves
webfonts as `../assets/fonts/…`, so the `tokens/` ÷ `assets/` structure is
reproduced exactly and the files can be re-copied over the top when AF
changes without a merge.

This is a manual copy, so it can go stale. Re-syncing means re-copying those
files and re-running `python docs/brand/contrast_check.py`, which reads the
palette from `tokens/color.css` and fails CI on any pair below WCAG 2.2 AA.

## Using it

`src/main.tsx` imports `tokens/index.css` — which pulls the files in AF's own
order — *before* `src/index.css`, which bridges the tokens into Tailwind's
`@theme` so they are reachable as utilities (`bg-card`, `text-strong`,
`border-hairline`).

**The import must stay in `main.tsx`.** Reaching the token entry through an
`@import` inside `src/index.css`, nested under Tailwind's own `@import`,
stops Vite rebasing the `@font-face` urls in `fonts.css`: the build emits
`../assets/fonts/…` unchanged, ships no `.woff2` at all, and Archivo and Plex
Mono fall back to Helvetica without any build error. Importing it as its own
CSS module resolves the paths relative to the token files, where they are
correct. Ten font files in `dist/assets/` is the check that this still works.

Two rules from AF's brief that the review checks for:

1. **Never use a base ramp directly.** `--ink-800` and `--brand-500` do not
   belong in component code; use the semantic alias — `--surface-card`,
   `--action-primary-bg`. Re-theming works only if this holds.
2. **Signal means "act".** One primary action per view. Brass
   (`--coral-*`) is editorial warmth and is never an action.
