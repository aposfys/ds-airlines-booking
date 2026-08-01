# AF Accessibility Standard

**Target: WCAG 2.2 Level AA**, applied to every AF surface, plus the EU public/private-sector deadline of **28 June 2025** referenced in the 1xINTERNET handbook you supplied. AA is the floor, not the ambition: most AF colour pairs land in AAA territory because the palette was built from measured contrast rather than picked and checked afterwards.

Accessibility in AF is a **token and component responsibility**. A designer using the system correctly cannot easily produce an inaccessible screen; where a decision can still go wrong, it is listed below.

---

## 1 · The ten pitfalls from the handbook, answered

| # | Pitfall (1xINTERNET) | How AF answers it | Where |
| --- | --- | --- | --- |
| 01 | **Poor colour contrast** | Every semantic pair is measured in OKLCH → sRGB before it becomes a token. Body text 13.07:1, muted text 5.75:1, primary action 8.19:1, status pairs ≥6.47:1. Sub-4.5:1 values exist (`--text-faint` 3.42:1) and are documented as non-text only. | `tokens/color.css`, `guidelines/cards/color-contrast.html` |
| 02 | **Missing or poor alt text** | Decorative icons are `aria-hidden`; meaningful ones require `label`. Charts are one `role="img"` with the full series in the alternative. Image placeholders in the kits carry a written description of what belongs there, so the alt text is specified before the photo exists. | `Icon`, `MiniBarChart` |
| 03 | **Improper heading hierarchy** | One `h1` per screen; kits and the manual step h1 → h2 → h3 with no skips. `Card` titles are mono *eyebrows*, not headings — a card that needs a heading gets a real one inside it. | `ui_kits/**`, `Card` |
| 04 | **Inconsistent or missing focus indicators** | One global rule: `:focus-visible { outline: 2px solid var(--focus-ring); outline-offset: 2px }`. `--focus-ring` is Coral on dark (8.19:1) and Brand blue-600 on light. Focus is never animated and `outline: none` appears nowhere in the system. | `tokens/base.css` |
| 05 | **Keyboard navigation issues** | Native elements by default: `Select` is a real `<select>`, `Switch` a real checkbox with `role="switch"`, tags and tabs are `<button>`s. `Tabs` uses roving `tabIndex`. `Dialog` traps focus, returns it to the trigger, and closes on Escape. Skip link (`.af-skip-link`) is the first element of every kit. | components, `tokens/base.css` |
| 06 | **Non-descriptive links and buttons** | Copy rule, enforced in review: buttons name the outcome and the amount — `Charge 302,62 €`, `Log a case`. "Click here", "Learn more", "Submit" and "OK" are banned in `readme.md` → CONTENT FUNDAMENTALS. | copy rules |
| 07 | **No or incomplete form labels** | `Field` renders a visible `<label htmlFor>`; AF never uses a placeholder as a label. Errors render `role="alert"`, replace help text, and describe the fix — not just the failure. Controls take `aria-invalid`. | `Field`, `Input`, `Select` |
| 08 | **Missing or improper ARIA** | ARIA only where HTML runs out: `role="dialog aria-modal"`, `role="status"` on `AgentStatus`, `role="progressbar"` on `ProgressMeter`, `aria-current="page"` in `SidebarNav`, `aria-pressed` on toggle tags. Landmarks (`nav`, `main`, `header`) are structural in every kit — no `role="navigation"` on a `<nav>`. | components, kits |
| 09 | **Autoplaying media** | Nothing autoplays with sound. The only looping motion is the decorative `Marquee`, which is `aria-hidden`, pauses on hover and stops entirely under `prefers-reduced-motion`. `StreamingText` renders instantly when motion is reduced. | `Marquee`, `StreamingText` |
| 10 | **No text resizing / zoom support** | Type is set in `rem` with fluid `clamp()`; no `max-height` on text containers; layout is flex/grid with `gap`, so 200% zoom and 400% reflow (1.4.10) do not clip. `text-size-adjust` is not disabled. No fixed viewport scale. | `tokens/typography.css` |

---

## 2 · Success criteria AF meets by construction

