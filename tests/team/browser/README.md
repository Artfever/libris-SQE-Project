# Playwright circulation acceptance flows (#16)

These tests exercise the six flows in [USE_CASES.md](../USE_CASES.md).
Each use case has one main, two alternate and two exception scenarios.
The suite opens Libris in Playwright Chromium, performs the actions, and
checks the screen or the application's access message. An authenticated
read-back verifies availability and loan history after each action.

## Run locally

Have Java 21 on PATH and build the backend with `mvnw -DskipTests package`
from `backend`. See the [API guide](../api/README.md) for the wrapper
workaround if the Windows workspace path contains an apostrophe. From
the repository root, run:

```powershell
python -m pip install -r tests/team/browser/requirements.txt
python -m playwright install chromium
python -u tests/team/browser/run_circulation.py
```

The suite creates a private fixture using the local H2 launcher at port
18083. Browser contexts use the fixture sessions, and each test closes its
context. All records and credentials are disposable. An earlier browser run
used application source `770474a395d575da9792812fb0c50e7bf3972626`; the fresh
central-takeover run used source commit
`b73456450a3bb53b8050237e8384d66d0f335ff4`. See
[`central-takeover-2026-11-22.md`](../evidence/central-takeover-2026-11-22.md)
for the current result and `playwright-results.txt` for raw test output.

| Use case | Main flow | Alternate flows | Exception flows | Traceability |
| --- | --- | --- | --- | --- |
| UC-01 | Librarian issues book | Omit or explicitly supply due date | Book borrowed from a competing session while form is open, then obsolete book selection | FR-B01–FR-B06, BR-C01–BR-C03, PR-01, PR-02, PR-03 |
| UC-02 | Admin issues magazine | Omit or explicitly supply due date | Magazine becomes unavailable, then obsolete magazine selection | FR-B01–FR-B06, BR-C01–BR-C03, PR-01, PR-02, PR-03 |
| UC-03 | Librarian issues newspaper | Omit or explicitly supply due date | Newspaper becomes unavailable, then obsolete newspaper selection | FR-B01–FR-B06, BR-C01–BR-C03, PR-01, PR-02, PR-03 |
| UC-04 | Librarian returns book | Admin returns it or staff opens borrower history after return | Obsolete loan ID and student forbidden | FR-R01–FR-R06, BR-C04, PR-04, PR-05, PR-06 |
| UC-05 | Admin returns magazine | Librarian returns it or staff opens borrower history after return | Obsolete loan ID and student forbidden | FR-R01–FR-R06, BR-C04, PR-04, PR-05, PR-06 |
| UC-06 | Librarian returns newspaper | Admin returns it or student verifies own history | Repeat return from a stale screen and obsolete loan ID | FR-R01–FR-R06, BR-C04, PR-04, PR-05, PR-06 |

Obsolete-record scenarios substitute a nonexistent ID in the browser
control, then click the actual application control and assert the real
server response shown on screen. The normal UI generates IDs only for
existing records. When a student opens circulation, the interface
displays the staff-only message and hides return controls. The same
Playwright browser checks the server's 403 and unchanged persisted state
for the two student exception flows. On the student dashboard the
application displays current loans, so the UC-06 alternate checks that
the student has no active loans on screen and uses the browser session
to verify the returned row through the student history endpoint.

Codex drafted and ran the browser flows for the request to complete the
assigned issues. It inspected the UI and persisted records, fixed the
empty-screen heading match and stale row selector, and reran the suite. Under
Abdullah's 2026-11-22 central-owner takeover, all six use-case specifications
are also authored under Abdullah; no peer authorship or review is claimed. The
fresh 30-test result and attribution boundary are recorded in
[`../evidence/central-takeover-2026-11-22.md`](../evidence/central-takeover-2026-11-22.md).
