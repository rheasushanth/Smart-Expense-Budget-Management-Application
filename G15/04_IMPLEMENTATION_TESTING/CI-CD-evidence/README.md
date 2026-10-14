# 04_IMPLEMENTATION_TESTING/CI-CD-evidence

GitHub Actions pipeline run logs and screenshots (Project Plan E.5: CI evidence).

The pipeline is defined in `.github/workflows/ci.yml` at the repository root. It runs on every push to
`main` and on every pull request targeting `main`, and performs four checks against
`G15/04_IMPLEMENTATION_TESTING/source-code`:

1. install Python 3.12 and the pinned requirements
2. `python manage.py check`
3. `python manage.py makemigrations --check --dry-run` — fails if a model changed without a migration
4. `pytest` with coverage, uploaded as a build artifact

## Evidence

| File | Shows |
| --- | --- |
| `ci-runs.png` | All workflow runs passing, on pull requests and on `main`. |
| `branch-protection.png` | `main` protection: pull request required, 1 approval, `test` status check required, branches must be up to date. |
| `milestone-dry-run.png` | Dry run milestone closed at 100% — TASK-01, TASK-02 and TASK-03 complete. |

## Dry run summary (12–16 October 2026)

| Issue | Pull request | Outcome |
| --- | --- | --- |
| #1 TASK-01 — project setup | #41 | Merged after review; four missing SRS Appendix B fields were found and added before merge. |
| #2 TASK-02 — CI pipeline and branch protection | #43 | Merged after review; pipeline green. |
| #40 TASK-03 — sample CSV files | #42 | Merged after review; a leading blank line that broke CSV parsing was found and fixed before merge. |

Deviations from the planned process are recorded in `G15/DEVIATIONS.md`.
