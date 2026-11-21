# Defect analyses and weekly quality measures

Snapshot date: 2026-11-21. Scope is the selected circulation write API,
circulation UI, response policy, and resolved Maven dependency set. The original
two input-error defects (#38 and #39) are joined by the four assigned Phase 4
findings (#44–#47). This remains a small, scoped sample, not a claim that all
product defects have been found. Each item links to its GitHub issue and risk;
the Phase 5 triage/fix evidence is in
`phase5-findings-remediation-2026-11-21.md`.

## Defects and root-cause analysis

### #38 — Malformed borrow JSON returns 500

- **Severity/priority/status:** Medium / P2 / confirmed; corrected and closed by PR #41 on 2026-11-21.
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

- **Severity/priority/status:** Medium / P2 / confirmed; corrected and closed by PR #41 on 2026-11-21.
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
tests and the focused `SecurityHardeningTest`; all 8 PR #41 CI checks passed,
and merge commit `140c791bf372046797398a78ee9e06ad3893bb13` closed issues #38
and #39.

## Pareto view

Category is assigned at the underlying failure mechanism level (the category
counts defects, not individual test cases).

| Category | Confirmed defects | Share | Cumulative share |
| --- | ---: | ---: | ---: |
| Input/error classification | 2 | 33.3% | 33.3% |
| Accessibility (contrast and accessible names) | 2 | 33.3% | 66.7% |
| Browser security policy | 1 | 16.7% | 83.3% |
| Dependency currency | 1 | 16.7% | 100% |
| **Total in this scoped sample** | **6** | **100%** | **100%** |

This Pareto is intentionally small and points to request-error classification
and accessibility as the two most frequent categories in the scoped sample.
It is not representative of the entire Libris backlog.

## GQM and weekly progress

| Goal / measure | Definition and source | 2026-11-21 result | Interpretation and control action |
| --- | --- | --- | --- |
| Defect density — understand confirmed defects in source scope | Confirmed tracked defects ÷ nonblank Java source lines in `backend/src/main/java` × 1,000. Count with the repository's Python standard library; blank lines are excluded and comment lines may be included. | 6 ÷ 4,060 × 1,000 = **1.48 tracked defects/KLOC** (95 Java files). | The numerator includes #38/#39 and #44–#47; the denominator is broad Java source and several findings concern CSS/configuration. This approximate screening measure is not a release-quality benchmark. Recompute with the same scope each weekly snapshot; unreported defects do not equal zero. |
| Requirements coverage — measure exercised selected FRs | Selected FRs with at least one passing linked test ÷ 12 selected FRs (FR-B01–B06 and FR-R01–R06). Sources: `TRACEABILITY_ESTIMATE.md`, the seven-case circulation integration rerun, and the Phase 5 evidence summary. | **12/12 = 100% linked/exercised** for the selected circulation API scope. | This is requirements coverage, not code coverage or full product coverage. Keep mappings current when a test or FR changes; separately report untested non-circulation and UI accessibility scope. |
| Reopen rate — monitor defect recurrence after closure | Defects reopened during the snapshot window ÷ defects closed during that window. Source: GitHub issue history for confirmed defects. | **0/6 = 0%** at the 2026-11-21 snapshot: #38, #39, and #44–#47 were closed; none was reopened. | Small denominator; not a long-term rate. Recompute each snapshot and inspect any reopened issue. |
| Weekly plan progress — control Phase 5 deliverables | Assigned Phase 5 issues #22–#25 and their linked pull-request/check status. | #22: PR #37 merged and issue closed; the live ruleset still lacks the `team-tests` and `mutation` contexts. PR #42 is deliberately open and blocked as the malformed-input regression demonstration. #23: #38/#39 closed after PR #41; #44–#47 closed after PRs #48/#50; member triage/review remains outstanding. #24: completion report and HOLD recommendation completed in merged PRs #50/#51; issue #24 is closed. #25: the named 45-page PDF and repository ZIP were regenerated from `main` after PR #51 merged as `9fe7692e0b44d573bb0df401587f94c7885c08ba`; both files open, the PDF was rendered for visual review, and the ZIP passed integrity/content checks. Member verification and personal viva evidence remain pending. | Ask the repository admin to add both contexts. Preserve PR #42 as the blocked example. Keep team-owned use cases and member verification/viva status explicit; update after member review. |

The control actions are to monitor required CI checks, preserve issue-level
triage and post-fix retest evidence, and obtain the outstanding teammate
contributions before closing the group-owned issues. No deployment pipeline
exists in this repository; CI blocks merges through branch rules and there is
no automated deploy job to block.