**Perceivable**
- **1.4.3 Contrast (minimum)** — 4.5:1 body, 3:1 for ≥24px or ≥19px bold. Measured table in `guidelines/cards/color-contrast.html`.
- **1.4.11 Non-text contrast** — `--border-subtle` (16% white) and stronger on all control edges; focus ring, switch track and chart bars all clear 3:1 against their ground.
- **1.4.1 Use of colour** — status always carries a word (`OVERDUE`), current nav carries `aria-current` plus a positional 2px edge, chart series carry printed values, form errors carry text and an icon.
- **1.4.12 Text spacing** — line-height 1.45 UI / 1.62 prose; no fixed heights on text blocks.
- **1.4.10 Reflow** — single-column at 576px; the 248px sidebar collapses to a 64px rail, then to a top sheet.

**Operable**
- **2.5.8 Target size (minimum, 2.2)** — 44×44px minimum. Small (30px) buttons and icon buttons extend their hit area with a pseudo-element rather than shrinking the target.
- **2.4.7 Focus visible** and **2.4.11 Focus not obscured (2.2)** — sticky-bar height is a single custom property, and both the bar and the `scroll-margin-top` on every jump target read from it, so a focused or jumped-to heading can never hide under it.
- **2.4.3 Focus order** — DOM order is reading order; dialogs move focus in and back out.
- **2.3.3 Animation from interactions** and **2.2.2 Pause, stop, hide** — all durations collapse to 1ms under `prefers-reduced-motion`; the marquee stops.
- **2.1.1 Keyboard** — no component requires a pointer. No drag-only interaction exists in the system (2.5.7).

**Understandable**
- **3.3.2 Labels or instructions** — visible label plus help text on every field.
- **3.3.1 / 3.3.3 Error identification and suggestion** — `role="alert"`, adjacent to the field, states the correction. Never the toast alone.
- **3.2.4 Consistent identification** — one `Button` component, one meaning for Coral, one meaning for the hatch pattern.
- **3.3.7 Redundant entry (2.2)** — unit, building and period carry across screens in the kits.

**Robust**
- **4.1.2 Name, role, value** — `IconButton` cannot render without `label`; toggles expose `aria-pressed`; live regions announce assistant steps.

---

## 3 · Rules that follow from this palette

1. **Coral is never text on a light ground.** `--coral-500` on `--paper` is 2.30:1. In light theme the primary button inverts: ink fill, Coral label (8.19:1). Coral text on light uses `--coral-800` (7.51:1).
2. **`--text-faint` is not for text.** 3.42:1 — borders, disabled labels, icons ≥24px only.
3. **Status tints are a pair.** Never a `fg` on an arbitrary surface; always `--status-*-fg` on its `--status-*-bg`.
4. **Never place body copy directly on photography.** Use the protection gradient or a card.
5. **A disabled control still needs to be readable.** `--action-disabled-fg` is 3.4:1 against its ground and is always accompanied by an explanation of why it is disabled.

## 4 · Review checklist (run before any AF screen ships)

- [ ] Tab through: every interactive element reachable, visible ring, order matches reading order.
- [ ] Escape closes every overlay; focus returns to the trigger.
- [ ] Zoom to 200%, then 400% at 1280px wide: nothing clipped, nothing overlapping.
- [ ] `prefers-reduced-motion: reduce` on: nothing moves, nothing is lost.
- [ ] Headings only: does the outline read as the page structure? One `h1`?
- [ ] Turn colour off (greyscale): is every status still legible?
- [ ] Screen reader pass on one flow: are icon buttons named, is the table captioned, are errors announced?
- [ ] Every image has alt text that states its purpose, not its filename.
- [ ] Contrast spot-check on any new colour pair, and add it to the matrix card.

## 5 · Not yet done — needs a real audit
This document is a design standard, not a compliance certificate. Before AF claims conformance it needs an axe/WAVE automated pass, a manual NVDA + VoiceOver run, a keyboard-only task walkthrough, a cognitive-load review of the expenses flow, and a published accessibility statement. The handbook you supplied says the same thing about its own checklist: it indicates whether a professional audit is warranted.
