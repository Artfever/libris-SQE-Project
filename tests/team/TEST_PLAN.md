# Circulation risk-based test plan

## Purpose and scope

Verify the borrow and return workflows for books, magazines, and newspapers,
including validation, persisted availability, active/returned history, dates,
repeat requests, authentication, authorization, and CSRF. This plan covers
synthetic local data and test accounts only. It does not claim MySQL, production,
or live-deployment verification unless a separate evidence record says so.

Out of scope: catalogue CRUD, real inventory, fines, reservations, notifications,
email verification, and policy not present in current code (for example, whether
past due dates should be rejected).

## Risk approach and levels

Prioritize state corruption, repeat/concurrent requests, and access-control
failures before date and response-contract coverage. Execute test levels in
order: (1) unit tests for service decision branches, (2) API/integration tests
for validation, status, security, and persisted postconditions, (3) browser
workflow tests for user-visible results. A later phase owns test automation;
this document defines expected controls rather than claiming those controls
already ran.

Risk score = likelihood × impact, each scored 1–5. Bands: 1–4 low, 5–9
moderate, 10–16 high, 17–25 critical. Highest risks are PR-01, PR-02, and
PR-04 (scores 15, 12, and 12).

## Roles and ownership

| Role | Responsibility |
| --- | --- |
| Phase lead `@Abdullah-SE-bit` | Maintain test basis, plan, risk and traceability; integrate evidence. |
| Phase 3 lead `@TahaSohail-Goat` | Implement unit/API/OpenAPI/browser automation assigned in Phase 3. |
| Phase 4 lead `@Artfever` | Mutation, UX, security, performance, and recovery checks. |
| Reviewer | Verify requirement links, fixture isolation, reproducibility, and actual result claims. |
| Application actors | `ADMIN`/`LIBRARIAN` for borrow and return; `STUDENT` for own-history read and denied mutation. |

## Environment and test data

- Primary: local H2 profile, Java 21, Maven wrapper, application started with
  private local test credentials. H2 is in-memory and resets on app restart.
- Secondary: disposable MySQL Compose environment only when Docker is available;
  use a dedicated disposable volume and credentials. Do not touch shared or
  production volumes.
- Browser tests: local app, synthetic student and one available item of each
  type, plus records seeded through the API. Record fixture IDs and starting
  availability in sanitized evidence. Never retain passwords, cookies, or CSRF
  tokens in artifacts.
- Clock/date assertions: use a fixed clock where injectable; otherwise compare
  to the server's local date and record timezone. Do not infer UTC from
  `LocalDate.now()`.

## Schedule and exit gates

| Stage | Planned work | Exit condition |
| --- | --- | --- |
| A — Unit | service branches, exact-one-item decision, availability, repeat return, dates | All planned unit tests pass; branch gaps explained. |
| B — API | all three item types, request validation, status/error contract, security and database read-back | Every high-risk mutation has persisted pre/post assertions. |
| C — Browser | six use cases, displayed outcome and persisted postcondition | All approved use-case flows pass in local H2; failures linked to defects. |
| D — Release review | traceability, evidence, risks, residual gaps | All release criteria met or explicit hold with owner/date. |

**Entry:** clean build baseline recorded; local environment available; synthetic
fixtures reset; source revision and tool versions captured.

**Exit:** no open critical/high defect affecting circulation state or access;
all release criteria below measured; all requirements and rules mapped to
executed evidence or explicitly marked untested; failures triaged.

**Suspend:** stop state-changing runs if fixture ownership is unclear, persisted
state diverges unexpectedly, credentials may have leaked, the environment
points at non-disposable data, or the build/test environment is unstable.

**Resume:** isolate/reset only the disposable fixture, preserve failure logs
without secrets, link a defect or environment issue, confirm target/profile and
baseline again, then rerun the failed case and affected regression set.

## Measurable release criteria

1. **State integrity (PR-01):** 100% of successful and rejected borrow/return
   cases assert catalogue availability and borrow-record state after the request;
   no unexpected rows or state changes in the planned suite.
2. **Repeat/concurrency safety (PR-02/PR-04):** duplicate borrow/return and
   concurrent attempts produce at most one active record for the item and one
   successful transition; all final states reconcile with history.
