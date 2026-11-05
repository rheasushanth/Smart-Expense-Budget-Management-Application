# Code Coverage Report (Statement Coverage)

**Project:** Smart Expense & Budget Management Application
**Group:** G-15
**Date:** 5 November 2026
**Commit:** `1429bc4` on `main`
**Tool:** coverage.py 7.16.2 via pytest-cov 7.1.0
**Command:**

```
pytest --cov=accounts --cov=budgets --cov=categories --cov=config \
       --cov=recurring --cov=reports --cov=transactions \
       --cov-branch --cov-report=xml --cov-report=json
```

Machine-readable output: [`artifacts/coverage.xml`](artifacts/coverage.xml),
[`artifacts/coverage.json`](artifacts/coverage.json).

## Headline

| Scope | Statements | Missed | **Line coverage** |
| --- | ---: | ---: | ---: |
| Production code (tests and migrations excluded) | 1284 | 183 | **85.7%** |
| NFR-005 scope — `budgets`, `recurring`, `transactions` | 723 | 103 | **85.8%** |
| Whole measured tree, including test modules | 2862 | 183 | 91.6% |

**NFR-005 requires at least 70% line coverage on the budgets, recurring and
transactions business-logic apps. Measured: 85.8%. The requirement is met.**

## Per application

Tests and migrations excluded, so these figures describe production code only.

| Application | Statements | Missed | Line coverage |
| --- | ---: | ---: | ---: |
| `reports` | 152 | 1 | 99.3% |
| `budgets` | 191 | 5 | 97.4% |
| `recurring` | 143 | 16 | 88.8% |
| `categories` | 111 | 15 | 86.5% |
| `accounts` | 238 | 47 | 80.3% |
| `transactions` | 389 | 82 | 78.9% |
| `config` | 60 | 17 | 71.7% |
| **Total** | **1284** | **183** | **85.7%** |

## Coverage fell during Sprint 2, and the reason is worth recording

An earlier measurement of this branch, taken before PR #68 merged, gave 88.6% on
production code. The figure is now 85.7%. Coverage did not fall because tests were
removed — 8 tests were *added* — but because PR #68 introduced
`transactions/management/commands/seed_perf_data.py`, a 43-statement operational
command that seeds the TC-PERF-01 dataset and has no test of its own. It is counted as
production code, so it dilutes the percentage.

This is the honest explanation and it is a real gap, not a measurement artefact: the
command is executable code that nothing verifies. The recommended fix is a short test
invoking it with `--count=5` and asserting the row count, which would restore roughly
three points. Carried into Sprint 3.

`transactions` is the only app whose figure moved; every other app is unchanged.

## A note on the measurement scope

The CI threshold step measures `--cov=budgets --cov=recurring --cov=transactions`,
which includes those apps' own `tests.py` modules. Test modules are executed in full,
so they score close to 100% and raise the reported figure — the 97.8% recorded against
the NFR-005 gate in `DEVIATIONS.md` was measured that way.

This report excludes test modules, which is the more honest measure of how much
*production* code the suite reaches. Both figures are given above so the difference is
visible rather than hidden. Either way the 70% requirement is comfortably met.

## Where the uncovered lines are

| Area | Reason |
| --- | --- |
| `transactions/management/commands/seed_perf_data.py` | Operational command added by PR #68; no test. See above. |
| `config/settings.py` | The `if not DEBUG:` production block is not exercised under test settings. Related to issue #61. |
| `accounts/views.py`, `accounts/models.py` | Manager branches for superuser creation, and some error paths in profile handling |
| `transactions/sandbox_adapter.py` | Live REST implementation; tests run against the mock, as NFR-006 requires |
| `transactions/importer.py` | Defensive branches for malformed uploads that the form rejects first |

No functional requirement depends on an uncovered path.

See also the [Branch Coverage Report](branch-coverage-report.md), which measures
decision outcomes rather than executed lines and is the stricter of the two.
