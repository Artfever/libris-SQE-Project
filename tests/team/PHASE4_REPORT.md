# Phase 4 quality evidence (#17–#21)

Source baseline: `e2b89dbe63bfffecefbacbc784cc7dcf057c6d0d`; Phase 4 tested source: `55a0ce2f8598da6d61613116414c40001ea1856d` (the evidence/documentation commit). All execution used synthetic accounts and a disposable local H2 database. Java 21, Maven Wrapper 3.9.11, Python 3.12.10, k6 2.2.0, Playwright Chromium 153.0.8010.12, ZAP 2.17.0 and PIT 1.19.4 were used. Local H2 results do not establish MySQL or production behavior. The final squash-merge SHA should be recorded in the Phase 5 completion report after merge.

## Mutation and business rules (#17)

Run `backend\mvnw.cmd -q -f ../tests/team/mutation/pom.xml install`, then from `backend` run `mvnw.cmd test-compile org.pitest:pitest-maven:1.19.4:mutationCoverage` and from the repository root run `python tests/team/mutation/check_pit.py backend/target/pit-reports/mutations.xml`. CI installs the custom operator JAR before running PIT and rejects missing custom mutants or execution errors. The 90% mutation and 90% mutated-line coverage floors are justified by the two equivalent null-guard survivors and high-risk circulation state rules. The full run had 74 mutants, 72 killed, two equivalent survivors, 97.3% mutation score and 99% mutated-line coverage. The custom `SQE_EXACTLY_ONE_ITEM` (BR-C01) and `SQE_DEFAULT_DUE_DATE` (BR-C05) operators were both killed. See [the 16-survivor review](evidence/pitest/SURVIVOR_REVIEW.md), [calibration XML](evidence/pitest/calibration-mutations.xml), and [full XML](evidence/pitest/phase4-mutations.xml). The calibration suite intentionally has weak assertions; its 14 survivors are all killed by the full team suite. The two remaining equivalent survivors are documented by method and line in the review.

## Usability and accessibility (#18)

This section records the initial Phase 4 baseline. Its original open-finding
and score summaries below are historical and are superseded by the Phase 5
fixes and reruns documented in `evidence/phase5-findings-remediation-2026-11-21.md`
and `RUBRIC_EVIDENCE.md` (current verification snapshot: 2026-11-26).

Run `npm.cmd ci` in `tests/team/usability`, build the backend JAR, then run `python tests/team/usability/compare_axe.py` and `python tests/team/usability/compare_lighthouse.py` from the repository root. Both comparison scripts reproduce the pre-fix state from the recorded source baseline, restoring the current source and JAR in a `finally` block. Axe runs its full default rule set. The two Playwright tasks used the staff circulation screen: (1) submit a borrow form with no item, observe the correction message, choose an item and student, verify keyboard focus order and submit by Enter; (2) submit a stale return ID, verify the failure left state unchanged, correct the ID and return. Both confirmed the displayed result, final availability and one retained returned loan. See [task results](evidence/usability/tasks-after.json), [axe before](evidence/usability/axe-borrow-before.json), [axe after](evidence/usability/axe-borrow-after.json), and the four Lighthouse JSON files in `evidence/usability/`.

| Key workflow screen | Lighthouse accessibility before → after | Best practices | SEO | `@axe-core/playwright` violations before → after |
| --- | ---: | ---: | ---: | ---: |
| Empty borrow screen | 88 → 90 | 100 → 100 | 90 → 90 | 1 → 0 |
| Active return screen | 90 → 90 | 100 → 100 | 90 → 90 | 0 → 0 |

Overlapping issues found by Lighthouse and axe are counted once per affected
element. Phase 4 initially found three UX issues; Phase 5 fixed them and
reran both tools. The current before/after `@axe-core/playwright` comparison
is 1 to 0 on borrow, 1 to 0 in the borrow dialog, and 0 to 0 on return.
The matched dark-theme Lighthouse comparison is borrow accessibility 88 to
90 and return 90 to 90; both screens retain best-practices 100 and SEO 90.
The post-fix run also records accessibility 90, best-practices 100, and SEO
90 for borrow and return in the light theme. Full raw reports are linked from
`RUBRIC_EVIDENCE.md` under Accessibility and defensive checks.

