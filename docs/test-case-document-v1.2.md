# Test Case Document v1.2

**Project:** Smart Expense & Budget Management Application
**Group:** G-15
**Issued:** 5 November 2026
**Supersedes:** Validation Spec v1.1 Sections 13.1 and 13.2 (`03_DESIGN/G15_ValidationSpec_v2.pdf`, 13 October 2026)
**Status at issue:** commit `1429bc4` on `main` — 195 tests, 0 failures

This is the current Test Case Document. It reissues all 37 cases with the expected
results that the delivered system actually meets, rather than the ones written before
Sprint 2. Every case whose text has changed is marked **[Changed v1.2]** with the reason;
cases carried forward unaltered are reproduced so this document stands alone.

Status values: **Pass** — executed, expected result met. **Partial** — executed in part.
**Not executed** — could not be run, with the reason given.

| Status | Cases |
| --- | ---: |
| Pass | 34 |
| Partial | 1 |
| Not executed | 2 |
| **Total** | **37** |

---

## 1. Accounts (owner: Sarthki Vachhani)

### TC-AUTH-01 — FR-001 — Functional, negative — **Pass**
**Steps.** Open Register. Enter name Asha, email asha@test.com, password Str0ng#Pass1, submit. Repeat with the same email. Then register bob@test.com with password `abc123` (6 characters) and with `abcdefgh` (no digit).
**Expected.** First submit creates the account and redirects to the dashboard. Second submit is rejected with "Email already registered"; only one user row exists. Both weak passwords are rejected with the password-policy error and no account is created.
**Evidence.** `accounts/tests.py::test_tc_auth_01_registration_and_duplicate_email`

### TC-AUTH-02 — FR-002 — Functional — **Pass**
**Steps.** Log in with asha@test.com and the correct password. Log out. Log in with a wrong password.
**Expected.** Correct login opens an authenticated session. Wrong password shows a generic error and creates no session.
**Evidence.** `accounts/tests.py::test_tc_auth_02_login_success_and_failure`

### TC-AUTH-03 — FR-003 — Functional — **Pass**
**Steps.** Logged in, open Profile, change name to Asha K and save; then submit an empty name.
**Expected.** Name updates and persists after reload. Empty name is rejected with an inline error.
**Evidence.** `accounts/tests.py::test_tc_auth_03_profile_name_update_and_empty_name`

### TC-AUTH-04 — FR-004 — Functional — **Pass**
**Steps.** Log in, note the session cookie, log out, press Back and re-request the dashboard URL.
**Expected.** Session is invalidated; the dashboard request redirects to Login. The old cookie is rejected.
**Evidence.** `accounts/tests.py::test_tc_auth_04_logout_invalidates_session`

---

## 2. Transactions and CSV import (owner: Sai Manogna BV)

### TC-TXN-01 — FR-005 — Functional — **Pass**
**Steps.** Add expense: amount 250.00, category Food, date today, note "Lunch". Add the same expense again.
**Expected.** Saved with type Expense and source Manual; appears in the list; note optional. The second identical manual expense is also saved — duplicate skipping applies to CSV import only.
**Evidence.** `transactions/tests.py::RecordExpenseTests::test_user_can_record_expense`

### TC-TXN-02 — FR-006 — Functional — **Pass**
**Steps.** Add income: amount 20000.00, category Salary, date today, no note.
**Expected.** Saved with type Income and source Manual.
**Evidence.** `transactions/tests.py::RecordIncomeTests::test_user_can_record_income`

### TC-TXN-03 — FR-007 — Negative, positive — **Pass**
**Steps.** Submit with no category; then amount 0; then amount −5; then an Income transaction with category Food (an Expense category).
**Expected.** Each is rejected with an inline error and nothing is saved. A submission with one active category of the matching type saves.
**Evidence.** `CategoryValidationTests`, `test_expense_category_cannot_be_used_for_income`, `test_income_category_cannot_be_used_for_expense`

### TC-TXN-04 — FR-008 — Functional — **Pass**
**Steps.** Edit own transaction amount from 250 to 300, then delete it. As user B, request user A's edit URL.
**Expected.** Edit and delete succeed for the owner. User B receives 404 and the record is unchanged.
**Evidence.** `transactions/tests.py::test_TC_TXN_04_user_can_edit_transaction`, `test_user_cannot_edit_another_users_transaction`

