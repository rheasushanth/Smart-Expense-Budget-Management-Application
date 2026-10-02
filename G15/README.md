# G15 – Smart Expense & Budget Management Application

Software Engineering course project, Group G-15.

A single-user personal finance web application (Python/Django). Users record expenses and income, organise them by category, set budgets with threshold alerts, import transactions from CSV files, set up recurring transactions and view reports and dashboards. An administrator manages the category list. Linking a sandbox (test) bank is an optional stretch feature.

## Team

| Member | SRN | Owned feature | Secondary responsibility |
| --- | --- | --- | --- |
| Rhea Sushanth | PES1UG24CS371 | Budget setting, alerts and reporting/analytics | CI/CD pipeline |
| Sarthki Vachhani | PES1UG24CS422 | User authentication and profile management | UI/UX, testing |
| Sai Manogna BV | PES1UG24CS399 | Expense/income transaction management | API design review |

## Repository structure

```
G15/
├── 01_SYNOPSIS/
│   └── G15_Synopsis.pdf
├── 02_REQUIREMENTS/
│   ├── G15_SRS.pdf
│   ├── G15_ValidationSpec_v1.pdf
│   └── G15_ProjectPlan.pdf
├── 03_DESIGN/
│   ├── G15_Architecture.pdf
│   ├── G15_SWDesign.pdf
│   └── G15_ValidationSpec_v2.pdf
├── 04_IMPLEMENTATION_TESTING/
│   ├── source-code/
│   ├── CI-CD-evidence/
│   └── security-validation/
├── 05_FINAL_REPORT/
│   └── screenshots/
├── 06_PRESENTATION/
└── README.md
```

## Deliverables and status

| Phase | File | Contents | Status |
| --- | --- | --- | --- |
| 1. Synopsis | `01_SYNOPSIS/G15_Synopsis.pdf` | Project proposal, team and ownership (Deliverable 1) | Submitted |
| 2. Requirements | `02_REQUIREMENTS/G15_SRS.pdf` | Software Requirements Specification v1.2 (IEEE 830): 24 FRs, 7 NFRs, 6 security requirements, 11 use cases, RTM | Final |
| 2. Requirements | `02_REQUIREMENTS/G15_ValidationSpec_v1.pdf` | Initial validation planning: techniques and plan by requirement category | Final |
| 2. Requirements | `02_REQUIREMENTS/G15_ProjectPlan.pdf` | Lifecycle, reuse vs build, WBS, Gantt chart, tool stack | Final |
| 3. Design | `03_DESIGN/G15_Architecture.pdf` | Software Architecture Specification v1.1 (IEEE 1016): goals, components, pattern, technology stack, risks, traceability, security architecture | Final |
| 3. Design | `03_DESIGN/G15_SWDesign.pdf` | Software Design: sequence diagrams, API design, error handling, UX, key classes, deployment and data view | Final |
| 3. Design | `03_DESIGN/G15_ValidationSpec_v2.pdf` | Test Plan v1.1 (IEEE 829): 37 traceable test cases | Final |
| 4. Implementation & testing | `04_IMPLEMENTATION_TESTING/` | Source code, test cases, unit test and coverage reports, CI/CD evidence, security validation, ValidationSpec_v3 | To be added |
| 5. Final report | `05_FINAL_REPORT/` | Final report, validation report, maintenance plan, screenshots | To be added |
| 6. Presentation | `06_PRESENTATION/` | Final presentation | To be added |

## How the documents relate

- All documents use the same requirement IDs (FR-001 to FR-024, NFR-001 to NFR-007, SEC-001 to SEC-006) and use cases (UC-01 to UC-11), and each cross-references the others.
- The validation specification grows with the project: v1 is the plan (requirements phase), v2 is the Test Plan with 37 test cases (design phase), and v3 will hold the test results (implementation phase).
