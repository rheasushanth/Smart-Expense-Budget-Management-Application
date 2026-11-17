# Maintenance Plan

**Project:** Smart Expense & Budget Management Application
**Group:** G-15
**Date:** 17 November 2026

What it would take to keep this application running and changeable after the
project ends. Written against what is actually deployed, not an idealised
setup.

---

## 1. Immediate expiry risk

**The free PostgreSQL instance expires 30 days after creation.** It was
created on 15 November 2026, so it lapses around **15 December 2026**, taking
every account, transaction and budget with it. The web service survives; only
the data goes.

Before that date, either move to a paid database plan, or export with
`pg_dump` and re-provision. `deployment.md` records this constraint, and it
is the single most likely cause of the application appearing broken after the
project is marked.

**The web service sleeps after 15 minutes idle** and takes roughly 50 seconds
to wake. That is a free-plan characteristic, not a defect, but anyone
demonstrating the application should load a page a minute beforehand.

## 2. Routine upkeep

| Task | Cadence | Why |
| --- | --- | --- |
| Review Dependabot or equivalent dependency alerts | Monthly | Django and psycopg receive security releases |
| Run the suite against a new Django patch release before adopting it | On release | 205 tests make this cheap |
| Check `SecurityEvent` table growth | Quarterly | No retention policy exists; see below |
| Re-run TC-PERF-01 after any query change in `reports/queries.py` | On change | NFR-001 depends on those queries |
| Confirm `/healthz/` still returns `{"status": "ok", "database": "ok"}` | Weekly | It is what Render restarts the service on |

## 3. Known debt, in the order worth paying it down

**Session writes on every request.** `SESSION_SAVE_EVERY_REQUEST = True`
gives the sliding 30-minute idle timeout SEC-004 requires, but writes a
session row on every request. On SQLite this makes concurrent use fail
outright; on PostgreSQL it is merely wasteful. A cache-backed session store
would remove the write without losing the timeout.

**`SecurityEvent` has no retention policy.** Rows accumulate indefinitely,
and `role_required` writes one for every anonymous access attempt with no
rate limit, so an unauthenticated scanner can grow the table at will. Both
points are recorded against D-06. A dated purge and a rate limit are the
fix.

**`Transaction.amount` is not constrained on the model.** The entry forms
reject non-positive amounts, but `objects.create()` does not. A validator or
database constraint closes it.

**The design document describes a different system in two places.** D-05 and
D-06 both state that SW Design Section 4.4 is to be corrected — to per-row
atomicity for CSV import, and to a persisted `SecurityEvent` table rather
than rotating files. Until that edit is made, anyone reading the design
document will be misled about how the system behaves.

**The FR-011 duplicate rule omits category.** Two transactions on the same
day, for the same amount, with an empty note, differing only by category,
collide and the second is skipped. Raised with the SRS owner; the documented
behaviour is retained until settled.

## 4. Changing the system

**Adding a feature.** Branch from `main`, work, open a pull request. Branch
protection requires one approving review and a passing `test` check, and the
author cannot approve their own pull request. CI runs a system check, a
missing-migration check, `collectstatic`, the suite with coverage, and the
NFR-005 threshold over `budgets`, `recurring` and `transactions`.

**Changing the environment.** Edit `render.yaml` rather than the Render
dashboard; the blueprint is the source of truth and dashboard changes will be
overwritten. Note that `fromService ... property: host` resolves to the
*internal* hostname, which is why `settings.py` appends
`RENDER_EXTERNAL_HOSTNAME` for the public one.

**Replacing the sandbox bank.** `transactions/sandbox_adapter.py` exposes
`fetch_bank_transactions()` returning a list of dictionaries, and
`validate_bank_transaction()` checking each one. A real provider means
replacing the first function with an HTTP call; the sync service, the
duplicate protection via `SandboxTransactionImport`, and the validation all
stay as they are.

**Running recurring generation.** `python manage.py
run_recurring_transactions` generates due transactions. Nothing schedules it
on the current deployment — it would need a Render cron job or equivalent.

## 5. Operational notes

Migrations run automatically on every deploy through `build.sh`, so no manual
step is needed. Logs are visible only in the Render dashboard; there is no
`LOGGING` configuration, so with `DEBUG` off Django's console handler is
filtered out and exceptions such as `DisallowedHost` are recorded nowhere.
Adding a production logging block is the cheapest observability improvement
available and would have saved three failed deploys during setup.