3. **Authorization (PR-06):** every planned role decision has an observed
   response; student write attempts and requests without required authentication
   or CSRF protection produce no database mutation.
4. **Coverage/traceability:** every FR/BR has at least one passing test or a
   documented deviation; all high risks have an executed control before release.

## Risk register

Likelihood and impact are 1–5. Project risks are labeled `PJ`; product risks
`PR`. Owners are responsible for evidence/control completion, not presumed
defect authors.

| ID | Risk | L | I | Score | Control / test evidence | Owner |
| --- | --- | -: | -: | -: | --- | --- |
| PR-01 | Borrow partially changes item availability or creates inconsistent history. | 3 | 5 | 15 | Successful and rejected borrow read-back; transaction rollback assertions across all item types. | `@TahaSohail-Goat` |
| PR-02 | Concurrent/repeated borrow of one item creates duplicate active loans. | 3 | 4 | 12 | Race two requests against one item; assert one active record and unavailable item; verify lock behavior. | `@TahaSohail-Goat` |
| PR-03 | Item selection or availability branch behaves differently by catalogue type. | 3 | 4 | 12 | Parameterized unit/API cases for book, magazine, newspaper; zero/multiple IDs and unavailable item. | `@TahaSohail-Goat` |
| PR-04 | Repeat return or concurrent return corrupts return date or availability. | 3 | 4 | 12 | Duplicate and concurrent return; compare original return date, history count, and availability. | `@TahaSohail-Goat` |
| PR-05 | Missing student/item/record causes an unintended partial write. | 2 | 4 | 8 | Not-found API cases with database read-back. | `@TahaSohail-Goat` |
| PR-06 | Student or anonymous caller can mutate circulation or read another student's history. | 2 | 5 | 10 | Role matrix, own-history vs other-history checks, no-mutation assertions, CSRF cases. | `@Artfever` |
| PR-07 | Due-date default or explicit date is persisted incorrectly or interpreted in the wrong timezone. | 3 | 3 | 9 | Default +14 days, explicit date, boundary/day comparisons using local-date semantics. | `@TahaSohail-Goat` |
| PR-08 | Borrower snapshot or returned history is lost when the student profile changes/deletes. | 2 | 4 | 8 | Verify snapshot fields after borrow and retained history after return; inspect deletion guard. | `@Artfever` |
| PR-09 | Borrow or return becomes too slow or unexpectedly fails under concurrent staff use. | 3 | 3 | 9 | Four comparable 60-second steady-state k6 runs at 1 and 5 users; compare p95 latency and failure rate with preset targets. | `@Artfever` |
| PR-10 | Circulation screens hide errors or have barriers for keyboard and assistive-technology users. | 3 | 3 | 9 | Playwright invalid/corrected tasks, keyboard focus and submit, axe-core and Lighthouse before/after. | `@Artfever` |
| PR-11 | Vulnerable dependencies or missing browser response controls increase attack exposure. | 3 | 4 | 12 | Resolved Maven/OSV audit, passive ZAP, configuration/source review and remediation triage. | `@Artfever` |
| PJ-01 | Docker/MySQL or browser tooling unavailable delays evidence or causes unsupported claims. | 3 | 3 | 9 | H2 fallback; mark MySQL/browser evidence conditional and do not claim unrun checks. | `@Abdullah-SE-bit` |
| PJ-02 | Team ownership/review or fixture conflicts delay completion or invalidate results. | 3 | 3 | 9 | Assign owners; shared fixture reset rules; review evidence and commit ownership; record schedule variance. | `@Abdullah-SE-bit` |

## Release decision record

| Criterion | Result | Evidence | Decision |
| --- | --- | --- | --- |
| State integrity | Pending | To be linked after Phase 3 execution | Not assessed |
| Repeat/concurrency safety | Pending | To be linked after Phase 3 execution | Not assessed |
| Authorization | Pending | To be linked after Phase 3/4 execution | Not assessed |
| Requirement traceability | Planned in `TRACEABILITY_ESTIMATE.md` | Update after execution | Not assessed |