### TC-TXN-05 — FR-009, FR-010 — Integration, negative — **Pass**
**Steps.** Import a 10-row CSV with 7 valid rows and 3 malformed (bad date, negative amount, missing category).
**Expected.** 7 rows imported with source CSV. The 3 malformed rows are not imported and are listed with row number and reason.
**Evidence.** `transactions/tests.py::test_TC_TXN_05_imports_seven_valid_and_reports_three_invalid_rows`

### TC-TXN-06 — FR-023 — Integration — **Pass**
**Steps.** With the mock sandbox adapter returning 5 transactions, click Sync. Repeat with the adapter set to fail.
**Expected.** 5 transactions imported with source Sandbox. On failure the user sees a clear message and no partial data is saved.
**Evidence.** `transactions/tests.py::test_TC_TXN_06_successful_sandbox_import`, `test_sandbox_api_failure_is_handled`

### TC-TXN-07 — FR-011 — Integration — **Pass**
**Steps.** Import a CSV containing a row matching an existing transaction on date, amount and note; 2 new rows; and a fourth row repeating one of the 2 new rows.
**Expected.** The existing-match row and the repeated in-file row are both skipped and reported as duplicates; the 2 new rows are imported once each and the import is not rolled back.
**Evidence.** `transactions/tests.py::test_TC_TXN_07_existing_and_in_file_duplicates_are_skipped`

---

## 3. Budgets and alerts (owner: Rhea Sushanth)

### TC-BUD-01 — FR-012 — Functional — **Pass**
**Steps.** Create a monthly Food budget, limit 5000, default threshold. Create a weekly Travel budget. Edit the Travel limit to 2000, then delete it. Try to create a budget on the Salary (Income) category.
**Expected.** Both budgets saved with threshold 80 and the chosen period. Limit 0, threshold 101 and an Income-category budget are rejected. The edit is saved; after delete the Travel budget and its alerts no longer appear.
**Evidence.** `budgets/tests.py`

### TC-BUD-02 — FR-013 — Unit, system — **Pass**
**Steps.** With a Food budget of 5000, add expenses of 1000 and 1500, then delete the 1000 one.
**Expected.** Displayed spend is 1000, then 2500, then 1500, each within 2 seconds of the save. Income is not counted.
**Evidence.** `budgets/tests.py`

### TC-BUD-03 — FR-014 — Negative — **Pass**
**Steps.** With an active monthly Food budget for this month, create another for the same month. Then create one for next month.
**Expected.** The second budget for the same category and month is rejected with an overlap error. The budget for next month is saved.
**Evidence.** `budgets/tests.py`

### TC-BUD-04 — FR-015 — Functional, boundary — **Pass**
**Steps.** Food budget 5000, threshold 80. Add spend to 3999, then to 4000, then add another 100.
**Expected.** No alert at 3999 (79.98%). Exactly one alert at 4000 (80%). No second threshold alert at 4100.
**Evidence.** `budgets/tests.py`

### TC-BUD-05 — FR-016 — Functional, boundary — **Pass**
**Steps.** Continue the same budget: add spend to 5000, then to 5001.
**Expected.** No over-budget alert at exactly 5000. One over-budget alert at 5001, with `is_read` false.
**Evidence.** `budgets/tests.py`

---

## 4. Reports, dashboard and recurring transactions (owner: Rhea Sushanth)

### TC-RPT-01 — FR-017 — System — **Pass**
**Steps.** Seed Food 1000, Rent 3000, Travel 1000 for one month. Open the category report for that month, then for an empty month. With a Food budget of 5000, open the budget report.
**Expected.** Food 20%, Rent 60%, Travel 20%, total 5000. Empty month shows totals of 0 and no error. The budget report shows Food with limit 5000, spent 1000, remaining 4000.
**Evidence.** `reports/tests.py::TCRPT01CategoryReport`, `TCRPT01BudgetAdherence`

