# Libris circulation test completion report

This report preserves the 21–22 November completion snapshot. The
[26 November verification](RUBRIC_EVIDENCE.md) and [current release decision](RELEASE_DECISION.md)
supersede its MySQL, browser authorization, and CI status where they provide newer evidence.

**Status:** HOLD for release. **Snapshot:** 21 November 2026. **Team:**
Section B — Abdullah Adnan (24I-3020), Muhammad Shaheer (24I-3063), and Taha
Sohail (24I-3165). **Module:** circulation management. **Workflows:** borrow
and return a book, magazine, or newspaper.

The repository under test is the team fork,
[Artfever/libris-SQE-Project](https://github.com/Artfever/libris-SQE-Project).
The upstream project is [prathamkashyap/libris](https://github.com/prathamkashyap/libris),
MIT-licensed at baseline commit
`faf2bc0d28b68d4c8ff8c0ffb0fcf5bb87d42804`. This report distinguishes
upstream application tests from team-owned circulation evidence.

## Executive result

The team verified service behavior, API partitions, authorization/CSRF,
persisted state, six browser workflows, static analysis, and focused mutation
gates. Phase 4 evidence is available in `PHASE4_REPORT.md`; Phase 5 follow-up
triage and locally verified fixes for #44–#47 are in
`evidence/phase5-findings-remediation-2026-11-21.md`. On 22 November, the issue
assignee directed a central-owner takeover of the remaining #9, #23, and #25
deliverables. Abdullah consolidated the final use-case text, triage, package,
fresh test runs, and technical mock viva with Codex assistance. The original
assigned workflow pairs are credited separately in `USE_CASES.md`; Taha
confirmed that he and Shaheer completed their pairs. No peer review of the
consolidated artifacts or personal oral performance is claimed. See
`evidence/central-takeover-2026-11-22.md`. Issues #9, #23, and #25 were closed
after PR #54 merged with that ownership boundary stated in their close comments.
Release remains on HOLD because the planned concurrent MySQL borrow/return
criterion is untested. The two remaining Spring MVC advisories are assessed as
not applicable to current source paths. H2 and passive ZAP evidence do not
establish MySQL concurrency or production behavior.

## Scope and results

| Level / area | Tested evidence and result | Scope boundary |
| --- | --- | --- |
| Upstream Java baseline | At baseline, `clean verify` ran 176 tests, all passing; existing overall line coverage was 90.3%. | Upstream tests and coverage are baseline evidence, not team-authored test counts. See `evidence/baseline-2026-11-20.md`. |
| Team service unit tests | 30 focused tests passed. Scoped coverage: `BorrowRecordService` 145/146 lines (99.3%) and 45/46 branches (97.8%); `OverdueCalculator` 100% lines and branches. | Test targets are the selected circulation service and overdue utility. The broader application JaCoCo gate is separate. See `unit/README.md` and `unit/coverage.json`. |
| Mutation | PIT killed 72/72 mutants (100%); mutated classes had 99% line coverage. The CI floor is 90% for mutation score and coverage. | Focused targets only; this is not application-wide mutation coverage. See `evidence/pitest/README.md` and raw `mutations.xml`. |
| API contract/generator | 4 generator tests passed; generated-data smoke: 1 test passed. Following the error-handler change, the H2 HTTP integration suite passed 7 tests, including malformed body and return-ID errors with unchanged state. | H2, synthetic records, sequential execution. The API integration suite reports 39.604 seconds for its 7-test local run. See `api/README.md`, `evidence/api-smoke-2026-11-21.md`, and `evidence/api-integration-2026-11-21.md`. |
| Browser | 30 Playwright tests passed across the six circulation flows; the browser flow suite checks visible outcomes and persisted API state. | Chromium and local H2; no manual user study. Run and raw result are linked from PR #35. |
| Security roles/CSRF | API checks cover anonymous 401, student write denial, CSRF denial, librarian writes, administrator writes, and student own-history read. Rejections compare availability/history snapshots. Strict same-origin CSP response assertions pass; static pages use no inline script/style; the external Google Fonts stylesheet was removed. Final passive ZAP retest proxied 52 messages through a successful borrow and return, retained one returned loan, and reported three informational alerts only. | Disposable H2 and local ZAP 2.17.0 only; no production claim. Two Spring MVC OSV IDs are assessed not applicable to current source paths. See Phase 5 remediation evidence and the sanitized post-fix JSON. |
| Accessibility | Axe-core reported zero violations on borrow, modal, and return in dark and light themes; Playwright verified keyboard borrow/return, visible outcomes, and stored state. | Local H2/Chromium only; no user study. Lighthouse accessibility 90 for both flows in both themes. See `evidence/usability/`. |
| Dependency triage | OSV checked 137 resolved packages; flagged package count fell from 20 to one after upgrades, leaving two Spring MVC IDs with source-backed not-applicable decisions. | OSV is an advisory inventory, not exploit proof. See `evidence/security/osv-2026-11-21-postfix.json` and Phase 5 remediation addendum. |
| SonarQube | Ephemeral Community Build scan and configured quality gate passed in CI. Baseline metrics: 513 project cyclomatic complexity, 1.7% duplication, 4 smells, 0 bugs, 1 vulnerability, 87.7% combined coverage; `BorrowRecordService` complexity 39. | These are baseline Sonar metrics and include the whole Java project; they are not team-only coverage. See `evidence/sonarqube/README.md` and raw JSON. |
| Build / portability | PR #37 passed the existing build, JavaScript, Phase 5 Python, backup-script, Sonar, and Docker jobs, plus the new team and mutation jobs. Docker built `linux/amd64` and `linux/arm64`. | CI builds images only; it does not publish or deploy. No deployment pipeline exists in this repository. |

## Release criteria: actual versus target

| Criterion | Target from `TEST_PLAN.md` | Actual | Decision |
| --- | --- | --- | --- |
| State integrity (PR-01) | 100% of planned successful and rejected borrow/return cases read back catalogue availability and record state; no unintended rows or state changes. | Team API integration covers all three item types, the single-item decision table, success, unavailable/missing records, repeat return, role/CSRF denial, generated input partitions, and malformed input. The suite asserts complete fixture availability and history snapshots after each rejection and success. Browser flows also check persisted outcomes. | **Met for the executed local H2 suite.** Does not prove MySQL locking or production behavior. |
| Repeat/concurrency safety (PR-02/PR-04) | Duplicate and concurrent borrow/return attempts permit at most one active record and one successful transition, with state reconciled to history. | Sequential duplicate borrow/return behavior is exercised. No forced concurrent borrow/return race or MySQL lock-contention run is evidenced. | **Not met. HOLD.** Run the planned concurrent cases against disposable MySQL and retain raw results. |
| Authorization (PR-06) | Observe each planned role decision; unauthenticated and student writes and missing session/CSRF must produce no mutation. | Anonymous, student, librarian, and administrator decisions are exercised; own-history reads and denied mutation are checked. Rejected writes retain the complete state snapshot. | **Met for the role decisions in the selected API/browser cases.** Final passive ZAP scan found informational alerts only; production and cross-student-history isolation remain unverified. |

Requirement/rule traceability is maintained in `TRACEABILITY_ESTIMATE.md` and
`evidence/api-integration-2026-11-21.md`. The selected 12 functional
requirements (FR-B01–B06 and FR-R01–R06) have passing linked evidence. The
selected BR-C01–C05 decision/date rules have API and unit coverage; concurrency
coverage for BR-C03/04 remains a deviation.

## Open findings, deviations, and risk

Defects [#38](https://github.com/Artfever/libris-SQE-Project/issues/38) and
[#39](https://github.com/Artfever/libris-SQE-Project/issues/39) are medium
priority P2 input-error defects. They were reproduced on the baseline as 500
responses with no persisted state change. The code, OpenAPI contract, and
regression tests merged in [PR #41](https://github.com/Artfever/libris-SQE-Project/pull/41);
both issues are now closed. The root-cause, 5 Whys, fishbone,
corrective/preventive actions, Pareto, and weekly GQM measures are in
`evidence/defect-quality-metrics-2026-11-21.md`.
Phase 4 findings #44–#47 have separate severity, priority, reproduction basis,
triage, risk mapping, and corrective actions in GitHub. Their fixes and residuals
are documented in `evidence/phase5-findings-remediation-2026-11-21.md`.

| Risk | Score | Evidence and residual risk |
| --- | ---: | --- |
| PR-01: partial state change on borrow/return | 15 (high) | H2 read-back passed for success and rejection. Residual: no database concurrency/production proof; keep high until disposable MySQL transaction checks pass. |
| PR-02: duplicate active loan under concurrent borrow | 12 (high) | Sequential duplicate attempts are rejected; concurrent race not run. **Open, high residual.** |
| PR-03: item-type-specific selection/availability | 12 (high) | Book, magazine, newspaper, and all eight ID-presence combinations are exercised in API/service coverage. Residual: H2-only. |
| PR-04: repeat/concurrent return corrupts state | 12 (high) | Sequential repeat return preserves date/state; concurrent return not run. **Open, high residual.** |
| PR-05: invalid/missing input causes partial writes | 8 (moderate) | Missing IDs and malformed body/path cases retain state; PR #41 merged the 400 mappings and regression tests. Residual is limited to H2 versus MySQL/deployment differences. |
| PR-06: unauthorized history access or mutation | 10 (high) | Role/CSRF denies and own-history behavior passed. Final passive ZAP scan found only informational alerts; explicit cross-student-history isolation remains unverified. |
| PR-07: due-date default/explicit date | 9 (moderate) | +14-day default, explicit dates, and neighboring date order checked. Policy for past/future dates is unspecified; local-date timezone remains an operational boundary. |
| PR-08: snapshot/history retention | 8 (moderate) | Borrower snapshot and returned history read-back tested. Profile deletion/referential behavior is not exercised in this evidence set; residual medium. |
| PR-09: slow or failing circulation under staff load | 9 (moderate) | Four local H2 k6 runs at one/five users met p95 and zero-failure targets; state reconciled after each run. No MySQL or production SLO evidence. See `PHASE4_REPORT.md`. |
| PR-10: accessible circulation screens | 9 (moderate) | Keyboard task passed; axe reports zero violations in both themes and Lighthouse accessibility is 90 for borrow/return in both themes. No user study. See Phase 4 and Phase 5 evidence. |
| PR-11: vulnerable dependencies or missing browser policy | 12 (high) | Four dependency families upgraded; one package/two IDs remain with a source-backed not-applicable assessment. Final passive ZAP scan found no medium CSP or SRI alert after removing inline scripts/styles and the external font stylesheet. Residual dependency applicability risk remains. |

**Untested or incomplete:** concurrent MySQL borrow/return and production
deployment. The central takeover completed the artifacts and fresh H2/browser
verification for #9, #23, and #25 under one named owner; it does not claim peer
authorship, peer review, or any student's personal oral viva performance.
Phase 4 baseline mutation, accessibility, security, performance, and recovery
evidence is in `PHASE4_REPORT.md`; local H2 and passive ZAP evidence do not prove
production behavior.

## CI merge control and recommendation

The required-check demonstration consists of:

- Passing CI PR #37, merged by squash as `e2b89dbe63bfffecefbacbc784cc7dcf057c6d0d`.
- Deliberately red regression PR #42, kept open; its required Maven `build`
  fails because the new tests expect 400 responses before the fix. GitHub marks
  the PR `BLOCKED`.
- Corrective PR #41, whose local Java 21 `clean verify`, focused security test,
  7-case H2 integration suite, 4 generator tests, generated smoke, and fixture
  reset passed. All 8 hosted checks passed; it merged as
  `140c791bf372046797398a78ee9e06ad3893bb13`.
- Phase 5 follow-up changes for #44–#47 merged in [PR #48](https://github.com/Artfever/libris-SQE-Project/pull/48) (`33062c86281164130f2ffd7d973e26d3129d5d31`). Java 21 `clean verify` passed 210 tests and the JaCoCo gate; all 30 circulation browser tests passed; axe reported zero violations in borrow, dialog, and return across both themes; Lighthouse accessibility scored 90 in all four states. The initial post-fix ZAP scan exposed CSP `unsafe-inline` directives; the follow-up removed inline scripts/styles and its final passive scan reported three informational alerts only. Evidence is in `security/zap-passive-2026-11-21-csp-hardening.json`.
- Submission ZIP contents were corrected in [PR #49](https://github.com/Artfever/libris-SQE-Project/pull/49), merged as `2a7d783d9d9da21eafd5dd09a1444a766bf6f7c8`. After [PR #51](https://github.com/Artfever/libris-SQE-Project/pull/51) merged as `9fe7692e0b44d573bb0df401587f94c7885c08ba`, the named 45-page PDF and repository ZIP were regenerated from `main`; the PDF was rendered for visual review, and the ZIP passed integrity and content checks. Under the 22 November central takeover, the files, test runs, and technical mock viva are maintained under Abdullah's ownership; no separate member review or oral performance is claimed.
- Strict same-origin CSP hardening, the CSP-safe axe runner, and final ZAP evidence merged in [PR #50](https://github.com/Artfever/libris-SQE-Project/pull/50) as `7bbf69bdd9c8c9dc289d242d761d41d6c29d6ce3`, closing issue #46. [PR #51](https://github.com/Artfever/libris-SQE-Project/pull/51) updated the post-merge Phase 5 metrics and completion report; issue #24 is closed. The report keeps the release on HOLD for MySQL concurrency; the 22 November central-owner takeover and its authorship boundary are recorded in the linked takeover evidence.

The active main ruleset is
[SQE main branch CI](https://github.com/Artfever/libris-SQE-Project/rules/27724105).
At this snapshot it requires `build`, `javascript`, `phase5`, `backup-script`,
`docker-build`, and `sonarqube`. The new `team-tests` and `mutation` checks run
and pass on PR #37 but are **not live required contexts**: updating the ruleset
returned HTTP 404 to this account, and the permission endpoint reports write
access without admin access. Do not treat the repository file's intended
eight-context list as evidence of live enforcement. The repository owner/admin
must add `team-tests` and `mutation`; no bypass was used. CI has no deployment
job, so there is no automated deployment path to block.

**Recommendation: HOLD release.** The executed H2 state-integrity and selected
authorization criteria pass, but the high-risk concurrency criterion does not.
Hold until the owner enables both new required checks, Phase 4 evidence is
reviewed, and concurrent MySQL evidence resolves PR-02/PR-04. This hold is an
evidence-backed completion decision, not a claim of product release.

## Evidence and GitHub references

- **Raw test evidence:** baseline `evidence/baseline-2026-11-20.md`; API `evidence/api-smoke-2026-11-21.md` and `evidence/api-integration-2026-11-21.md`; team coverage `unit/README.md` and `unit/coverage.json`; PIT `evidence/pitest/README.md` and `mutations.xml`; Sonar `evidence/sonarqube/README.md` and adjacent JSON exports.
- **Browser:** `browser/playwright-results.txt`; [automation PR #35](https://github.com/Artfever/libris-SQE-Project/pull/35). **CI gates:** [PR #37](https://github.com/Artfever/libris-SQE-Project/pull/37).
