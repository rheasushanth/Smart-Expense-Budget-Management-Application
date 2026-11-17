# Sprint demo videos

Group G-15 — Smart Expense & Budget Management Application

The Part-2 deliverables ask for a one-minute Sprint 1 video and a two-minute
Sprint 2 video demonstrating a working product. Both are linked below rather
than committed; see **D-09** in [`../DEVIATIONS.md`](../DEVIATIONS.md) for why.

**Folder:** <https://drive.google.com/drive/folders/1Wje5nWRNsJx_3RsEgE2rwl8yFfdKhuvc?usp=drive_link>

Sharing is set so that anyone with the link can view, without requesting
access.

| File | Sprint | Size |
| --- | --- | --- |
| `sprint1.mp4` | Sprint 1 | 133 MB |
| `sprint2.mp4` | Sprint 2 | 71 MB |

Both were recorded against the deployed service at
`https://smart-expense-pz56.onrender.com`, so the address bar also evidences
the Render deployment rather than a local development server.

## Sprint 1 — scope demonstrated

Sprint 1 delivered FR-001 to FR-020 together with SEC-001, SEC-002 and
SEC-004. The recording covers the user-facing core of that:

- Registration and login (FR-001, FR-002)
- Recording an expense and an income (FR-005, FR-006)
- Creating a budget and the alert raised when its limit is exceeded
  (FR-012, FR-015, FR-016)
- Profile and logout (FR-003, FR-004)

## Sprint 2 — scope demonstrated

Sprint 2 delivered the reporting, integration and administrative work:

- Category spending report and budget adherence (FR-017)
- Analytics dashboard: pie, bar and line (FR-018)
- CSV import run twice over the same file, showing duplicates skipped
  (FR-009, FR-011)
- Sandbox bank sync run twice, showing the second run skip all three
  transactions (FR-023, NFR-006)
- A disabled category no longer offered when recording a transaction
  (FR-021)
- The registered users list (FR-022)
- `/healthz/` returning `{"status": "ok", "database": "ok"}` (NFR-002)

FR-024, generating recurring transactions on schedule, is not filmed: it runs
from the `run_recurring_transactions` management command rather than from a
page, so there is nothing to show in a browser.
