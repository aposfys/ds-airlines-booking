# Documentation

Everything that is not code. Read in this order if you are new to the
project.

---

## 1 · What was wrong

**[Current-state assessment](analysis/current-state-assessment.md)**, an
audit of commit `f1f732d`, my own March 2026 port of the 2022 Flask
coursework to FastAPI and React. 30 defects, 4 Critical, each with its business
impact, the evidence, and where it was resolved. It also lists what was
deliberately deferred and what was accepted, so the omissions are explicit.

This is the document the project is built around. Start here.

## 2 · Why it was built this way

**[ADR-001 · PostgreSQL over MongoDB](adr/0001-postgresql-over-mongodb.md)** —
the decision that shaped Phase 1. Context, the three options considered, what
was chosen and what it cost.

**[ADR-002 · A server-side weather proxy](adr/0002-server-side-weather-proxy.md)**
covers why forecasts come through the API rather than from the browser.

New architecture decisions get a numbered file in `adr/`, following the same
shape: context, options, decision, consequences.

## 3 · Who it is for

**[Personas](product/personas.md)** — four people the product serves, each
ending with what they cost the codebase. A persona that changes nothing is
decoration.

**[User stories](product/user-stories.md)** — 17 stories with Gherkin
acceptance criteria, and a traceability matrix from story to endpoint to the
test that proves it. Status is Done, Partial or Not started, and the Partials
carry their limitation.

## 4 · What it says and how it looks

**[Airy Sky Editorial](design/airy-sky-editorial.md)** — the design system the
interface runs on: the Paper & Sky palette, Outfit and Figtree, glass, and the
rule that no text ever sits on bare photography.

**[Product brand](brand/brandbook.md)**, positioning, network, fare
architecture and voice. It owns only the words. The visual system belongs to
[Airy Sky Editorial](design/airy-sky-editorial.md), whose token layer lives in
[`frontend/src/design-system/`](../frontend/src/design-system/README.md).

**[contrast_check.py](brand/contrast_check.py)** reads the palette out of
the token files the application actually loads, composites translucent
values in sRGB, and fails CI if any of its 17 pairs drops below WCAG 2.2 AA
in either theme.

```bash
make contrast
```

## 5 · How it is verified

**[Test strategy](qa/test-strategy.md)** — the layers, how to run each of
them, a 42-case manual pass covering every page, and an honest list of what
is still not covered.

---

## Conventions

- **Assertions are checkable.** Every number in these documents comes from
  something that can be run. Where a claim cannot be verified, it says so.
- **Gaps are named.** Each document ends with what it does not cover. An
  empty row in the traceability matrix is more useful than a missing one.
- **Defects are referenced by identifier.** `DEF-001` and friends are defined
  in the assessment and cited from code comments, commit messages and tests.

## Images

`screenshots/` holds the stills used by the root README and `media/` the
walkthrough. Both are captured from a running stack by `make screenshots` and
`make walkthrough`, not mocked up.
