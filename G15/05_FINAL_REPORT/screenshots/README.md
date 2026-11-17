# 05_FINAL_REPORT/screenshots

Application screenshots for the final report. Capture these from the deployed
service at <https://smart-expense-pz56.onrender.com> so the address bar
evidences the deployment, and save them here.

Load a page a minute beforehand: the free instance sleeps after 15 minutes
and takes roughly 50 seconds to wake.

| Suggested file | Page | Shows |
| --- | --- | --- |
| `01-home.png` | `/` | Landing page |
| `02-register.png` | `/accounts/register/` | FR-001 |
| `03-record-expense.png` | `/transactions/expense/` | FR-005 |
| `04-transactions.png` | `/transactions/` | FR-008, and the source tag on each row |
| `05-budget-alert.png` | `/budgets/` | FR-015, FR-016 — an over-limit row and its alert |
| `06-reports.png` | `/reports/` | FR-017 — spending by category and budget adherence |
| `07-dashboard.png` | `/reports/dashboard/` | FR-018 — pie, bar and line |
| `08-csv-import.png` | `/transactions/import/` | FR-011 — a second import reporting duplicates skipped |
| `09-sandbox-sync.png` | `/transactions/sandbox-sync/` | FR-023 — a second sync reporting three skipped |
| `10-categories.png` | `/categories/` | FR-020, as an administrator |
| `11-users.png` | `/categories/users/` | FR-022 |
| `12-healthz.png` | `/healthz/` | NFR-002 |

For 05, 08 and 09, capture the state *after* the action, since the point of
each is the result rather than the form.
