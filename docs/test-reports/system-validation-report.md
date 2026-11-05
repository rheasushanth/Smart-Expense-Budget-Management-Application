# System Validation Report

**Project:** Smart Expense & Budget Management Application
**Group:** G-15
**Date:** 5 November 2026
**Commit:** `7ea5525` on `main`
**Baseline:** Validation Spec v1.1 (`03_DESIGN/G15_ValidationSpec_v2.pdf`), Sections 13.1 and 13.2
**Environment:** Python 3.12.6, Django 5.2.18, SQLite, Django test client

## Summary

| | Cases | |
| --- | ---: | --- |
| **Passed** | **34** | Executed and meeting their expected result |
| **Partially executed** | 1 | TC-AVAIL-01 |
| **Not executed** | 2 | TC-PERF-01, TC-POL-01 |
| **Total in the Validation Spec** | **37** | |
| Failed | 0 | |

**No test case fails.** The three cases not fully executed share a single cause: no
deployed PostgreSQL environment exists. This is tracked as issue #70 and recorded as
deviation D-04.

Against the exit criteria in Validation Spec Section 14:

| Criterion | Status |
| --- | --- |
| All High-priority requirements pass | **Met**, except NFR-001, whose measured run is blocked (see below) |
| At least 70% line coverage on budgets, recurring, transactions | **Met** — 91.2% |
| Zero open High or Critical security findings | **Met** — the user-enumeration finding raised in review of PR #69 was fixed before merge |
| Every failed Medium or Low case has a documented workaround | **Met** — no case fails |

## 13.1 Functional test cases

