# Final Report

**Project:** Smart Expense & Budget Management Application
**Group:** G-15
**Date:** 17 November 2026
**Repository:** <https://github.com/rheasushanth/Smart-Expense-Budget-Management-Application>
**Deployment:** <https://smart-expense-pz56.onrender.com>

| Member | SRN | Owned feature | Secondary |
| --- | --- | --- | --- |
| Rhea Sushanth | PES1UG24CS371 | Budgets, alerts, reporting and analytics | CI/CD pipeline |
| Sarthki Vachhani | PES1UG24CS422 | Authentication and profile management | UI/UX, testing |
| Sai Manogna BV | PES1UG24CS399 | Expense and income transactions | API design review |

---

## 1. What was built

A single-user personal finance application in Python and Django. A user
records expenses and income against categories, sets budgets with threshold
alerts, imports transactions from CSV, configures recurring rules, pulls
transactions from a sandbox bank adapter, and reads category and budget
reports with an analytics dashboard. An administrator manages the category
list and views registered users.

Twenty-four functional requirements, FR-001 to FR-024, are implemented.

## 2. Architecture

Django's MVT pattern across seven applications, each owning one area of the
domain:

| Application | Responsibility |
| --- | --- |
| `accounts` | Registration, login, profile, roles, lockout, security events |
| `transactions` | Expense and income records, CSV import, sandbox sync |
| `budgets` | Limits, spend calculation, threshold and exceeded alerts |
| `categories` | Administrator-managed category list, registered users |
| `recurring` | Rules and scheduled generation |
| `reports` | Aggregation queries, report views, chart data endpoint |
| `config` | Settings, URL root, health endpoint |

Reporting aggregation lives in `reports/queries.py` rather than in views, so
it can be unit tested without HTTP and so the NFR-001 query work has a single
home.

The database is selected at runtime. `dj_database_url.config()` reads
`DATABASE_URL`, which Render supplies from the managed PostgreSQL service;
with no such variable the same code falls back to SQLite for local
development.

### Stack

Django 5.2.18 on Python 3.12.6, PostgreSQL 18 in production and SQLite
locally, gunicorn with eight gthread workers, WhiteNoise for static files,
and Chart.js on the dashboard.

## 3. Process

Two sprints, planned on a GitHub Project board, with a third week absorbing
spill-over under Part-3.

Every change reached `main` through a pull request. `main` carries branch
protection requiring a pull request, one approving review, and a passing
`test` status check. Eighty-four pull requests were raised across the
project.

### Continuous integration

`.github/workflows/ci.yml` runs on every push and pull request against
`main`: a Django system check, a check for missing migrations,
`collectstatic`, the full test suite with coverage, and a dedicated step
enforcing `--cov-fail-under=70` over the `budgets`, `recurring` and
`transactions` applications, which is NFR-005.

## 4. Testing

| Measure | Result |
| --- | --- |
| Tests | **205 passed**, 35 subtests, 0 failures |
| Line coverage, production code | 85.7% |
| Line coverage, NFR-005 scope | **85.8%** against a 70% requirement |
| Branch coverage, production code | 72.8% |
| Branch coverage, NFR-005 scope | 73.2% |
| System validation cases | 34 passed, 3 partial, 0 failed |

Full reports are in [`../../docs/test-reports/`](../../docs/test-reports/):
unit test, system validation, code coverage and branch coverage, with
`junit.xml`, `coverage.xml` and `coverage.json` alongside them.

Branch coverage was measured for the first time during Part-3; CI previously
ran `--cov` without `--cov-branch`, so only statement coverage existed. The
pipeline now collects both.

## 5. Non-functional outcomes

**NFR-001, performance.** TC-PERF-01 ran against the PostgreSQL deployment
with 10,000 transactions and 50 concurrent users. The response-time criterion
is met: the six measured endpoints answer in 270–600 ms at the 95th
percentile against a 2,000 ms budget. The error-rate criterion is not met,
at 4.47%–5.41% against a below-1% budget. Every failure is a 502, and all
are confined to the opening login phase — the cumulative failure count
reaches its final value early and does not move again, so the service runs
the remaining minutes clean. PBKDF2 password hashing saturates the free
tier's 0.1 CPU allocation. The constraint is instance capacity, not the
reporting code. Recorded as D-04, with figures in
[`../../docs/test-reports/`](../../docs/test-reports/) and
`performance/TC-PERF-01-results.md`.

**NFR-002, availability.** A `/healthz/` endpoint returns application and
database state and is wired to Render's health check, which restarts the
service when it stops returning 200. The seven-day polling run for
TC-AVAIL-01 is outstanding.

**NFR-007, policy compliance.** Three of four checklist items pass. Access
is not restricted to the team and evaluators: the deployment is publicly
reachable and registration is open. Recorded as D-08, pending the project
guide's confirmation.

**Security.** Passwords are hashed with Django's PBKDF2 (SEC-001).
Role-based access control guards the administrator views (SEC-002). Sessions
expire after 30 minutes idle (SEC-004). Failed logins are counted and the
account locks out, with events written to a `SecurityEvent` table (SEC-006).
CSV input is validated and malformed rows reported rather than trusted
(SEC-003). Sensitive financial identifiers are kept out of the system
(SEC-005).

## 6. Deployment

Defined as a Render Blueprint in `render.yaml` at the repository root, so the
environment is reproducible from the repository rather than reconstructed by
hand: a Python web service and a PostgreSQL database, both free plan, both in
the Singapore region. `build.sh` runs `collectstatic` then `migrate` on every
deploy. `DJANGO_SECRET_KEY` is generated by the platform and never stored in
the repository.

Three defects were found and fixed while bringing it up, each by a failed
deploy: `build.sh` committed without its executable bit, the database created
in a different region from the web service so the internal hostname would not
resolve, and `DJANGO_ALLOWED_HOSTS` resolving to the internal hostname rather
than the public one, which made Django reject every request including the
health check. The procedure and the free-plan constraints are documented in
[`../../docs/deployment.md`](../../docs/deployment.md).

## 7. Deviations

Nine are recorded in [`../DEVIATIONS.md`](../DEVIATIONS.md). The substantive
ones:

| # | Summary |
| --- | --- |
| D-04 | NFR-001 met on response time, not met on error rate, on free-tier capacity |
| D-05 | CSV import is per-row atomic, not whole-file; retained deliberately, as the retry is idempotent |
| D-06 | Security logging uses a database table, not rotating files, which do not survive Render's container replacement |
| D-07 | A change was pushed to `main` bypassing review; reverted and re-merged through a pull request |
| D-08 | The deployment is public; TC-POL-01 item 4 unmet, pending the guide's confirmation |
| D-09 | Demo videos linked rather than committed, as one exceeds GitHub's 100 MB limit |

D-05 and D-06 both record that SW Design Section 4.4 is to be corrected to
match what was built. That correction has not yet been made, so the design
document still describes whole-file atomicity and rotating file loggers.

## 8. Known gaps

Carried deliberately and listed in [`../DEVIATIONS.md`](../DEVIATIONS.md).
The notable ones: `Transaction.amount` is validated in the entry forms but
not on the model, so a direct `objects.create()` can store a non-positive
amount; the seeded demo accounts have unusable passwords; Django's built-in
admin is mounted at `/admin/` rather than the `/django-admin/` the Project
Plan specifies; and the FR-011 duplicate rule matches on date, amount and
note without category, so two same-day, same-amount transactions differing
only by category collide.

## 9. Maintenance

See [`G15_MaintenancePlan.md`](G15_MaintenancePlan.md).
