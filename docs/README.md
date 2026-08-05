# Documentation

Everything that is not code. Read in this order if you are new to the
project.

---

## 1 · What was wrong

**[Current-state assessment](analysis/current-state-assessment.md)** — an
audit of the original code. 30 defects, 4 Critical, each with its business
impact, the evidence, and where it was resolved. It also lists what was
deliberately deferred and what was accepted, so the omissions are explicit.

This is the document the project is built around. Start here.

## 2 · Why it was built this way

**[ADR-001 · PostgreSQL over MongoDB](adr/0001-postgresql-over-mongodb.md)** —
the decision that shaped Phase 1. Context, the three options considered, what
was chosen and what it cost.

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

**[Product brand](brand/brandbook.md)** — positioning, network, fare
architecture and voice. It owns only the words: the visual system belongs to
[VANE](../frontend/src/design-system/README.md).

**[contrast_check.py](brand/contrast_check.py)** — reads the palette out of
the token files the application actually loads, converts hex/rgba to linear
sRGB, and fails CI if any pair drops below WCAG 2.2 AA in either theme.

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

`images/` holds the screenshots used by the root README. They are captured
from a real running stack, not mocked up.
