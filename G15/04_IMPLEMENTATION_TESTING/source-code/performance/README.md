# TC-PERF-01 — NFR-001 load test

**Requirement (NFR-001, SRS v1.2).** 95% of dashboard/report requests respond
within 2 seconds under 50 concurrent users with 10,000 stored transactions,
with an error rate below 1%.

**Test case (Validation Spec v1.1, Section 13.2).** Seed 10,000 transactions.
Run Locust with 50 concurrent users for 10 minutes, each alternating
dashboard, category report and budget page requests.

## Running it

1. Seed the dataset. The password is given on the command line and never
   stored in the repository:

   ```
   python manage.py seed_perf_data --password '<choose one>'
   ```

2. Serve the application. **Not** `manage.py runserver` for the official run —
   see "Which environment" below.

3. Run the load test:

   ```
   set PERF_PASSWORD=<the same password>
   locust -f performance/locustfile.py --host <base url> \
       --users 50 --spawn-rate 5 --run-time 10m --headless
   ```

The run exits non-zero when NFR-001 is not met, so it can be read by a script
or a CI job rather than by eye. It judges the six measured endpoints only;
logging in is per-user setup, and password hashing is deliberately slow, so
counting it would measure PBKDF2 rather than the reports.

## Which environment

The official run must be against **PostgreSQL**, as the risk register in
Validation Spec v1.1 Section 6 already requires ("Run the load test on staging
PostgreSQL with the seeded 10,000 transactions"). This is not a formality:

`SESSION_SAVE_EVERY_REQUEST = True` (`config/settings.py`) gives the sliding
30-minute idle timeout, which means **every request writes a row to the
session table**. SQLite takes a database-wide write lock, so at 50 concurrent
users those writes serialise and fail with `database is locked`; Django then
raises `SessionInterrupted` and returns HTTP 400. The reports are not the
bottleneck — the session write is, and only on SQLite. PostgreSQL takes a row
lock instead, so concurrent session writes do not contend.

A measured run on SQLite with the Django development server therefore cannot
pass TC-PERF-01 at 50 users, whatever the query code does.

## Indicative local results

Dev server, SQLite, 10,000 transactions, 3 Nov 2026. Indicative only — these
do not constitute the TC-PERF-01 pass, which needs 50 users for 10 minutes on
PostgreSQL.

| Endpoint | 50th | 95th |
| --- | --- | --- |
| dashboard | 26 ms | 130 ms |
| chart-data (pie) | 28 ms | 140 ms |
| chart-data (bar) | 25 ms | 110 ms |
| chart-data (line) | 26 ms | 160 ms |
| category report | 30 ms | 240 ms |
| budget page | 47 ms | 490 ms |

10 users, 60 seconds, 369 measured requests, 0 failures. Worst endpoint 95th
percentile 490 ms against a 2000 ms budget.

At 50 users on the same stack the measured endpoints return 400s from the
session-lock contention described above, not from slow reporting.

## What was changed for NFR-001

- **Indexes on `Transaction`** — `(user, date)` and `(user, category, date)`,
  required by SAD v1.1 Section 5.6 and previously never created in any
  migration. Without them every report was a full table scan.
- **`budget_adherence` no longer issues one query per budget.** Spend for all
  active budgets is fetched once and summed per budget, and the budget list is
  narrowed in SQL to periods that can still be running.
