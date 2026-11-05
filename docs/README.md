# docs

Test documentation and reports for the Smart Expense & Budget Management Application
(Group G-15), produced for Mini-Project Deliverable Part-3.

## Test reports

| Report | Contents |
| --- | --- |
| [Unit Test Report](test-reports/unit-test-report.md) | 195 tests, all passing, broken down by module and test level |
| [System Validation Report](test-reports/system-validation-report.md) | All 37 Validation Spec test cases mapped to status and evidence |
| [Code Coverage Report](test-reports/code-coverage-report.md) | Statement coverage — 85.7% on production code, 85.8% on the NFR-005 scope |
| [Branch Coverage Report](test-reports/branch-coverage-report.md) | Decision coverage — 72.8% on production code, measured for the first time |

Machine-readable artifacts are in [`test-reports/artifacts/`](test-reports/artifacts/):
`junit.xml`, `coverage.xml` and `coverage.json`, all from the same run.

## Test case documentation

| Document | Contents |
| --- | --- |
| [**Test Case Document v1.2**](test-case-document-v1.2.md) | **The current Test Case Document.** All 37 cases with the expected results the delivered system meets, superseding Sections 13.1 and 13.2 of the v1.1 PDF |
| [Test Case Update Log](test-case-updates.md) | Narrative of what changed and why, supporting v1.2 |
| [Sprint 3 Plan](sprint-3-plan.md) | Spillover sprint scope, sequence and blockers |
| [Deployment](deployment.md) | The Render environment, its constraints, and the procedure TC-POL-01 reviews |

Test Case Document v1.2 supersedes Sections 13.1 and 13.2 of
`03_DESIGN/G15_ValidationSpec_v2.pdf` (Validation Spec v1.1, 13 October 2026). The v1.1
PDF remains the baseline for the sections v1.2 does not reissue — scope, test levels,
the risk register and the traceability matrix.

## Headline figures

| Measure | Value |
| --- | --- |
| Tests | 195, all passing |
| Test cases passing | 34 of 37 |
| Test cases failing | 0 |
| Line coverage (production code) | 85.7% |
| Line coverage (NFR-005 scope, threshold 70%) | 85.8% |
| Branch coverage (production code) | 72.8% |

Three test cases — TC-PERF-01, TC-AVAIL-01 and TC-POL-01 — are not fully executed. All
three require a deployed PostgreSQL environment, which does not yet exist. This is
tracked as issue #70, recorded as deviation D-04, and carried into Sprint 3.

## Reproducing the reports

From `G15/04_IMPLEMENTATION_TESTING/source-code/`:

```
pytest --cov=accounts --cov=budgets --cov=categories --cov=config \
       --cov=recurring --cov=reports --cov=transactions \
       --cov-branch \
       --cov-report=xml:../../../docs/test-reports/artifacts/coverage.xml \
       --cov-report=json:../../../docs/test-reports/artifacts/coverage.json \
       --junitxml=../../../docs/test-reports/artifacts/junit.xml
```

CI runs the same collection on every push; see `.github/workflows/ci.yml`.
