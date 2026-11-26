# Parts 1–5 verification record

Snapshot: 26 November 2026. Application: Libris circulation. The selected
workflows are issuing and returning books, magazines, and newspapers. A
successful issue changes catalogue availability and creates the loan that
return closes. The Section B team uses the public MIT fork and upstream
baseline `faf2bc0d28b68d4c8ff8c0ffb0fcf5bb87d42804`. Historical evidence
references the revision used for that run. The follow-up changed the test
harness, release checks, unsupported-media response, and JDBC driver.
The circulation service and database migrations are unchanged.

[Java 21 verification](evidence/java-rubric-2026-11-26.txt) recorded
210 passing tests, zero failures/errors/skips, and a passing JaCoCo gate.
[The browser rerun](evidence/browser-rubric-2026-11-26.txt) recorded
30 passing cases on the corrected build. The same build passed the
native MySQL 8.4.11 suite with Connector/J 26.10.0.

| Part | Evidence and interpretation |
| --- | --- |
| 1. System and scope | The [basis](TEST_BASIS.md) documents 12 functional requirements, five business rules, staff and student permissions, and the shared records. The [fresh seed and reset](evidence/fixture-h2-rubric-2026-11-26.json) found an empty H2 database, inserted and inspected synthetic records, and verified all five entity counts returned to zero after restart. The [registration record](evidence/registration-2026-11-20.md) and [closed issue #5](https://github.com/Artfever/libris-SQE-Project/issues/5) support the team's confirmation that Section B registration was completed. The Sheet row and timing were not independently inspected. |
| 2. Plan and functional automation | The [plan](TEST_PLAN.md) supplies the 5 × 5 matrix, three release criteria and controls. The [traceability and estimate](TRACEABILITY_ESTIMATE.md) links 12 of 12 selected requirements. The team supplied 14 person-hours of reported effort across ten areas. The estimate document compares matched areas and links the closed issues. The [Java unit evidence](unit/README.md) explains the unreachable branch and maps the feasible MCC rows and MC/DC pairs. The [API suite](api/README.md) uses the OpenAPI generator, complete state snapshots, and MySQL race and 409 evidence. The [six specifications](USE_CASES.md) each have main, two alternate, and two exception flows. [Thirty Playwright cases](browser/README.md) automate them. All six specifications have one recorded author. The brief calls for two per member, which needs new member contributions or an instructor-approved exception. |
| 2. Mutation and CI | The expanded focused PIT run killed 72 of 74 mutants (97.3%) and killed both business-rule operators. The [survivor review](evidence/pitest/SURVIVOR_REVIEW.md) distinguishes 14 killable calibration survivors and two equivalent full-suite survivors. The [red run and corrective PR](evidence/ci-gate-demonstration-2026-11-21.md) establish the existing documented blocked merge. The updated workflow puts all eight checks behind the already-required `build` context and checks actual Sonar conditions. The [release procedure](../../docs/DEPLOYMENT.md) also checks the exact successful `main` revision and image revision. Live enforcement of these new files depends on their integration and hosted execution. |
| 3. Usability and accessibility | The [task output](evidence/usability/tasks-rubric-after.json) records Tab from Item through Student, Issue date, Due date, Cancel, and finally Issue item. Enter first triggers a corrective message and leaves state unchanged, then completes the corrected issue. The return task first sees the missing-record message, then confirms the successful return. The five task scan states had zero axe violations. Historical Lighthouse reports retain the before-and-after comparison, including improved heading hierarchy, accessibility 88 to 90 on borrow, best practices 100, and SEO 90. The [Phase 4 report](PHASE4_REPORT.md) and [retest analysis](evidence/phase5-findings-remediation-2026-11-21.md) explain root cause, user impact, severity, and correction for heading order, contrast, and accessible names. |
| 4. Defensive security | The [Playwright access table](evidence/security/roles-playwright-2026-11-26.json) records 11 expected and observed HTTP decisions, session cookie flags, cross-student isolation, CSRF denials, and final state. The [passive ZAP report](evidence/security/zap-passive-rubric-2026-11-26.json) retained 48 messages observed during the two workflows and three informational alerts. The resolved Maven/OSV inventory and [triage](evidence/phase5-findings-remediation-2026-11-21.md) document component versions, impact, upgraded dependencies, and residual applicability. |
| 5. Performance and recovery | The [k6 runs](evidence/performance/rubric-2026-11-26/runs.json) used two runs at one VU and two at five VUs with the same local H2 setup, a five-second warmup, 60 seconds at target load, and separate books per VU. The [controlled recovery](evidence/recovery/TEST-com.example.lms.team.TeamRecoveryTest.xml) asserts rollback before retry and checks the final state. Same-item locking was measured separately in [the MySQL suite](evidence/mysql-concurrency-2026-11-26.json). |

## Static analysis and CI thresholds

SonarQube Community Build 26.11 and SonarScanner for Maven 5.5.0.6356
analyzed application revision `ddd2c0a526ae9bf250fa1bfd6f5ef1dc80df2464`.
The [raw measurements](evidence/sonarqube/rubric-2026-11-26/project.json)
and [gate export](evidence/sonarqube/rubric-2026-11-26/gate.json) record
coverage 87.7% against an 85% floor and duplication 1.7% against a 3%
ceiling. Both conditions were explicitly evaluated and passed. The floor
preserves most of the 87.7–87.8% combined baseline coverage while the
stricter team-unit gate separately protects circulation. A 3% duplication
ceiling allows routine variation around the 1.7% baseline and catches
substantial duplication regressions.

Project cyclomatic complexity is 518, cognitive complexity 214, and
the circulation service remains at 39 cyclomatic and 29 cognitive.
The [manual CFG](evidence/sonarqube/README.md) reconciles with the unchanged
service. There are four smells, zero bugs, 80 minutes of estimated
technical debt, and ratings A for reliability and maintainability and
B for security. Current coverage combines source lines and branches.
One [Sonar finding](evidence/sonarqube/rubric-2026-11-26/issues.json)
flags the intentionally browser-readable CSRF cookie. The browser
reads it to send the required request header. The session cookie
remains HttpOnly and the role suite independently verified that
omitting the CSRF header rejects both writes. Keep the finding recorded
and retain that split if this mechanism is revised.

The initial [hosted rerun](https://github.com/Artfever/libris-SQE-Project/actions/runs/45707342642)
ran Maven, Sonar, and mutation successfully. The team job failed before
testing because the fresh runner could not download the Maven Wrapper
distribution. The workflow now retries the distribution warmup, with
test and quality failures still propagated to the required aggregate.

## API coverage and new finding

| Input or response group | Executed evidence |
| --- | --- |
| Request body fields | Each generated body-field partition uses one changed field against a valid fixture. The suite covers omitted, null, valid values, malformed dates and wrong types. Empty and nonempty borrower name, email, and phone values do not replace the saved student's contact snapshot. |
| Boundary values | Every identifier field and the return path ID exercise the three points around both signed 64-bit limits. Exactly-one item selection covers 0, 1 and 2 and all eight presence combinations. Explicit due dates around the issue date are accepted as supplied. Unconstrained strings and dates carry no invented domain bounds. |
| Request and response contract | Borrow returns 201 with Location and a stored representation. Return returns 204 without a body. Roles, CSRF, syntax, missing records, repeated requests, unsupported method and media type, and MySQL 409s have meaningful response and state assertions. Unexpected 500 is the fallback error contract. The recovery suite deliberately injects a failure at the service and checks rollback. |
| Cross-workflow states | Missing loans cannot return. Active loans can return once and retained returned loans cannot repeat that transition. Books, magazines, and newspapers each pass borrow then return, including duplicate requests while active and after return. |

**API-03, unsupported media type (Medium / P2, PR-05, [issue #57](https://github.com/Artfever/libris-SQE-Project/issues/57)).** A normal borrow
request sent as plain text fell through the generic exception handler to
500. The dedicated Spring MVC exception now maps to 415
`UNSUPPORTED_MEDIA_TYPE` with a sanitized correction message. Otherwise
valid JSON sent with the wrong header should be corrected by the client,
and misclassification inflates the apparent server failure rate. The
regression checks the structured response and complete persisted state.
Keep empty, non-object, and wrong-media requests in the regression matrix.
The [focused baseline run](evidence/api-media-type-before.txt) records
the observed mismatch. The [corrected run](evidence/api-rubric-2026-11-26.txt)
passes all eight cases. The issue remains open pending integration of
[draft PR #56](https://github.com/Artfever/libris-SQE-Project/pull/56).

## Accessibility and defensive checks

The [pre-fix Playwright axe report](evidence/usability/axe-playwright-rubric-before.json)
overlays only the historical borrow script on the same packaged application.
The same full scanner, axe-core 4.14.1 through `@axe-core/playwright`,
found `heading-order` on the empty borrow screen and modal state. The
[fixed scan](evidence/usability/axe-playwright-rubric-after.json) found
zero violations on all three scanned states. The historic Lighthouse
comparison measures the matching heading improvement and records all three
requested categories. Both result sets distinguish severity, user impact,
and correction in the [Phase 4 report](PHASE4_REPORT.md).

One [hosted scan](evidence/usability/axe-borrow-modal-linux-animation.json)
captured the dialog while its backdrop and panel were still fading in.
At that instant axe measured some text at 1.28–1.8:1. Playwright's visible
assertion only established layout visibility. Both runners now wait for
the real form and full opacity on the panel and backdrop, then run the
same contrast rules. This controls the measurement timing without changing
the application's colors or suppressing any rules. Control: PR-10.

| Role | Action | Expected | Observed |
| --- | --- | ---: | ---: |
| Student A | Borrow book | 403 | 403 |
| Admin | Borrow without CSRF | 403 | 403 |
| Admin | Borrow book | 201 | 201 |
| Admin | Borrow magazine for student B | 201 | 201 |
| Student A | View global loan history | 403 | 403 |
| Student A | View own history with both students' loans present | 200 | 200 |
| Student B | View own history with both students' loans present | 200 | 200 |
| Student A | Return book | 403 | 403 |
| Admin | Return without CSRF | 403 | 403 |
| Admin | Return book | 204 | 204 |
| Admin | Return magazine | 204 | 204 |

All decisions use browser requests with real local session cookies.
Independent fixture read-back confirms both rejected write paths preserve
state and successful return leaves both items available. Chromium observed
HttpOnly and SameSite=Lax. The loopback fixture uses HTTP. Production Secure
configuration is source evidence, with production runtime outside this check.

### Dependency-Check applicability review

OWASP Dependency-Check 13.0.0 used the project's NVD JSON mirror and
Retire.js. The [before inventory](evidence/security/dependency-check-rubric-before.json)
has 120 analysis records and seven flagged files. The
[after inventory](evidence/security/dependency-check-rubric-after.json)
has 120 analysis records and six flagged files. Bundled JavaScript files
explain the difference between a file count and a package count. The
exports retain filenames, resolved package IDs, advisory IDs, severities,
and sources. They omit local filesystem paths and advisory narrative.

| Component | Evidence and likely impact | Correction or disposition |
| --- | --- | --- |
| MySQL Connector/J 9.7.0 | Four NVD matches on a runtime driver used by the MySQL profile. This is an actual library version match and warrants remediation under PR-11. | Follow the [vendor guidance](https://dev.mysql.com/doc/connector-j/en/) and use Connector/J 26.10.0. The same scan finds zero matches for the replacement driver. Rerun the MySQL transaction and application suites. |
| Spring Framework 6.2.19 | Seventeen CPE matches reported under `spring-core`. Reviewed feature families include reactive routes, streaming views, XSLT, template views, expression handling, and data binding. The scoped circulation routes use REST JSON DTOs and no application-level WebFlux, XSLT, SSE or expression evaluation. | Preserve the findings. Review the remaining application paths, including filter settings, error conversion and exported headers. Plan a supported framework upgrade and regression run. [Vendor fixes](https://enterprise.spring.io/projects/spring-framework/6.2.20/). |
| Spring Data JPA 3.5.13 | The reported advisory requires untrusted sort passed into a native query with sorting. Circulation constructs its pageable from numeric page and size and supplies no client sort. | No relevant sort path in the selected workflows. Keep server-controlled sorting and reassess other repositories before a production release. [Vendor advisory](https://spring.io/security/cve-2026-47834/). |
| Spring Security 6.5.11 | Five IDs appear in both core and OAuth2 core. The selected workflow uses BCrypt sessions and CSRF. No WebAuthn, embedded LDAP, DPoP implementation, or application encryption helper is used there. The optional OAuth profile needs separate review. | Keep the relevance assessment scoped to circulation. Review optional authentication and upgrade on a supported line before enabling new authentication paths. |
| Swagger UI 5.20.1 with DOMPurify 3.2.4 | Twenty-two matching IDs appear in both bundled scripts. Exposure depends on serving Swagger UI and accepting affected metadata. The production profile disables Swagger UI and API docs. | Keep production Swagger disabled. Review the newest compatible bundle before enabling it in any shared environment. |

An inventory match shows an advisory classification and grounds a triage
decision. No active security testing was performed.

Reproduce the scan from the repository root with Java 21 and Maven Wrapper.
The project-maintained feed avoids the need for a personal NVD API key.

```sh
./mvnw -B org.owasp:dependency-check-maven:13.0.0:check -Dformat=JSON \
  -DossindexAnalyzerEnabled=false \
  '-DnvdDatafeedUrl=https://dependency-check.github.io/DependencyCheck_Builder/nvd_cache/nvdcve-{0}.json.gz'
```

Run the browser decision table with
`python tests/team/security/check_roles.py --output output/security-roles.json`.
For passive replay use a local ZAP 2.17 daemon on loopback port 18090, then run
`python tests/team/security/run_zap_passive.py --output output/zap-passive.json`.
Both scripts create their own synthetic app data.

## Comparable load and recovery results

Targets set before testing: p95 below 1,000 ms per operation and zero
unexpected failures. Staff operations update inventory and loan history
synchronously. A one-second budget makes them responsive at local staff
load. Any unplanned failure is significant because a staff member must
know whether the item and loan changed.

| VUs / repetition | Borrow p95 (ms) | Return p95 (ms) | Completions/sec per operation | Unexpected failures |
| --- | ---: | ---: | ---: | ---: |
| 1 / 1 | 15.27 | 14.04 | 13.48 | 0% |
| 1 / 2 | 25.38 | 22.34 | 12.19 | 0% |
| 5 / 1 | 45.52 | 36.58 | 52.25 | 0% |
| 5 / 2 | 53.33 | 43.55 | 49.35 | 0% |

All four runs completed with zero active loans and all five items available.
Throughput increased roughly fourfold while latency rose under shared JVM
and database load. The highest p95 was 53.33 ms, within the planned
threshold. Local performance is a moderate PR-09 residual risk because
the H2 test excludes live infrastructure latency and MySQL workload
characteristics. The recovery test verifies PR-01 with a dependency
exception during borrow and a successful retry.

## Progress, control and residual risk

The [21–22 November reports](evidence/central-takeover-2026-11-22.md)
record six tracked defects, 1.48 defects/KLOC in the disclosed historical
denominator, 12/12 selected requirements exercised, and a 0/6 reopen rate.
The follow-up addresses concurrency, browser role evidence, keyboard
submission, and fail-closed gate logic. API-03 was tracked as issue #57
in the follow-up window and is excluded from the historical denominator.
The [effort comparison](TRACEABILITY_ESTIMATE.md) records the retrospectively reported effort, its source, and differences from the estimates where the scopes align.

| Window | Against plan | Defect density | Requirements coverage | Reopen rate | Control |
| --- | --- | --- | --- | --- | --- |
| 15–22 November | Initial phases and functional suite executed, with MySQL and branch enforcement held. | 6 / 4,060 nonblank Java lines = 1.48 per KLOC | 12/12 | 0/6 = 0% | Prioritize same-record races and complete branch enforcement. |
| 23–26 November, in progress | MySQL, 409s, browser role isolation, keyboard focus, full axe integration and dependency recheck executed. Hosted enforcement and individual records remain pending. | 7 tracked defects / 4,073 nonblank Java lines = 1.72 per KLOC. | 12/12 | N/A, no closures among these defects in this partial window. | Review the candidate on hosted CI, submit exact-revision evidence, and obtain the missing academic records. |

The small defect sample spans Java, dependency and frontend findings while
the denominator uses Java source. The density changed because the new
defect was recorded and the source denominator grew. It is a tracking
measure for this scope.

### Individual use-case ownership

An allocation for individual validation is Taha on UC-01/UC-04, Shaheer on
UC-02/UC-05, and Abdullah on UC-03/UC-06. It is a proposed allocation only.
Each member should take their pair, verify source and requirements, exercise
the alternate and exception flows, and commit their own substantive checks.
Retain the central author's true history. Closed issue #9 and the team effort entry do not establish individual ownership of two named cases per person.

PR-01 retains environment-specific risk beyond verified transaction and
recovery paths. PR-02/PR-04 now have same-item MySQL evidence. PR-03 has
all three item types and selection combinations. PR-05 has generated data,
malformed-input and media-type checks. PR-06 has representative roles and
cross-student isolation, with live session settings outside these runs.
PR-07 has the 14-day default and observed date behavior. PR-08 has saved
snapshots and retained records, with profile deletion outside this check.
PR-09 remains limited to the measured workload. PR-10 has automated
keyboard and accessibility evidence, with untested assistive technology
combinations. PR-11 retains dependency applicability and source-review
limits. PJ-01 now has runnable MySQL and browser evidence. PJ-02 remains
open because the individual use-case ownership evidence is still incomplete.

See the [release decision](RELEASE_DECISION.md) for the formal actual versus
target comparison.
