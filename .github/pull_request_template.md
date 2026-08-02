## What this changes

<!-- One or two sentences. What is different afterwards, not what you did. -->

## Why

<!-- The problem, not the solution. If it fixes a recorded defect, cite it:
     DEF-001, defined in docs/analysis/current-state-assessment.md. -->

## Verification

<!-- What you ran, and what it said. "make check passed" is enough for most
     changes; say more when the change is not covered by it. -->

- [ ] `make check` passes
- [ ] `make e2e` passes, or the change cannot affect the interface
- [ ] New behaviour has a test that fails without the change
- [ ] Docs updated, or the change does not contradict any

## What this does not cover

<!-- Required. Every phase of this project states its gaps; a pull request
     should too. "Nothing" is a valid answer if it is true. -->
