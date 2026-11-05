"""TC-PERF-01 load test for NFR-001.

Each simulated user logs in once, then alternates the three pages named in
the test case: the analytics dashboard, the category report and the budget
page. NFR-001 passes when the 95th percentile response is 2.0 seconds or
less with an error rate below 1%, at 50 concurrent users for 10 minutes
against the 10,000 transactions created by seed_perf_data.

Run (see README.md in this directory for the full procedure):

    locust -f performance/locustfile.py --host http://127.0.0.1:8000 \
        --users 50 --spawn-rate 5 --run-time 10m --headless
"""

import os
import re

from locust import HttpUser, between, events, task

CSRF_PATTERN = re.compile(r'name="csrfmiddlewaretoken" value="([^"]+)"')

# Thresholds from the Validation Spec v1.1, Section 13.2.
P95_LIMIT_MS = 2000
ERROR_RATE_LIMIT = 0.01


class ReportingUser(HttpUser):
    """A customer reading their reports (UC-04)."""

    wait_time = between(1, 3)

    def on_start(self):
        """Log in once; the session cookie carries the rest of the run."""
        email = os.environ.get("PERF_EMAIL", "perf@example.com")
        password = os.environ.get("PERF_PASSWORD")
        if not password:
            raise RuntimeError(
                "Set PERF_PASSWORD to the password given to seed_perf_data."
            )

        page = self.client.get("/accounts/login/")
        match = CSRF_PATTERN.search(page.text)
        if not match:
            raise RuntimeError("No CSRF token on the login page.")

        response = self.client.post(
            "/accounts/login/",
            {
                "csrfmiddlewaretoken": match.group(1),
                "email": email,
                "password": password,
            },
            headers={"Referer": self.client.base_url + "/accounts/login/"},
        )
        if "/accounts/login/" in response.url:
            raise RuntimeError(
                "Load-test user could not log in; check PERF_PASSWORD."
            )

    @task(3)
    def dashboard(self):
        self.client.get("/reports/dashboard/", name="dashboard")

    @task(3)
    def chart_data(self):
        # The dashboard draws itself from this endpoint, so the charts are
        # only as fast as it is (FR-018).
        for kind in ("pie", "bar", "line"):
            self.client.get(
                f"/reports/chart-data/?kind={kind}",
                name=f"chart-data ({kind})",
            )

    @task(3)
    def category_report(self):
        self.client.get("/reports/", name="category report")

    @task(1)
    def budget_page(self):
        self.client.get("/budgets/", name="budget page")


# TC-PERF-01 measures "dashboard, category report and budget page
# requests". Logging in is setup each simulated user does once, and
# password hashing is deliberately slow, so counting it would report the
# cost of PBKDF2 rather than the cost of the reports.
MEASURED = (
    "dashboard",
    "chart-data (pie)",
    "chart-data (bar)",
    "chart-data (line)",
    "category report",
    "budget page",
)


@events.quitting.add_listener
def _assert_nfr_001(environment, **kwargs):
    """Fail the run, and so the command, when NFR-001 is not met.

    Locust exits 0 by default whatever the timings, which would let a
    failing TC-PERF-01 look like a pass in a CI log.
    """
    entries = [
        entry
        for entry in environment.stats.entries.values()
        if entry.name in MEASURED
    ]
    requests = sum(entry.num_requests for entry in entries)

    if not requests:
        environment.process_exit_code = 1
        print("TC-PERF-01 FAILED: no measured requests were made.")
        return

    # Percentiles do not average, so pick the worst endpoint rather than
    # letting a fast one mask a slow one.
    p95 = max(
        (entry.get_response_time_percentile(0.95) or 0) for entry in entries
    )
    failures = sum(entry.num_failures for entry in entries)
    error_rate = failures / (requests + failures) if requests else 1.0

    problems = []
    if p95 > P95_LIMIT_MS:
        problems.append(
            f"worst endpoint 95th percentile {p95} ms exceeds {P95_LIMIT_MS} ms"
        )
    if error_rate >= ERROR_RATE_LIMIT:
        problems.append(f"error rate {error_rate:.2%} is not below 1%")

    if problems:
        environment.process_exit_code = 1
        print("TC-PERF-01 FAILED: " + "; ".join(problems))
    else:
        environment.process_exit_code = 0
        print(
            f"TC-PERF-01 PASSED: worst endpoint 95th percentile {p95} ms, "
            f"error rate {error_rate:.2%}, {requests} measured requests."
        )
