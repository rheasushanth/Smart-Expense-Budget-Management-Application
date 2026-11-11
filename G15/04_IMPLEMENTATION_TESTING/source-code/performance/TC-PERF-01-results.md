# TC-PERF-01 — measured results

**Date:** 11 November 2026
**Environment:** Render, Singapore. Web service free plan (0.1 CPU, 512 MB),
PostgreSQL 18 free plan, same region.
**Dataset:** 10,000 transactions seeded with `seed_perf_data`.
**Commit:** `b17b6d5` (runs 2 and 3), `43de3fa` (run 1).
**Harness:** `locust -f performance/locustfile.py --users 50 --run-time 10m --headless`.

## Outcome

**NFR-001 is met on response time and not met on error rate.**

| Criterion | Requirement | Measured | Result |
| --- | --- | --- | --- |
| Response time | 95% of requests within 2 s | 270–600 ms at the 95th percentile | **Met** |
| Error rate | below 1% | 4.47% – 5.41% | **Not met** |

The harness exits non-zero on either criterion, so all three runs report
`TC-PERF-01 FAILED`. The failure is the error rate alone.

## Runs

| # | Start command | Spawn rate | Requests | Failures | Error rate |
| --- | --- | --- | --- | --- | --- |
| 1 | `gunicorn config.wsgi:application` | 5/s | 9,702 | 591 | 5.38% |
| 2 | `gunicorn ... --worker-class gthread --threads 8` | 5/s | 7,340 | 384 | 4.47% |
| 3 | `gunicorn ... --worker-class gthread --threads 8` | 1/s | 10,938 | 592 | 4.76% |

### 95th percentile, measured endpoints

| Endpoint | Run 1 | Run 2 | Run 3 | Budget |
| --- | --- | --- | --- | --- |
| dashboard | 390 ms | 290 ms | 500 ms | 2000 ms |
| category report | 440 ms | 340 ms | 520 ms | 2000 ms |
| budget page | 440 ms | 340 ms | 600 ms | 2000 ms |
| chart-data (bar) | 360 ms | 270 ms | 490 ms | 2000 ms |
| chart-data (line) | 400 ms | 270 ms | 440 ms | 2000 ms |
| chart-data (pie) | 420 ms | 320 ms | 510 ms | 2000 ms |

Every endpoint is inside the 2 s budget in every run, by a factor of three
or more. The query work NFR-001 depends on — the SAD v1.1 Section 5.6
indexes and the removal of the per-budget query in `budget_adherence` —
holds up at 50 users against 10,000 rows.

## What the failures are

Every failure in every run is `502 Bad Gateway`. None is a timeout, a
database error or an application exception.

They are not spread through the run. The cumulative failure count reaches
its final value early and then stops moving: in run 2 it stands at 384 from
5,404 requests through to the final 7,340, and in run 3 at 592 from 7,881
through to 10,938. **Once the users are logged in, the service serves the
remaining minutes with no failures at all.** The falling error rate across
each run is the denominator growing against a frozen numerator, not a
service recovering.

The burst coincides with login. `POST /accounts/login/` fails at 70–90% in
every run and takes 13–36 s on average, against medians of 110–150 ms for
the measured endpoints. Password hashing is PBKDF2 and deliberately CPU
expensive; fifty of them on a 0.1 CPU instance saturate it, and requests
queue until the platform proxy gives up. The `Max` column clusters at
24,000–29,000 ms in every run, which is the proxy's limit rather than
anything the application chose.

## What was tried

**Threaded workers (run 2).** Render sets `WEB_CONCURRENCY=1` from the
available CPU, and bare `gunicorn` uses sync workers, so the service handled
exactly one request at a time. Switching to `gthread` with 8 threads
improved the 95th percentile by roughly 25% and cut failures from 591 to
384. The change is retained: a service that answers one request at a time
is also an NFR-002 availability risk, since the health check competes with
user traffic for the same worker.

**Slower ramp (run 3).** Spawning users at 1/s rather than 5/s, to spread
the login hashing over 50 seconds instead of 10. This did not work: the
error rate went from 4.47% to 4.76%, and the absolute failure count rose
from 384 to 592 as failed logins were retried. The hypothesis that the
failures were an artefact of simultaneous arrival is not supported — the
cost is the hashing itself, not its concentration.

## Why it is not pursued further

The remaining gap is instance capacity, not application code. Serving 50
concurrent sessions through 0.1 CPU, where each session opens with a
deliberately slow key derivation, is the constraint. Reaching the 1% error
rate needs a larger instance, which is a paid plan; `deployment.md` already
records that the free plan is what this project runs on.

Two options remain open and are recorded rather than taken:

- Run TC-PERF-01 once on a paid instance to evidence the error-rate
  criterion, then return to the free plan.
- Reduce the PBKDF2 iteration count for the load-test user set only.
  Rejected: it would weaken SEC-006's lockout work and measure a system
  that is not the one being delivered.

This is logged as D-04 in `G15/DEVIATIONS.md`.
