# Test Case Document — Update Log

**Project:** Smart Expense & Budget Management Application
**Group:** G-15
**Baseline document:** Validation Spec v1.1 — `03_DESIGN/G15_ValidationSpec_v2.pdf`, issued 13 October 2026
**This update:** 5 November 2026, covering changes made during Sprint 2

Deliverable Part-3 item 1 requires the earlier test cases to be updated for changes
made during the sprints, and the Test Case Document updated accordingly. The baseline
document is a PDF and is owned by the team member who produces it; this log records
every change it must absorb, so the next issue of the PDF can be made from a definite
list rather than from memory.

## 1. New test cases added during Sprint 2

| TC | Requirement | Added | Why it did not exist in v1.1 |
| --- | --- | --- | --- |
| TC-SEC-03 (encoding) | SEC-003 | `test_TC_SEC_03_rejects_non_utf8_csv` | v1.1 described the 2 MB limit only; non-UTF-8 input was identified as an untested input class during review |
| TC-SEC-03 (formula cell) | SEC-003 | `test_TC_SEC_03_formula_cell_is_stored_as_text` | Documents that spreadsheet formula text is stored literally. See the caveat below. |
| TC-SEC-03 (SQL payload) | SEC-003 | `test_TC_SEC_03_sql_payload_is_stored_literally` | Confirms the ORM parameterises input |
| TC-SEC-06-03b | SEC-002, SEC-006 | `test_tc_sec_06_03b_lockout_is_not_revealed_without_the_password` | Added after review of PR #69 found that the lockout reply disclosed whether an email address is registered |
| TC-REL-01 (retry) | NFR-004 | `test_TC_REL_01_retry_after_interrupted_import_completes_remaining_rows` | v1.1 covered repeated import but not interrupted import |

## 2. Test cases whose expected result changed

**TC-SEC-06 — account lockout.** v1.1 does not state what a locked account is told. The
delivered behaviour, after the fix in PR #69, is that the lockout reason is disclosed
**only** to a caller who supplies the correct password; a wrong password receives the
same "Invalid email or password." that an unregistered address receives. The Test Case
Document should state this explicitly, because the obvious implementation — reporting
the lock to anyone who asks — is a user-enumeration hole, and a future change could
reintroduce it without an explicit expected result to check against.

**TC-REL-01 — interrupted import.** The expected result must say that rows written
before an interruption are **retained**, and that re-running the same file completes the
remainder without creating duplicates. This contradicts SW Design v1.1 Section 4.4,
which states that multi-row writes are atomic. The behaviour is deliberate and is
recorded as deviation **D-05**; Section 4.4 is to be corrected rather than the code.

**TC-RPT-02 — analytics dashboard.** v1.1 says "pie, bar and line charts render from the
same data as the report; the browser console shows no errors." The delivered design
makes this concrete: all three charts read one endpoint,
`GET /reports/chart-data/?kind=&from=&to=&group=`, which also defines error responses
(400 for an unknown kind or grouping, 422 for a reversed or unparseable date range).
The Test Case Document should name the endpoint and its error statuses, since those are
now testable behaviours.

## 3. Test cases whose verification environment changed

**TC-PERF-01.** v1.1 does not name the environment in the case itself, although Section 6
requires staging PostgreSQL. Experience has shown the environment is not optional: on
SQLite the case cannot pass at 50 concurrent users for reasons unrelated to the code
under test (see the System Validation Report). The case should state PostgreSQL as a
precondition rather than leaving it in the risk register.

**TC-AVAIL-01.** Needs a deployed health URL to poll. `/healthz/` exists and is tested
for a 200 response, but the 7-day polling window cannot begin until the application is
deployed.

## 4. Caveat to record against TC-SEC-03 (formula cell)

`test_TC_SEC_03_formula_cell_is_stored_as_text` asserts that a cell such as
`=HYPERLINK("https://example.com","click")` is stored verbatim. This confirms storage
behaviour; it does **not** demonstrate a defence against CSV injection, which is an
export-time risk. The application has no export feature, so there is currently nothing
to defend. The Test Case Document should describe this case as documenting storage
behaviour, not as evidencing a control, so that adding an export feature later is
understood to require a new case.

## 5. Numbering note

The traceability matrix in v1.1 Section 15 lists 37 test cases. No case has been removed.
The five additions above are variants within existing TC identifiers rather than new
identifiers, which keeps the matrix stable; if the next issue prefers unique identifiers
per case, TC-SEC-03 and TC-REL-01 should be split into lettered sub-cases.
