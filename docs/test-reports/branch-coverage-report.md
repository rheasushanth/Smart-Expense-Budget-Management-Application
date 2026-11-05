# Branch Coverage Report

**Project:** Smart Expense & Budget Management Application
**Group:** G-15
**Date:** 5 November 2026
**Commit:** `1429bc4` on `main`
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
| Production code (tests and migrations excluded) | 312 | 59 | **72.8%** |
| NFR-005 scope — `budgets`, `recurring`, `transactions` | 194 | 44 | **73.2%** |

## Per application

| Application | Branches | Partial | Branch coverage |
| --- | ---: | ---: | ---: |
| `reports` | 40 | 1 | 97.5% |
| `budgets` | 48 | 5 | 89.6% |
| `recurring` | 28 | 6 | 78.6% |
| `transactions` | 118 | 33 | 65.3% |
| `accounts` | 62 | 10 | 64.5% |
| `config` | 4 | 2 | 50.0% |
| `categories` | 12 | 2 | 33.3% |
| **Total** | **312** | **59** | **72.8%** |

## Reading these figures honestly

Branch coverage of 72.8% against statement coverage of 85.7% is the normal gap, and
the per-app spread is informative rather than alarming. Four observations worth
recording:

**`categories` at 33.3% looks worse than it is.** The app has only 12 branches in
total, so two partially covered decisions move the percentage by 17 points. The
absolute gap is two branches, not a systematic hole. Percentages on small denominators
should not be read as a quality signal.

**`transactions` at 65.3% is the real gap**, because it holds 118 branches — more than
a third of the codebase's decision points — and 33 are half-covered. The uncovered
outcomes are concentrated in `importer.py` and `sandbox_adapter.py`: defensive paths
for malformed uploads that the form rejects before the importer sees them, and the
live REST adapter, which by NFR-006 is deliberately never exercised in tests.

**`config` at 50.0% is expected.** Its branches are the `if not DEBUG:` production
settings block, which test settings never enter. Related to issue #61.

**`reports` is the strongest at 97.5%**, which is where the NFR-001 query work lives.
A single partially covered branch remains.

## No threshold is set for branch coverage

NFR-005 specifies a line-coverage threshold of 70% and says nothing about branches.
The CI gate therefore remains line-based; this report is measurement, not enforcement.
Were the same 70% applied to branches, the production-code figure of 72.8% and the
NFR-005-scope figure of 73.2% would both pass, but `transactions`, `accounts`, `config`
and `categories` would individually fall short.

Recommendation for Sprint 3: raise `transactions` branch coverage by exercising the
importer's malformed-input paths directly rather than only through the form, which is
where the largest concentration of half-covered decisions sits.
