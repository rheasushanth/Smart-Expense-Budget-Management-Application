# Branch Coverage Report

**Project:** Smart Expense & Budget Management Application
**Group:** G-15
**Date:** 5 November 2026
**Commit:** `7ea5525` on `main`
**Tool:** coverage.py 7.16.2 with `--cov-branch`

Branch coverage measures whether each decision point has been taken both ways — an
`if` that is only ever entered with a true condition counts as a covered *line* but a
half-covered *branch*. It is the stricter measure and is always lower than statement
coverage.

**This is the first time branch coverage has been measured on this project.** Until
this report, `ci.yml` ran `--cov` without `--cov-branch`, so only statement coverage
existed. The CI pipeline has been updated to collect it on every run.

## Headline

| Scope | Branches | Partially covered | **Branch coverage** |
| --- | ---: | ---: | ---: |
| Production code (tests and migrations excluded) | 298 | 59 | **74.2%** |
| NFR-005 scope — `budgets`, `recurring`, `transactions` | 186 | 44 | **76.3%** |

## Per application

| Application | Branches | Partial | Branch coverage |
| --- | ---: | ---: | ---: |
| `reports` | 34 | 1 | 97.1% |
| `budgets` | 48 | 5 | 89.6% |
| `recurring` | 28 | 6 | 78.6% |
| `transactions` | 110 | 33 | 70.0% |
| `accounts` | 62 | 10 | 64.5% |
| `config` | 4 | 2 | 50.0% |
| `categories` | 12 | 2 | 33.3% |
| **Total** | **298** | **59** | **74.2%** |

## Reading these figures honestly

Branch coverage of 74.2% against statement coverage of 88.6% is the normal gap, and
the per-app spread is informative rather than alarming. Three observations worth
recording:

**`categories` at 33.3% looks worse than it is.** The app has only 12 branches in
total, so two partially covered decisions move the percentage by 17 points. The
absolute gap is two branches, not a systematic hole. Percentages on small denominators
should not be read as a quality signal.

**`transactions` at 70.0% is the real gap**, because it holds 110 branches — more than
a third of the codebase's decision points — and 33 are half-covered. The uncovered
outcomes are concentrated in `importer.py` and `sandbox_adapter.py`: defensive paths
for malformed uploads that the form rejects before the importer sees them, and the
live REST adapter, which by NFR-006 is deliberately never exercised in tests.

**`config` at 50.0% is expected.** Its branches are the `if not DEBUG:` production
settings block, which test settings never enter. Related to issue #61.

## No threshold is set for branch coverage

NFR-005 specifies a line-coverage threshold of 70% and says nothing about branches.
The CI gate therefore remains line-based; this report is measurement, not enforcement.
Were the same 70% applied to branches, the production-code figure of 74.2% and the
NFR-005-scope figure of 76.3% would both pass, but `accounts`, `config` and
`categories` would individually fall short.

Recommendation for Sprint 3 or a future iteration: raise `transactions` branch
coverage by exercising the importer's malformed-input paths directly rather than only
through the form, which is where the largest concentration of half-covered decisions
sits.