| Finding | Affected element and user impact | Correction and current status |
| --- | --- | --- |
| UX-01, moderate | Empty-state `h3` immediately followed page `h1`; heading navigation skipped level 2 for assistive-technology users. | Changed to `h2`; current axe scan has no heading-order violation. |
| UX-02, serious | Low-contrast shell text and controls, including search shortcut, top-bar role, and issue button; reduced readability for users with low vision. | Raised and paired theme-specific text/foreground/background tokens; current axe scans report no contrast violations in tested screens/themes. |
| UX-03, serious | Brand and profile links had accessible names that replaced visible wording; voice-control users could not invoke links by their visible names. | Removed redundant overriding labels from visible links and retained a name for the icon-only profile control; current axe scans report no name mismatch. |

These three findings were closed in Phase 5; their remediation and raw
before/after evidence are recorded in
`evidence/phase5-findings-remediation-2026-11-21.md` and
`evidence/usability/axe-playwright-rubric-before.json`,
`evidence/usability/axe-playwright-rubric-after.json`, and the Lighthouse
reports in `evidence/usability/`. See the current [rubric evidence](RUBRIC_EVIDENCE.md)
for the final task run and axe results.

## Security and dependencies (#19)

Run `python tests/team/security/check_roles.py` after packaging the local H2 JAR. The seven automated decisions in [the role evidence](evidence/security-roles-2026-11-21.json) cover two roles, allowed and denied actions, observed HTTP responses, and final persisted state. `STUDENT` received 403 for borrow, return and global history; 200 for own history. `ADMIN` received 201 for borrow and 204 for return. Rejected writes left availability and history unchanged. `SecurityConfig` requires `ADMIN`/`LIBRARIAN` for circulation mutations and authorizes student own-history reads. The same source uses a CSRF cookie/header for state-changing requests. `application-prod.properties` requires explicit credentials and keeps Secure/SameSite session cookies; H2 loopback HTTP overrides Secure only for this disposable test. These verified controls address PR-06.

| Route / data | Staff (`ADMIN`/`LIBRARIAN`) | `STUDENT` | Observed Phase 4 evidence |
| --- | --- | --- | --- |
| `POST /api/borrow-records` / selected item, student, dates | Create loan and change availability | Denied | Admin 201, student 403; book/history read-back |
| `POST /api/borrow-records/{id}/return` / return date, item availability | Return active loan | Denied | Admin 204, student 403; unchanged state after denial |
| `GET /api/borrow-records` / all borrowers' history | Read | Denied | Student 403 |
| `GET /api/borrow-records/my` / caller's history | Read (route permitted) | Read own records | Student 200 before/after borrow |
| `GET /api/books/{id}` / catalog availability | Read | Read | Admin read-back in Phase 4; student route is source-backed, not separately executed here |

The source also permits `LIBRARIAN` on the staff routes; this Phase 4 matrix exercised `ADMIN` and `STUDENT`. Phase 3 browser flows exercised librarian actions separately.

The passive scan used the exact local ZAP container `ghcr.io/zaproxy/zaproxy:stable` (2.17.0) bound to `127.0.0.1:18090`, with the app and synthetic data on port 18088. Start it with `docker run -d --name sqe-phase4-zap --publish 127.0.0.1:18090:8080 ghcr.io/zaproxy/zaproxy:stable zap.sh -daemon -host 0.0.0.0 -port 8080 -config api.disablekey=true -config api.addrs.addr.name=.* -config api.addrs.addr.regex=true`; run `python tests/team/security/run_zap_passive.py`; then stop it with `docker rm -f sqe-phase4-zap`. The script proxies the borrow and return browser actions, waits for the passive queue and exports only sanitized alert fields. No active scan was invoked. [ZAP result](evidence/security/zap-passive-2026-11-21.json): 65 proxied messages, eight alerts. Four medium alerts for missing CSP on the circulation page/components share one root cause: no CSP response header for those resources. Impact: fewer browser restrictions on injected scripts; fix: add a tested CSP compatible with current modules and external fonts. One medium alert identifies the Google Fonts stylesheet without subresource integrity; root cause: externally hosted CSS without a pinned integrity value. Impact: third-party stylesheet changes are not pinned; fix: self-host/pin or apply an appropriate integrity policy. Three informational alerts (comments, session response identification, modern app detection) require no demonstrated exploit. Risk: PR-11. ZAP's passive results are observations, not proof of exploitability.