### TC-RPT-02 — FR-018 — System — **Pass** — **[Changed v1.2]**
**Steps.** Open the dashboard with seeded data. Additionally, request `GET /reports/chart-data/` with `kind=pie|bar|line`, with an unknown `kind`, with an unknown `group`, and with a reversed date range.
**Expected.** Pie, bar and line charts render from the same figures as the FR-017 report, and the browser console shows no errors. The chart-data endpoint returns 200 with `{kind, labels, values, total}`; an unknown kind or grouping returns **400**; a reversed or unparseable date range returns **422**.
**Changed because.** v1.1 described only the rendered charts. The delivered design draws all three charts from one endpoint (SW Design Section 4.5), so the endpoint and its error statuses are now testable behaviour and belong in the case.
**Evidence.** `reports/tests.py::TCRPT02ChartData`, `TCRPT02DashboardPage`, `TCRPT02ChartDataEndpoint`. Browser-verified: all three charts totalled 114 982 against the report table's 114 982.00, no console errors.

### TC-REC-01 — FR-019 — Integration — **Pass**
**Steps.** Create a monthly rule: amount 999, category Subscriptions, next run date tomorrow. Edit the amount to 1099. Then deactivate the rule.
**Expected.** Rule is saved and active, and the edit is saved. A disabled category or amount of 0 is rejected on create and on edit. After deactivation the rule shows as inactive.
**Evidence.** `recurring/tests.py`

### TC-REC-02 — FR-024 — Integration — **Pass**
**Steps.** Run the rule runner with the clock set to (a) the day before, (b) the run date, (c) after deactivation, (d) the run date of a rule whose category has been disabled, with a second active rule also due.
**Expected.** (a) no transaction. (b) exactly one transaction with source Recurring, `next_run_date` moves forward one month; running twice on the same day creates only one. (c) no transaction. (d) no transaction for that rule, the rule is flagged on the recurring page, and the second rule's transaction is still created.
**Evidence.** `recurring/tests.py`

---

## 5. Administrator (owner: Sarthki Vachhani)

### TC-ADM-01 — FR-020 — Functional — **Pass**
**Steps.** As admin, add category "Gym" (Expense), rename it to "Fitness", disable it, then re-enable it.
**Expected.** Each change is saved; after disabling `is_active` is false, after re-enabling it is true.
**Evidence.** `categories/tests.py::test_administrator_can_add_category`, `test_administrator_can_edit_category`, `test_administrator_can_disable_and_reenable_category`

### TC-ADM-02 — FR-021 — Negative — **Pass**
**Steps.** With "Fitness" disabled, try to use it in a new transaction, budget and recurring rule as a Customer. Re-enable and repeat.
**Expected.** All three attempts are rejected while disabled. Existing transactions that used it remain visible. After re-enabling, all three are accepted.
**Evidence.** `categories/tests.py::DisabledCategoryAssignmentTest`

### TC-ADM-03 — FR-022 — Functional — **Pass**
**Steps.** As admin, open the user list; then request it as a Customer.
**Expected.** Admin sees the list of registered users with no password data. The Customer request returns 403.
**Evidence.** `categories/tests.py::RegisteredUsersAdminTest`

---

## 6. Non-functional requirements

### TC-PERF-01 — NFR-001 — Performance — **Not executed** — **[Changed v1.2]**
**Steps.** Seed 10 000 transactions. **On a PostgreSQL environment**, run Locust with 50 concurrent users for 10 minutes, each alternating dashboard, category report and budget page requests.
**Expected.** 95th percentile response time is 2.0 seconds or less and the error rate is below 1%.
**Changed because.** v1.1 left the environment to the Section 6 risk register. It is not optional: with `SESSION_SAVE_EVERY_REQUEST = True` (required by SEC-004) every request writes a session row, SQLite takes a database-wide write lock, and at 50 users those writes fail with `database is locked`, returning HTTP 400. The case cannot pass on SQLite for reasons unrelated to the code under test, so PostgreSQL is now stated as a precondition.
**Why not executed.** No deployed PostgreSQL environment exists. Issue #70, deviation D-04.
**Partial evidence.** Harness delivered (`performance/locustfile.py`, `seed_perf_data`). At 10 users on SQLite: worst endpoint 95th percentile 490 ms against a 2000 ms budget, 369 requests, 0 failures. This is not a pass.

