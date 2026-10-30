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

## Known gaps

Accepted deliberately rather than treated as defects. Resolved rows are kept with their
closing note, so the log reads as a history rather than only a to-do list.

| Item | Detail | Status |
| --- | --- | --- |
| Coverage threshold not enforced | The CI pipeline reported coverage but did not fail below a threshold. NFR-005 requires at least 70% line coverage on the budgets, recurring and transactions apps. | **Resolved** — Sprint 2 (#31, PR #58). `ci.yml` now runs a dedicated step with `--cov-fail-under=70` scoped to those three apps. Verified to fail when the threshold is raised above actual coverage, so the gate is known to bite rather than merely to be present. Coverage at the time of closing: 97.8%. |
| Validation constraints absent | `Transaction.amount`, `Budget.limit_amount` and `RecurringRule.amount` were not constrained to be greater than zero, and `Budget.threshold_pct` not to the documented 1–100 range (SRS Appendix B.2, B.3). | **Mostly resolved** — Sprint 1. `Budget.limit_amount`, `Budget.threshold_pct` and `RecurringRule.amount` now carry model validators. `Transaction.amount` is still validated only in the entry forms, not on the model, so a direct `objects.create()` can store a non-positive amount. To be closed with FR-010/FR-011 work. |
| Seed accounts cannot authenticate | `seed_demo` calls `set_unusable_password()`, so the three demo users have no usable password. | **Open.** Registration (FR-001) now exists, so a demo account can be created through the UI, but the seeded users remain unusable for a scripted demo. |
| Sample CSV fixtures incomplete | No row exercises the "up to 2 decimal places" rule, and no row pairs a category with a mismatched transaction type (the FR-007 case). | **Open** — to be extended alongside FR-011 (#13). |
| Admin path | `templates/base.html` links to `/admin/`, whereas Project Plan E.2 places Django's built-in admin at `/django-admin/`, restricted to superusers. | **Partly resolved** — FR-020 is now served by role-protected views in the categories app (#22, PR #56), as the Project Plan requires. Django's built-in admin is still mounted at `/admin/` rather than `/django-admin/`, and `base.html` still links to it. |
| Navigation links absent | `base.html` links only to Home and Administration. Budgets, transactions, recurring rules and categories are reachable only by typing their URLs. | **Open** — the features work but the application cannot be navigated by clicking. Worth folding into the FR-018 dashboard work (#20). |
| CSV duplicate rule can drop legitimate rows | SRS Appendix B.8 matches duplicates on date, amount and note only. Two transactions that differ solely by category — a 100.00 Food expense and a 100.00 Travel expense on the same day with an empty note — collide, and the second is skipped. Verified: such an import reports `imported=1 errors=1`. | **Open, by design** — FR-011 (#13, PR #60) implements the rule as specified. Raised with the SRS owner to confirm whether category belongs in the matching key; the documented behaviour is retained until that is settled. |
