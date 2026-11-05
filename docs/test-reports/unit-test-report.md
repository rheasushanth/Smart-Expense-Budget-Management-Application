# Unit Test Report

**Project:** Smart Expense & Budget Management Application
**Group:** G-15
**Date:** 5 November 2026
**Commit:** `1429bc4` on `main`
**Environment:** Python 3.12.6, Django 5.2.18, pytest 9.1.1, pytest-django 4.14.0, SQLite
**Command:** `pytest --junitxml=docs/test-reports/artifacts/junit.xml`

## Result

| | |
| --- | --- |
| Test functions | **195** |
| Executed cases (including subtests) | 225 |
| Passed | **225** |
| Failed | 0 |
| Errors | 0 |
| Skipped | 0 |
| Duration | 225.4 s |

**All tests passed.** Machine-readable output: [`artifacts/junit.xml`](artifacts/junit.xml).

## Tests by module

| Module | Tests | Covers |
| --- | --- | --- |
| `accounts` | 25 | FR-001 to FR-004, SEC-001, SEC-002, SEC-004, SEC-006 |
| `budgets` | 44 | FR-012 to FR-016 |
| `categories` | 11 | FR-020 to FR-022 |
| `config` | 2 | NFR-002 health endpoint |
| `recurring` | 23 | FR-019, FR-024 |
| `reports` | 53 | FR-017, FR-018, NFR-001 |
| `transactions` | 37 | FR-005 to FR-011, FR-023, NFR-004, SEC-003, SEC-005 |
| **Total** | **195** | |

## Test levels

Levels follow Validation Spec v1.1 Section 4.

| Level | Where | Notes |
| --- | --- | --- |
| Unit | `budgets/services.py`, `budgets/alerts.py`, `recurring/tasks.py`, `reports/queries.py` | Business rules exercised directly, without HTTP |
| Integration | CSV import, recurring generation, sandbox sync | Django test client against a test database; the sandbox adapter is mocked (NFR-006) |
| System | Auth, transaction, report, dashboard and admin flows | Full request/response through the test client |
| Negative | Invalid amounts, dates, categories, encodings, oversized uploads | Equivalence partitioning per Validation Spec Section 4 |
| Performance (guard) | `reports/tests.py::TCPERF01QueryCost` | Pins query counts so the NFR-001 optimisations cannot regress between load runs |

## Continuous integration

Every push and pull request runs the suite through `.github/workflows/ci.yml`. A second
step enforces the NFR-005 threshold with `--cov-fail-under=70` scoped to the
`budgets`, `recurring` and `transactions` apps. The gate has been verified to fail when
the threshold is raised above actual coverage, so it is known to bite rather than merely
to be present.

## Not covered by this report

Three cases in the Validation Spec cannot be executed by the automated suite and are
accounted for in the [System Validation Report](system-validation-report.md):
TC-PERF-01, TC-AVAIL-01 and TC-POL-01. All three require a deployed PostgreSQL
environment, which does not yet exist (issue #70, deviation D-04).