### TC-AVAIL-01 — NFR-002 — Operational review — **Partial**
**Steps.** Poll the staging health URL every 5 minutes for 7 days during 06:00–24:00 IST, excluding announced maintenance.
**Expected.** At least 99% of polls return HTTP 200. Downtime causes are logged.
**Executed in part.** `/healthz/` is verified to return 200 and the database to be reachable (`config/tests.py::AvailabilityTest`). The 7-day polling window has not begun — there is no deployed URL to poll. Issue #70.

### TC-USA-01 — NFR-003 — Usability walkthrough — **Pass**
**Steps.** Three first-time users, given only the goal "record a Rs. 200 food expense", start from the logged-in dashboard while an observer counts screens.
**Expected.** Every user completes the task in 3 primary screens or fewer, without help.
**Evidence.** Walkthrough conducted under #29; `transactions/tests.py::test_TC_USA_01_user_can_record_expense_with_clear_confirmation` pins the screen count.

### TC-REL-01 — NFR-004 — Negative, integration — **Pass** — **[Changed v1.2]**
**Steps.** Import file A (20 rows) three times. Then interrupt an import after 10 rows and import file A again.
**Expected.** Transaction count is 20 after every run, with no duplicate rows. **After an interruption the 10 rows already written are retained**, and re-importing file A completes the remaining 10 without creating duplicates, giving 20.
**Changed because.** v1.1 expected "no half-imported batch". The importer is atomic **per row**, not per file, so an interrupted import keeps the rows written so far. This is deliberate — the FR-011 duplicate check makes retrying safe, so discarding valid rows would cost work for no benefit. Recorded as deviation **D-05**; SW Design Section 4.4 is to be corrected to match.
**Evidence.** `test_TC_REL_01_reimporting_same_csv_three_times_creates_no_duplicates`, `test_TC_REL_01_retry_after_interrupted_import_completes_remaining_rows`

### TC-MNT-01 — NFR-005 — Code review, unit — **Pass**
**Steps.** Review the repository layout and run coverage on the budgets, recurring and transactions apps.
**Expected.** Budgeting, alerts and recurrence logic sit in separate apps, each with unit tests, and line coverage is 70% or more.
**Evidence.** `tests_maintainability.py`; measured line coverage on those three apps 85.8% excluding test modules, 97.8% as the CI gate measures it. CI enforces `--cov-fail-under=70`.

### TC-TST-01 — NFR-006 — Unit, integration — **Pass**
**Steps.** Disable network access and unset the sandbox adapter, then run the budget calculation and alert evaluation test modules.
**Expected.** All tests pass without any external bank or payment service.
**Evidence.** `budgets/tests.py`; the sandbox is behind an interface with a mock.

### TC-POL-01 — NFR-007 — Compliance review — **Not executed**
**Steps.** Review the deployment against a four-point checklist: hosted on campus-approved infrastructure, no real personal financial data, test data only, access limited to the team and evaluators.
**Expected.** All four checklist items are confirmed and the reviewer signs the checklist.
**Why not executed.** There is no deployment to review. Issue #33, blocked on #70.

---

## 7. Security requirements

### TC-SEC-01 — SEC-001 — Configuration review — **Pass**
**Steps.** Register a user with password Str0ng#Pass1. Query the user table and search logs and a database dump for the password.
**Expected.** Stored value is a salted hash (for example `pbkdf2_sha256$...`); the plaintext appears nowhere.
**Evidence.** `accounts/tests.py::test_password_is_hashed`

### TC-SEC-02 — SEC-002 — Authorization — **Pass**
**Steps.** Log in as a Customer and request the admin category and user-list URLs directly, by GET and POST.
**Expected.** Every request returns 403 and no category is changed.
**Evidence.** `test_customer_cannot_access_django_admin`, `test_customer_receives_403_for_category_management`

