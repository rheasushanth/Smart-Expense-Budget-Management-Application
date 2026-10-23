# Deviations Log

Group G-15 — Smart Expense & Budget Management Application

Records where delivered work departed from the SRS, Architecture & Design Specification, Test Plan or the
definition of done stated on an issue, together with the reason and the resolution. Referenced by the
"deviations logged" item in every issue's definition of done.

| # | Date | Scope | Deviation | Reason | Resolution |
| --- | --- | --- | --- | --- | --- |
| D-01 | 2026-10-13 | TASK-01 (#1, PR #41) | Merged without a passing CI check, although the issue's definition of done requires one. | The CI pipeline is delivered by TASK-02, and it cannot run before a Django project, `requirements.txt` and `pytest.ini` exist in the repository. Merging CI first would have produced a failing first run with nothing to test. | CI was added immediately afterwards (TASK-02, PR #43) and validated against the merged code on `main`. Run 38504249475 passed on the merge commit containing all of TASK-01. |
| D-02 | 2026-10-14 | TASK-02 (#2, PR #43) | Issue definition of done states "reviewed and merged by the repo owner", but the assignee and the repo owner are the same person. | GitHub does not permit a pull request author to approve their own pull request, so the stated rule is not satisfiable for issues assigned to the repo owner. | Reviewed and approved by Sarthki Vachhani, merged by the repo owner. The wording is to be corrected on remaining issues to "reviewed by another team member, merged by the repo owner". |
| D-03 | 2026-10-14 | Repository history | One commit message on `main` was rewritten after it had been pushed, and `main` was force-pushed. | The commit carried an unwanted co-author trailer. | `git filter-branch` removed the trailer; branch protection was lifted only for the duration of the push and re-enabled immediately. Both team members reset their local `main`. Pull requests #41 and #43 therefore reference merge-commit SHAs that are no longer on `main`; the pull requests themselves remain merged and their CI runs remain green. |

## Known gaps carried into Sprint 1

These were accepted deliberately during the dry run rather than treated as defects.

| Item | Detail | Planned resolution |
| --- | --- | --- |
| Validation constraints absent | `Transaction.amount`, `Budget.limit_amount` and `RecurringRule.amount` are not constrained to be greater than zero, and `Budget.threshold_pct` is not constrained to the documented 1–100 range (SRS Appendix B.2, B.3). | Sprint 1, alongside the budget and transaction forms. |
| Seed accounts cannot authenticate | `seed_demo` calls `set_unusable_password()`, so the three demo users have no usable password. | Sprint 1, with the authentication work (FR-001 to FR-004). |
| Coverage threshold not enforced | The CI pipeline reports coverage but does not fail below a threshold. NFR-005 requires at least 70% line coverage on the budgets, recurring and transactions apps. | Sprint 2 (#31), once those apps carry real tests. |
| Sample CSV fixtures incomplete | No row exercises the "up to 2 decimal places" rule, and no row pairs a category with a mismatched transaction type (the FR-007 case). | Sprint 2, when the CSV importer is built (FR-009 to FR-011). |
| Admin path | `templates/base.html` links to `/admin/`, whereas Project Plan E.2 places Django's built-in admin at `/django-admin/`, restricted to superusers, with FR-020 to FR-022 delivered by team-built views in the categories app. | Sprint 2, with the admin and category management work. |
### Temporary Login URL

| Temporary login URL | `LOGIN_URL = "/admin/login/"` redirects unauthenticated users to Django's admin login, which is not suitable for regular Customer-role users. | Update `LOGIN_URL` to the customer login route when FR-002 authentication is implemented. |