| TC | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| TC-AUTH-01 | FR-001 | Pass | `accounts/tests.py::test_tc_auth_01_registration_and_duplicate_email` |
| TC-AUTH-02 | FR-002 | Pass | `accounts/tests.py::test_tc_auth_02_login_success_and_failure` |
| TC-AUTH-03 | FR-003 | Pass | `accounts/tests.py::test_tc_auth_03_profile_name_update_and_empty_name` |
| TC-AUTH-04 | FR-004 | Pass | `accounts/tests.py::test_tc_auth_04_logout_invalidates_session` |
| TC-TXN-01 | FR-005 | Pass | `transactions/tests.py::RecordExpenseTests::test_user_can_record_expense` |
| TC-TXN-02 | FR-006 | Pass | `transactions/tests.py::RecordIncomeTests::test_user_can_record_income` |
| TC-TXN-03 | FR-007 | Pass | `test_expense_category_cannot_be_used_for_income`, `test_income_category_cannot_be_used_for_expense` |
| TC-TXN-04 | FR-008 | Pass | `transactions/tests.py::test_TC_TXN_04_user_can_edit_transaction` |
| TC-TXN-05 | FR-009, FR-010 | Pass | `test_TC_TXN_05_imports_seven_valid_and_reports_three_invalid_rows` |
| TC-TXN-06 | FR-023 | Pass | `test_TC_TXN_06_successful_sandbox_import` (mock adapter, per NFR-006) |
| TC-TXN-07 | FR-011 | Pass | `test_TC_TXN_07_existing_and_in_file_duplicates_are_skipped` |
| TC-BUD-01 | FR-012 | Pass | `budgets/tests.py` |
| TC-BUD-02 | FR-013 | Pass | `budgets/tests.py` |
| TC-BUD-03 | FR-014 | Pass | `budgets/tests.py` |
| TC-BUD-04 | FR-015 | Pass | `budgets/tests.py` |
| TC-BUD-05 | FR-016 | Pass | `budgets/tests.py` |
| TC-RPT-01 | FR-017 | Pass | `reports/tests.py::TCRPT01CategoryReport`, `TCRPT01BudgetAdherence` |
| TC-RPT-02 | FR-018 | Pass | `reports/tests.py::TCRPT02ChartData`, `TCRPT02DashboardPage`, `TCRPT02ChartDataEndpoint`. Also verified in-browser: pie, bar and line render from the same figures as the report table (all three totalled 114 982 against the table's 114 982.00) with no console errors. |
| TC-REC-01 | FR-019 | Pass | `recurring/tests.py` |
| TC-REC-02 | FR-024 | Pass | `recurring/tests.py` |
| TC-ADM-01 | FR-020 | Pass | `categories/tests.py::test_administrator_can_add_category`, `test_administrator_can_edit_category` |
| TC-ADM-02 | FR-021 | Pass | `categories/tests.py::DisabledCategoryAssignmentTest` |
| TC-ADM-03 | FR-022 | Pass | `categories/tests.py::RegisteredUsersAdminTest` |

## 13.2 Non-functional and security test cases

| TC | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| **TC-PERF-01** | NFR-001 | **Not executed** | Harness delivered — `performance/locustfile.py` and `seed_perf_data`. See below. |
| **TC-AVAIL-01** | NFR-002 | **Partially executed** | `config/tests.py::AvailabilityTest` confirms `/healthz/` returns 200 and the database is reachable. The 7-day polling window in the test case has not been run — there is no deployed URL to poll. |
| TC-USA-01 | NFR-003 | Pass | `transactions/tests.py::test_TC_USA_01_user_can_record_expense_with_clear_confirmation` |
| TC-REL-01 | NFR-004 | Pass | `test_TC_REL_01_reimporting_same_csv_three_times_creates_no_duplicates`, `test_TC_REL_01_retry_after_interrupted_import_completes_remaining_rows`. See deviation D-05 on partial-import semantics. |
| TC-MNT-01 | NFR-005 | Pass | `tests_maintainability.py` plus the CI coverage gate |
| TC-TST-01 | NFR-006 | Pass | `budgets/tests.py` — core services tested without HTTP or external APIs |
| **TC-POL-01** | NFR-007 | **Not executed** | Reviews the actual hosting and deployment setup; nothing is deployed. Issue #33. |
| TC-SEC-01 | SEC-001 | Pass | `accounts/tests.py::test_password_is_hashed` |
| TC-SEC-02 | SEC-002 | Pass | `test_customer_cannot_access_django_admin`, `test_customer_receives_403_for_category_management` |
| TC-SEC-03 | SEC-003 | Pass | Four cases: oversized upload, non-UTF-8 encoding, formula cell, SQL payload |
| TC-SEC-04 | SEC-004 | Pass | `accounts/tests.py::test_session_timeout_is_30_minutes` |
| TC-SEC-05 | SEC-005 | Pass | `test_TC_SEC_05_sensitive_credentials_are_not_exposed_in_errors` |
| TC-SEC-06 | SEC-006 | Pass | `accounts/test_security.py` — 14 cases covering failed-login logging, the 10-minute attempt window, lockout after 5 failures, counter reset, and admin category auditing |
| TC-SEC-07 | SEC-002 | Pass | `recurring/tests.py` — a user may only reach their own rules |

## TC-PERF-01 in detail

The case requires 10 000 seeded transactions, 50 concurrent users for 10 minutes, a
95th-percentile response of 2.0 s or less, and an error rate below 1%.

**What is delivered:** `performance/locustfile.py` drives the three page types the case
names and asserts both thresholds, exiting non-zero on breach so a failing run cannot be
mistaken for a pass. `python manage.py seed_perf_data` creates the dataset.

**Why it has not been measured:** `SESSION_SAVE_EVERY_REQUEST = True` — which implements
the 30-minute sliding idle timeout required by SEC-004 — writes a session row on every
request. SQLite takes a database-wide write lock, so at 50 concurrent users those writes
fail with `database is locked`, Django raises `SessionInterrupted`, and requests return
HTTP 400. The reporting code is not the limiting factor.

Validation Spec Section 6 already anticipates this: the risk register requires the load
test to run "on staging PostgreSQL with the seeded 10 000 transactions".

**Indicative measurement** — development server, SQLite, 10 000 transactions, 10 users,
60 seconds, 369 requests, 0 failures:

| Endpoint | 50th percentile | 95th percentile |
| --- | ---: | ---: |
| Dashboard | 26 ms | 130 ms |
| Chart data (pie) | 28 ms | 140 ms |
| Chart data (bar) | 25 ms | 110 ms |
| Chart data (line) | 26 ms | 160 ms |
| Category report | 30 ms | 240 ms |
| Budget page | 47 ms | 490 ms |

Worst endpoint 490 ms against a 2000 ms budget. This is evidence that the query work is
sound; it is **not** a TC-PERF-01 pass, which requires the stated load on PostgreSQL.

Two optimisations were made under NFR-001 and are covered by regression tests: the two
indexes on `Transaction` required by SAD v1.1 Section 5.6, which no migration had
previously created, and the removal of a per-budget query in `budget_adherence`.

## Open deviations affecting validation

| ID | Effect on validation |
| --- | --- |
| D-04 | TC-PERF-01 not measured; needs the PostgreSQL environment |
| D-05 | CSV import is atomic per row, not per file; TC-REL-01 asserts the per-row behaviour |
| D-06 | SEC-006 persists events to the database rather than the rotating files SW Design Section 4.4 specifies |

## Conclusion

Thirty-four of thirty-seven cases pass, none fails, and the two unexecuted cases plus the
one partial case are blocked by the same missing deployment rather than by any defect.
Every functional requirement, FR-001 to FR-024, has at least one passing test case.
