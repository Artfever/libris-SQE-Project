# Defect analyses and weekly quality measures

Snapshot date: 2026-11-21. Scope is the selected circulation write API and its
test contract. The numbers below are from the two confirmed input-error findings
captured by the H2 API integration run; they are a small, scoped sample, not a
claim that all product defects have been found. Both defects are linked to risk
PR-05 (invalid or missing input must not cause a partial write).

## Defects and root-cause analysis

### #38 — Malformed borrow JSON returns 500

- **Severity/priority/status:** Medium / P2 / confirmed; fix submitted for review.
- **Reproduction/evidence:** On the baseline, send malformed JSON or a body value
  that Jackson cannot convert to the borrow DTO at `POST /api/borrow-records`.
  The generic advice returned `500 INTERNAL_ERROR`; the full catalogue and
  history snapshots were unchanged. See the baseline and remediation evidence in
  [the API integration report](api-integration-2026-11-21.md).
- **Root cause:** `HttpMessageNotReadableException` had no specific advice
  handler, so it reached the catch-all `Exception` handler.
- **5 Whys:** (1) Why 500? The request error was treated as an unhandled server
  failure. (2) Why unhandled? Advice had no unreadable-body handler. (3) Why was
  it missing? Existing coverage emphasized DTO Bean Validation and valid JSON
  business rules. (4) Why did those tests miss it? They did not exercise parser
  failures and coercion failures as separate input classes. (5) Why was there no
  guard against that gap? The test contract did not define the response class
  for malformed JSON. The fix defines that contract and adds regression cases.
- **Fishbone (contributing causes):** Method — no malformed-input response
  mapping; Measurement — no assertion for malformed JSON; Technology — Jackson's
  conversion exception fell through the broad handler; Test data — valid
  objects and missing-field validation were better represented than unreadable
  bodies; Process — API error response expectations were not explicit in the
  contract. Database and deployment are not causal based on this reproduction.
- **Corrective action:** Map unreadable bodies to a sanitized `400
  INVALID_REQUEST`, document it in OpenAPI, and check response plus unchanged
  state in the circulation suite.
- **Preventive action:** Keep malformed and invalid-type body cases in the API
  regression matrix; any new exception handling path must return the documented
  `ApiError` shape without parser internals.

### #39 — Malformed return ID returns 500

- **Severity/priority/status:** Medium / P2 / confirmed; fix submitted for review.
- **Reproduction/evidence:** On the baseline, POST to
  `/api/borrow-records/not-a-number/return`. Spring path conversion reached the
  generic handler and returned `500 INTERNAL_ERROR`; record history and
  availability were unchanged. See [the API integration report](api-integration-2026-11-21.md).
- **Root cause:** `MethodArgumentTypeMismatchException` had no specific advice
  handler, so numeric path conversion failures were treated as server failures.
- **5 Whys:** (1) Why 500? The route argument conversion failure fell through to
  the catch-all. (2) Why did it fall through? No type-mismatch advice handler
  existed. (3) Why was that path overlooked? Valid numeric IDs and missing
  records were tested, while a syntactically invalid path value was treated as
  the same class as a missing record. (4) Why did tests not distinguish them?
  The response contract did not specify a client-error category for failed path
  conversion. (5) Why was that contract absent? Route parameter conversion was
  not tracked as its own input partition. The fix separates invalid syntax from
  a valid but unknown ID.
- **Fishbone (contributing causes):** Method — conversion failures had no
  explicit mapping; Measurement — malformed path values were absent from
  regression assertions; Technology — Spring's conversion exception reached
  the generic handler; Test data — valid/missing IDs were covered more deeply
  than nonnumeric strings; Process — contract used a generic response note.
  Persistence and deployment are not causal based on the unchanged-state
  reproduction.
- **Corrective action:** Map type mismatches to a sanitized `400
  INVALID_ARGUMENT`, document it in OpenAPI, and assert the complete state is
  unchanged.
- **Preventive action:** Keep nonnumeric path IDs and signed 64-bit boundaries
  in the API matrix; report malformed syntax as 400 and valid unknown IDs as
  404.

The shared corrective change adds narrow handlers for the two framework
exceptions; it does not alter CSRF, authorization, service transactions, or
business-rule responses. The 2026-11-21 local rerun passed 7 HTTP integration
tests and the focused `SecurityHardeningTest`. CI and merge evidence remains in
the associated pull request and issue timelines.

## Pareto view

Category is assigned at the underlying failure mechanism level (the category
counts defects, not individual test cases).

| Category | Confirmed defects | Share | Cumulative share |
| --- | ---: | ---: | ---: |
| Input/error classification | 2 | 100% | 100% |
| **Total in this scoped sample** | **2** | **100%** | **100%** |

This Pareto is intentionally small and supports prioritizing request-error
classification in the circulation API. It is not representative of the entire
Libris backlog.

## GQM and weekly progress

| Goal / measure | Definition and source | 2026-11-21 result | Interpretation and control action |
| --- | --- | --- | --- |
| Defect density — understand confirmed defects in source scope | Confirmed tracked circulation defects ÷ nonblank Java source lines in `backend/src/main/java` × 1,000. Count with the repository's Python standard library; blank lines are excluded and comment lines may be included. | 2 ÷ 4,049 × 1,000 = **0.49 tracked defects/KLOC** (95 Java files). | Scoped tracker numerator and broad application denominator make this an approximate screening measure, not a release-quality benchmark. Recompute with the same scope each weekly snapshot; do not infer that unreported defects equal zero. |
| Requirements coverage — measure exercised selected FRs | Selected FRs with at least one passing linked test ÷ 12 selected FRs (FR-B01–B06 and FR-R01–R06). Sources: `TRACEABILITY_ESTIMATE.md`, the seven-case circulation integration rerun, and the Phase 5 evidence summary. | **12/12 = 100% linked/exercised** for the selected circulation API scope. | This is requirements coverage, not code coverage or full product coverage. Keep mappings current when a test or FR changes; separately report untested non-circulation and UI accessibility scope. |
| Reopen rate — monitor defect recurrence after closure | Defects reopened during the snapshot window ÷ defects closed during that window. Source: GitHub issue event history for #38 and #39. | **N/A (0 closed, 0 reopened)**; both confirmed findings remain open pending reviewed fix merge. | Do not report 0% with a zero denominator. After fixes merge and issues close, compare weekly reopen counts and add recurrence analysis if either reopens. |
| Weekly plan progress — control Phase 5 deliverables | Assigned Phase 5 issues #22–#25 and their linked pull-request/check status. | #22: CI additions are in PR #37; ordinary checks pass, Docker architecture build is still running. #23: #38/#39 reproduced; fix and regression evidence prepared. #24: completion/release report still to be finalized. #25: package and viva rehearsal still pending. | Keep #22 open until required checks/ruleset demonstration are verified. Keep defects open until fix merge. Finish the completion report and package only after CI and issue evidence settle. |

The control actions are to monitor the pending Docker check, merge only after
the required quality checks pass, close the two defect issues only after their
fix is merged, then refresh the weekly metrics and completion report from the
final GitHub state. No deployment pipeline exists in this repository; CI
blocks merges through branch rules and there is no automated deploy job to
block.