For the open-source dependency audit, from `backend` run `mvnw.cmd -q org.apache.maven.plugins:maven-dependency-plugin:3.7.1:tree -DoutputType=json -DoutputFile=../tests/team/evidence/security/dependency-tree.json`; then run `python tests/team/security/audit_maven.py tests/team/evidence/security/dependency-tree.json tests/team/evidence/security/osv-2026-11-21.json` at the root. The [resolved inventory and OSV IDs](evidence/security/osv-2026-11-21.json) record 137 checked Maven packages, including versions and scopes; 20 packages returned one or more advisory IDs, 19 in compile scope and one test-only (`assertj-core`). The most exposed families include Tomcat, Spring Web/Security and Jackson. Finding SEC-01, severity **high for triage**: the pinned Spring Boot 3.5.0 dependency set includes packages with OSV advisories. Root cause: the baseline dependencies have not been upgraded against the current advisory set. Potential impact depends on each advisory's affected path and configuration; no exploitability claim is made here. Correction: review each ID, upgrade to supported fixed versions, rerun full regression and dependency audit, and document any not-applicable advisories. Risk: PR-11. Do not treat the count of advisory IDs as a count of independently exploitable defects.

## Performance (#20)

Run `python -u tests/team/performance/run.py` after building the backend JAR. The runner starts a fresh H2 app for each of four runs, seeds the same five books, one synthetic student and five distinct librarian accounts, then executes the same `circulation.js` script at one or five simultaneous users twice. Each run holds target concurrency for 65 seconds; custom metrics begin after five seconds, leaving at least 60 seconds at target load. The build, host, fixture shape and zero-loan starting state are consistent. Both borrow and return targets were set before execution: **p95 < 1000 ms** and **0% unexpected failures**. These are conservative local-H2 feedback targets for staff state-changing operations; they are not production SLOs. Risk: PR-09, with state integrity cross-checks for PR-01/PR-04.

The table immediately below preserves the original Phase 4 run as historical
evidence. The newer, 26 November rubric rerun supersedes these figures for the
current completion decision; see `RUBRIC_EVIDENCE.md` and the raw files in
`evidence/performance/rubric-2026-11-26/`.

| Users / repeat | Borrow p95 ms | Return p95 ms | Borrow/return completed per second | Unexpected failures |
| --- | ---: | ---: | ---: | ---: |
| 1 / 1 | 27.44 | 24.55 | 11.53 each | 0% |
| 1 / 2 | 22.91 | 19.84 | 12.80 each | 0% |
| 5 / 1 | 16.67 | 14.10 | 72.01 each | 0% |
| 5 / 2 | 17.29 | 14.34 | 71.78 each | 0% |

All four runs met both targets. The lower p95 at five users is likely warm cache/JIT and scheduling variation; it should not be extrapolated to a production throughput curve. Every run ended with zero active loans, all five books available, and retained loan history. [Raw k6 summaries and output](evidence/performance/runs.json) are in `evidence/performance/`. The harness fails on zero completed operations, unexpected failures, a broken threshold or unresolved loan state.

## Controlled failure and recovery (#21)

Run `backend\mvnw.cmd test -Dtest=TeamRecoveryTest` from `backend`. `TeamRecoveryTest` starts a disposable H2 database, seeds one synthetic student/book, and injects an exception from the audit dependency during `BorrowRecordService.borrow()`. Immediately after the failure, a separate repository read confirms the book is still available and loan count is zero. The test then restores the dependency, retries the same borrow, confirms one active loan and unavailable book, returns it, and confirms one retained returned record and restored availability. This tests transactional rollback and safe recovery for PR-01/PR-04 without affecting users or persistent production data. [JUnit XML evidence](evidence/recovery/TEST-com.example.lms.team.TeamRecoveryTest.xml) records the focused run.

## Outstanding risk for Phase 5

At the Phase 4 snapshot, UX-02, UX-03, CSP/SRI and dependency-advisory findings
were still open. Phase 5 later recorded their triage, fixes and retests. H2 and
five-user results do not establish MySQL, a public deployment or higher
concurrency. Preserve this scope limit in the final report.

## Phase 5 follow-up

The findings above were assigned as #44–#47. The remediation, retest results,
dependency applicability decisions, and final scanner result are
recorded in [`evidence/phase5-findings-remediation-2026-11-21.md`](evidence/phase5-findings-remediation-2026-11-21.md).
The current source fixes the accessibility findings and adds CSP while
removing the external font stylesheet. Maven/OSV triage upgraded four affected
dependency families; two Spring MVC advisories remain recorded as not
applicable to the current source paths. ZAP 2.17.0 was rerun in passive-only
mode against a local H2 borrow/return flow. The final scan reported three
informational alerts and no CSP or SRI medium alerts; see the sanitized raw
results in `evidence/security/zap-passive-2026-11-21-csp-hardening.json`.
