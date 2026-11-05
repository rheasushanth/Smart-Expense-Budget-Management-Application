# Sprint 3 — Spillover Sprint

**Project:** Smart Expense & Budget Management Application
**Group:** G-15
**Declared:** 5 November 2026
**Scope:** Work carried over from Sprint 2, under Part-3 deliverable item 3

Sprint 2 delivered every functional requirement, FR-001 to FR-024. The items below are
non-functional and operational work that could not complete, and they are carried into
Sprint 3 rather than left unaccounted for.

## Carried items

| # | Issue | Owner | Blocked by |
| --- | --- | --- | --- |
| 1 | **#70 — Deploy to Render (PostgreSQL environment)** | unassigned | Nothing. Needs a Render account and service to be created. |
| 2 | **#61 — `DJANGO_DEBUG` defaults to `True`** | unassigned | Nothing. One-line change plus a regression test. |
| 3 | **#27 — NFR-001 measured run (TC-PERF-01)** | Rhea Sushanth | #70 |
| 4 | **#33 — NFR-007 compliance review (TC-POL-01)** | duplicatenode | #70 |
| 5 | **NFR-002 measured run (TC-AVAIL-01)** | duplicatenode | #70, then 7 days of polling |

## The single blocker

Four of the five items depend on item 1. Nothing else in Sprint 3 can be evidenced until
the application is deployed to a PostgreSQL environment, and item 5 then needs seven
calendar days of health-URL polling before it can be reported. **Item 1 is therefore the
first task of Sprint 3 and should not be scheduled behind anything else.**

Item 2 must land **before** item 1. `DJANGO_DEBUG` currently defaults to `True`, so a
deployment that does not set the variable runs with `SECURE_SSL_REDIRECT`,
`SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_CONTENT_TYPE_NOSNIFF` and
`X_FRAME_OPTIONS` all disabled, and still serves traffic with nothing signalling the
problem. Deploying first would create a window in which that is real.

## Sequence

1. #61 — fail-closed debug setting, with a test asserting the five security settings hold when `DEBUG = False`
2. #70 — `render.yaml`, service created, environment variables set, `/healthz/` returning 200
3. Seed the deployed database and run TC-PERF-01; update deviation D-04 with the measured result
4. Start TC-AVAIL-01 polling — this governs the earliest possible completion date
5. #33 / TC-POL-01 — review the deployed hosting setup

## Documentation work also carried

Three deviations need the design specification corrected so that code and documents
agree in the submitted artefacts:

- **D-05** — SW Design Section 4.4 to describe per-row atomicity plus idempotent retry for CSV import
- **D-06** — SW Design Section 4.4 to describe a persisted `SecurityEvent` table rather than rotating log files
- **Test Case Document** — reissue from `docs/test-case-updates.md`

## Two open questions from the Sprint 2 reviews

Neither is a defect, and both need a team decision rather than a code change:

- `role_required` writes a `SecurityEvent` row for anonymous requests before the authentication check, with no rate limit, so an unauthenticated caller can grow the table without bound. Tracked on PR #69.
- The `SecurityEvent` table has no retention policy.

## Definition of done for Sprint 3

- TC-PERF-01, TC-AVAIL-01 and TC-POL-01 executed and reported, or a documented reason why not
- D-04, D-05 and D-06 closed, with the design specification reissued
- Test reports in `docs/test-reports/` regenerated against the final `main`
