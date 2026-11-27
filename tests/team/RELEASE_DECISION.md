# Circulation release decision

**Product release decision: APPROVED FOR RELEASE (team-reported).** The
selected circulation criteria passed in disposable H2 and MySQL. Main commit
`29c3abc0d0b9ef45edce875429348d398c04785e` passed all nine CI jobs in
[the main-branch run](https://github.com/Artfever/libris-SQE-Project/actions/runs/45872478751),
including the required aggregate gate after a transient wrapper-download retry.
On 27 November, Taha reported that the team completed the dependency review and
the operator's backup, migration, and smoke preflight and approved release.
See the user-confirmed status recorded in `AI_USE.md`. This report does not
claim that a live production deployment was performed or independently
observed.

| Release criterion | Target defined in the test plan | Actual against target | Decision |
| --- | --- | --- | --- |
| State integrity (PR-01) | Every planned successful and rejected borrow/return case reads back availability and loan history. Zero unintended writes. | The HTTP suite compares complete snapshots for the traffic it exercises. The MySQL races and both forced 409s preserved all unrelated catalogue and history state. The controlled audit-dependency failure rolled back the write and allowed exactly one retry. | Met for the executed H2 and MySQL checks. |
| Repeat and concurrency safety (PR-02, PR-04) | A duplicate or concurrent request permits at most one active loan and one successful return. Final state reconciles with history. | MySQL 8.4.11 observed two waiters in each of six races. Each borrow had one 201 and one UNAVAILABLE. Each return had one 204 and one ALREADY_RETURNED. Forced borrow and return timeouts produced 409 before clean retries. Four final returned records matched the four successful borrows. | Met in the disposable MySQL environment. |
| Authorization (PR-06) | Every tested role decision has an observed response. Unauthorized, forbidden, and missing-CSRF writes produce zero changes. | H2 API scenarios cover anonymous, librarian, admin, student and CSRF responses. Eleven Chromium role decisions passed. Two students with concurrent active loans each saw only their own records. Denied writes preserved the snapshot. | Met on local synthetic accounts. |

Evidence: [test plan](TEST_PLAN.md),
[MySQL race report](evidence/mysql-concurrency-2026-11-26.json),
[browser access report](evidence/security/roles-playwright-2026-11-26.json),
and [recovery report](evidence/recovery/TEST-com.example.lms.team.TeamRecoveryTest.xml).
See the [current rubric and residual-risk review](RUBRIC_EVIDENCE.md) for test
scope, package readiness, and accountable follow-up.

**Decision: APPROVED FOR RELEASE per the team's 27 November confirmation.**
The team reports that dependency dispositions and deployment preflight are
complete. `scripts/check-release-ci.py` still blocks a manual release if the
exact revision lacks a successful run or any required job. Production
deployment itself is not claimed in this report.