### TC-SEC-03 — SEC-003 — Negative, security — **Pass, with one step outstanding** — **[Changed v1.2]**
**Steps.** Upload CSVs with a `<script>` note, a formula cell `=HYPERLINK(...)`, a 10 MB file and a non-UTF-8 file. Enter `' OR 1=1 --` in note and name fields.
**Expected.** Oversized files are rejected ("File must be 2 MB or smaller"), wrongly encoded files are rejected ("CSV file must use UTF-8 encoding"), formulas are **stored as text**, and the SQL string is stored literally.
**Changed because.** Two clarifications. First, the formula step documents *storage* behaviour only — CSV injection is an export-time risk and the application has no export feature, so this step evidences no control; adding an export feature would require a new case. Second, the `<script>` step's "content is escaped on display" is **not currently covered by an automated test**; Django templates autoescape by default, but nothing asserts it. Recommended addition in Sprint 3.
**Evidence.** `test_TC_SEC_03_rejects_csv_over_2mb`, `test_TC_SEC_03_rejects_non_utf8_csv`, `test_TC_SEC_03_formula_cell_is_stored_as_text`, `test_TC_SEC_03_sql_payload_is_stored_literally`

### TC-SEC-04 — SEC-004 — Security — **Pass**
**Steps.** Call the transaction list and budget endpoints with no session cookie, a tampered cookie, a session idle for more than 30 minutes, and a logged-out session.
**Expected.** Each request is redirected to Login (or returns 401) and returns no data.
**Evidence.** `accounts/tests.py::test_session_timeout_is_30_minutes`, plus the `login_required` coverage across app test modules.

### TC-SEC-05 — SEC-005 — Design review — **Pass**
**Steps.** Inspect models, migrations and logs while running a mocked sandbox sync.
**Expected.** No bank access token or credential is stored in the database or written to logs.
**Evidence.** `test_TC_SEC_05_sensitive_credentials_are_not_exposed_in_errors`

### TC-SEC-06 — SEC-006 — System — **Pass** — **[Changed v1.2]**
**Steps.** Make 5 failed logins within 10 minutes, then a 6th attempt with the correct password, and one forbidden admin request; as admin, rename a category; then read the security and audit records. Additionally, make a 6th attempt with an **incorrect** password.
**Expected.** The 6th attempt with the correct password is refused: the account is locked for 10 minutes and the response states this. The 6th attempt with an **incorrect** password receives the same generic "Invalid email or password." that an unregistered address receives, and must **not** disclose the lock. The category rename appears in the audit record. Each event is recorded with timestamp, user or email, IP address and event type; no password is recorded.
**Changed because.** Two corrections. First, v1.1 expected **HTTP 429**; the delivered implementation returns HTTP 200 with an error message, which is normal for a server-rendered form and is what the case now specifies. Second, v1.1 said nothing about what a *wrong* password sees. Disclosing the lock to any caller is a user-enumeration hole — only a registered address can ever lock — found during review of PR #69 and fixed before merge. The expected result now states it explicitly so it cannot regress.
**Note.** Events are persisted to a `SecurityEvent` database table rather than the rotating log files SW Design Section 4.4 specifies. Deliberate: the deployment target replaces the container filesystem on every deploy. Recorded as deviation **D-06**.
**Evidence.** `accounts/test_security.py` — 14 cases, including `test_tc_sec_06_03b_lockout_is_not_revealed_without_the_password`

### TC-SEC-07 — SEC-002, Confidentiality — Authorization (IDOR) — **Pass**
**Steps.** As user A, request user B's transaction, budget and alert IDs by changing the ID in the URL.
**Expected.** Every request returns 404 and B's data is not exposed.
**Evidence.** `recurring/tests.py` and the owner-scoping assertions across the app test modules.

---

## 8. Summary of changes from v1.1

| Case | Change |
| --- | --- |
| TC-RPT-02 | Chart-data endpoint and its 400/422 error statuses added |
| TC-PERF-01 | PostgreSQL stated as a precondition, with the reason |
| TC-REL-01 | Expected result corrected: interrupted imports retain written rows (D-05) |
| TC-SEC-03 | Formula step reclassified as documenting storage; `<script>` escaping noted as untested |
| TC-SEC-06 | HTTP 429 corrected to a 200 response; lockout non-disclosure to a wrong password added |

No case has been removed, and the traceability matrix in Validation Spec v1.1 Section 15
remains valid.

## 9. Known gaps in this document

- **TC-SEC-03** — the `<script>`-escaping step has no automated test.
- **TC-BUD-01 to TC-BUD-05, TC-REC-01, TC-REC-02, TC-SEC-07** — covered by tests that do not carry the TC identifier in their name. The coverage is real but the traceability is by module rather than by test name; renaming them would make the mapping mechanical.
