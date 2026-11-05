# Code Coverage Report (Statement Coverage)

**Project:** Smart Expense & Budget Management Application
**Group:** G-15
**Date:** 5 November 2026
**Commit:** `7ea5525` on `main`
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
| Production code (tests and migrations excluded) | 1225 | 140 | **88.6%** |
| NFR-005 scope — `budgets`, `recurring`, `transactions` | 678 | 60 | **91.2%** |
| Whole measured tree, including test modules | 2733 | 140 | 92.9% |

**NFR-005 requires at least 70% line coverage on the budgets, recurring and
transactions business-logic apps. Measured: 91.2%. The requirement is met.**

## Per application

Tests and migrations excluded, so these figures describe production code only.

| Application | Statements | Missed | Line coverage |
| --- | ---: | ---: | ---: |
| `reports` | 138 | 1 | 99.3% |
| `budgets` | 191 | 5 | 97.4% |
| `recurring` | 143 | 16 | 88.8% |
| `transactions` | 344 | 39 | 88.7% |
| `categories` | 111 | 15 | 86.5% |
| `accounts` | 238 | 47 | 80.3% |
| `config` | 60 | 17 | 71.7% |
| **Total** | **1225** | **140** | **88.6%** |

## A note on the measurement scope

The CI threshold step measures `--cov=budgets --cov=recurring --cov=transactions`,
which includes those apps' own `tests.py` modules. Test modules are executed in full,
so they score close to 100% and raise the reported figure — the 97.8% recorded against
the NFR-005 gate in `DEVIATIONS.md` was measured that way.

This report excludes test modules, which is the more honest measure of how much
*production* code the suite reaches. Both figures are given above so the difference is
visible rather than hidden. Either way the 70% requirement is comfortably met.

## Where the uncovered lines are

| Area | Line coverage | Reason |
| --- | ---: | --- |
| `config/settings.py` | 71.7% | The `if not DEBUG:` production block is not exercised under test settings. Related to issue #61. |
| `accounts/views.py`, `accounts/models.py` | 80.3% | Manager branches for superuser creation, and some error paths in profile handling |
| `transactions/sandbox_adapter.py` | 67% | Live REST implementation; tests run against the mock, as NFR-006 requires |
| `transactions/importer.py` | 78% | Defensive branches for malformed uploads that the form rejects first |

None of the uncovered areas is business logic required by a functional requirement.

See also the [Branch Coverage Report](branch-coverage-report.md), which measures
decision outcomes rather than executed lines and is the stricter of the two.
