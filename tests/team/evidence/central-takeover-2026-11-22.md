# Central contribution takeover and verification

**Date:** 22 November 2026  
**Owner:** Abdullah Adnan (`@Abdullah-SE-bit`, 24I-3020)  
**Source commit for the verification run:** `b73456450a3bb53b8050237e8384d66d0f335ff4`

## Ownership and attribution

At Abdullah's explicit direction, the outstanding contribution work for issues
#9, #23, and #25 is consolidated under one owner. The use cases, defect triage,
metrics, package updates, test runs, and mock viva answers in this takeover are
attributed to Abdullah with Codex assistance, as disclosed in `AI_USE.md`.
Nothing here claims that Muhammad Shaheer or Taha Sohail authored, reviewed,
tested, or rehearsed any part of the work. This supersedes the earlier planned
two-use-cases-per-member and all-member-triage allocation for this completion
run.

## Issue #9: six circulation use cases

All six cases in `USE_CASES.md` now have Abdullah as author/owner and include
actor, preconditions, main flow, two alternate flows, two exception flows,
persisted postconditions, and FR/BR/risk links. The table in
`browser/README.md` maps each case to its browser main, alternate, and exception
coverage. API integration coverage verifies item selection, availability,
history persistence, authorization, invalid requests, and date behavior.

The current 30-case Playwright run passed on the source commit above. The six
case specifications are committed by one named contributor in this takeover;
they are not represented as six individually authored teammate contributions.

## Issue #23: consolidated triage and weekly measures

| Issue | Initial severity / priority | Final status and triage | Root cause / corrective outcome | Risk and evidence |
|---|---|---|---|---|
| #38 malformed borrow JSON | Medium / P2 | Confirmed, fixed, closed | Unreadable JSON fell through to generic exception handling; structured `400 INVALID_REQUEST` and unchanged-state regression added. | PR-05; API integration remediation evidence; PR #41. |
| #39 malformed return ID | Medium / P2 | Confirmed, fixed, closed | Path conversion fell through to generic exception handling; structured `400 INVALID_ARGUMENT` and unchanged-state regression added. | PR-05; API integration remediation evidence; PR #41. |
| #44 contrast | Medium / P2 | Confirmed, fixed, closed | Theme tokens produced insufficient contrast; foreground/background tokens and controls were corrected. | PR-10; five current axe screen states have zero violations; PR #48. |
| #45 accessible names | Medium / P2 | Confirmed, fixed, closed | Redundant labels overrode visible link text; labels were removed or corrected. | PR-10; axe scans and Phase 5 remediation report; PR #48. |
| #46 CSP and external stylesheet | Medium / P2 | Confirmed, fixed, closed | No CSP and a third-party stylesheet without integrity; strict same-origin CSP and local assets now apply. | PR-11; final passive ZAP scan reported three informational alerts and no CSP/SRI medium alerts; PR #50. |
| #47 dependency advisories | High initial triage / P1 | Audited, remediated where fixed versions existed, residual applicability recorded, closed | Four dependency families were upgraded; two Spring MVC advisories were assessed as not applicable to current source paths. | PR-11; refreshed OSV inventory and dependency tree; PR #48. |

Detailed 5 Whys and fishbone analyses for #38 and #39, reproduction steps, the
Pareto, and individual retest evidence remain in
`defect-quality-metrics-2026-11-21.md` and
`phase5-findings-remediation-2026-11-21.md`. GitHub state confirms all six
defects are closed. Their issue timelines contain no reopen events in the
2026-11-15 through 2026-11-22 reporting window.

### GQM snapshot for 22 November 2026

| Measure | Result and source | Interpretation and next control |
|---|---|---|
| Defect density | 6 confirmed tracked defects / 4,060 nonblank Java lines x 1,000 = **1.48 defects/KLOC**; 95 Java files. Recounted from `backend/src/main/java`. | Scoped screening measure; accessibility and configuration findings are included in a Java-source denominator. Recount with the same scope next week. |
| Requirements coverage | **12/12 selected circulation FRs linked to passing API/browser evidence**. Fresh Java verification, seven-case H2 API integration, and 30-case browser suite passed. | This is selected circulation requirements coverage, not full product or code coverage. Keep traceability updated when requirements or flows change. |
| Reopen rate | **0/6 = 0%** over 2026-11-15 through 2026-11-22; the six tracked defects closed during the window and the GitHub timelines show no reopen event. | Small scoped denominator. Continue checking issue timelines; report N/A rather than zero if a future window has no closures. |
| Weekly control | #22 and #24 are closed; #23's triage/metrics are consolidated here; #25's package and centralized mock rehearsal are prepared. PR #42 remains the intentionally open blocked demonstration. | Keep release on HOLD until planned MySQL concurrency evidence is run. The live branch ruleset still needs an administrator to add `team-tests` and `mutation` as required contexts. |

## Issue #25: package, selected tests, and mock viva

The package is generated from the merged repository source and includes the
requirements, test plans, use cases, test results, defect analyses, completion
report, AI-use record, scripts, fixtures, CI configuration, Git history, exact
upstream baseline, setup/reset instructions, and viva rehearsal. The filenames
use the real roll numbers and section B. See the generated PDF and ZIP in
`output/pdf/` and `output/zip/` after the takeover PR merges.

### Fresh central-run verification

Environment: Windows 11, JetBrains Runtime Java 21.0.11, Maven Wrapper 3.9.11,
Python 3.14.6, and Chromium 159.0.8154.6. Circulation tests used disposable H2
data; no production system or credentials were used.

| Command | Result |
|---|---|
| From `backend`: `mvnw.cmd clean verify` | **210 tests passed**, 0 failures/errors/skips; `BUILD SUCCESS`; JaCoCo gate met. |
| `python -u tests/team/api/run_circulation_integration.py` | **7 tests passed** against fresh H2 data. |
| `python -u tests/team/browser/run_circulation.py` | **30 tests passed** across six use cases. |
| `python -u tests/team/usability/run_tasks.py after` | **2 tasks passed**; axe reported zero violations on borrow, borrow-light, borrow modal, return, and return-light; final book availability true and loan history count one. |

### Change predictions and observed evidence

| Change prompt | Predicted effect | Evidence observed |
|---|---|---|
| Let malformed borrow JSON or a nonnumeric return ID reach the generic handler again. | Security/API regression assertions should reject 500 responses and require `400 INVALID_REQUEST` or `400 INVALID_ARGUMENT`; complete fixture availability and history snapshots should remain unchanged. | The full Java suite and seven-case API integration run passed, including the corrected malformed-input paths and unchanged-state assertions. |
| Restore the previous low-contrast theme token. | Axe should report `color-contrast` on affected text/control elements in the impacted theme; task-level persisted-state assertions are independent of visual checks. | Current axe reports contain zero violations on all five tested screen states; the task flow also read back the returned loan and available book. |
| Change the default due date from 14 to 7 days. | Omitted-date default assertions should fail for affected borrow flows; explicitly supplied due dates should remain unchanged. | Current API and six-flow browser suites passed with the 14-day default and explicit-date cases. |

This is a centralized, AI-assisted technical mock rehearsal and test execution
under Abdullah's takeover instruction. It is not evidence of any student's
personal oral performance or a test run claimed by Muhammad Shaheer or Taha
Sohail. Actual human viva performance is not represented. Production behavior,
MySQL concurrency, and the release HOLD decision remain unchanged.
