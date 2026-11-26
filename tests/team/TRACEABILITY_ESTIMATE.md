# Circulation traceability and estimate

## Requirement and rule traceability

Test IDs identify the planned/executed checks; `UC-*` are the centrally authored
flows in `USE_CASES.md`. Execution results are distinguished below and in the
linked fresh evidence. A planned concurrency check is not reported as passed.

| Requirement/rule | Planned tests / use case | Risk | Owner | Evidence / status |
| --- | --- | --- | --- | --- |
| FR-B01 | T-BORROW-ROLE; UC-01, UC-02, UC-03 | PR-06 | `@Abdullah-SE-bit` (takeover) | Executed; role/API and six-flow browser evidence |
| FR-B02 | T-REQ-VALIDATION | PR-05 | `@Abdullah-SE-bit` (takeover) | Executed; generated and malformed request partitions |
| FR-B03 | T-ITEM-COUNT-0; T-ITEM-COUNT-2; T-ITEM-COUNT-3 | PR-03 | `@Abdullah-SE-bit` (takeover) | Executed; all eight item-selection combinations |
| FR-B04 | T-BORROW-AVAILABLE; T-BORROW-UNAVAILABLE; UC-01–UC-03 | PR-01, PR-03 | `@Abdullah-SE-bit` (takeover) | Executed sequentially; H2 API and browser persisted-state checks |
| FR-B05 | T-DUE-DEFAULT; T-DUE-EXPLICIT; T-DATE-BOUNDARY | PR-07 | `@Abdullah-SE-bit` (takeover) | Executed; default, explicit, and neighboring date cases |
| FR-B06 | T-BORROW-SNAPSHOT; UC-01–UC-03 | PR-08 | `@Abdullah-SE-bit` (takeover) | Executed; borrower snapshots checked |
| FR-R01 | T-RETURN-ALL-TYPES; UC-04–UC-06 | PR-01 | `@Abdullah-SE-bit` (takeover) | Executed for all item types; H2/browser read-back |
| FR-R02 | T-RETURN-REPEAT; UC-06 | PR-04 | `@Abdullah-SE-bit` (takeover) | Sequential repeat return executed; concurrent return not run |
| FR-R03 | T-RETURN-MISSING | PR-05 | `@Abdullah-SE-bit` (takeover) | Executed; missing and malformed IDs covered |
| FR-R04 | T-STUDENT-OWN-HISTORY; T-STUDENT-MUTATION-DENIED | PR-06 | `@Abdullah-SE-bit` (takeover) | Executed; own-history and denied mutation checks |
| FR-R05 | T-HISTORY-READBACK; UC-04–UC-06 | PR-08 | `@Abdullah-SE-bit` (takeover) | Executed; returned history read back |
| FR-R06 | T-CSRF-MISSING; T-SESSION-MISSING | PR-06 | `@Abdullah-SE-bit` (takeover) | Executed; CSRF/session cases in role suite |
| BR-C01 | T-ITEM-COUNT-* | PR-03 | `@Abdullah-SE-bit` (takeover) | Executed; zero, one, two, and three item selections |
| BR-C02 | T-BORROW-EXISTS-AVAILABLE; T-BORROW-MISSING; T-BORROW-UNAVAILABLE | PR-01, PR-03, PR-05 | `@Abdullah-SE-bit` (takeover) | Executed; existence and availability outcomes |
| BR-C03 | T-BORROW-STATE-SUCCESS; T-BORROW-STATE-REJECTED; T-BORROW-CONCURRENT | PR-01, PR-02 | `@Abdullah-SE-bit` (takeover) | Success/rejection executed; `T-BORROW-CONCURRENT` remains untested |
| BR-C04 | T-RETURN-STATE; T-RETURN-REPEAT; T-RETURN-CONCURRENT | PR-04 | `@Abdullah-SE-bit` (takeover) | Sequential return/repeat executed; `T-RETURN-CONCURRENT` remains untested |
| BR-C05 | T-DUE-DEFAULT; T-DUE-EXPLICIT; T-DATE-ORDER-POLICY | PR-07 | `@Abdullah-SE-bit` (takeover) | Default/explicit/boundary dates executed; date-order policy is unspecified |

## Executed Phase 4 links (#17–#21)

The Phase 4 owner added these executed links. See [the Phase 4 report](PHASE4_REPORT.md)
and the raw paths it references. Fresh Phase 2/3 API and browser execution is
recorded in [`evidence/central-takeover-2026-11-22.md`](evidence/central-takeover-2026-11-22.md).

| Requirement/rule or risk | Executed Phase 4 check | Evidence / result |
| --- | --- | --- |
| FR-B01, FR-R01, FR-R04, PR-06 | Seven staff/student allow/deny decisions and persisted-state checks | `evidence/security-roles-2026-11-21.json`; passed |
| FR-B03, BR-C01, PR-03 | Custom exact-one-item PIT operator and MCC test | `evidence/pitest/phase4-mutations.xml`; killed |
| FR-B05, BR-C05, PR-07 | Custom 14-to-13-day PIT operator and due-date assertion | `evidence/pitest/phase4-mutations.xml`; killed |
| FR-B04, FR-R01, FR-R05, BR-C03, BR-C04, PR-01, PR-04 | 1/5-user borrow/return cycles with persisted read-back | `evidence/performance/runs.json`; four passing runs |
| FR-B04, FR-R05, BR-C03, PR-01 | Audit-failure rollback, retry and no-duplicate state | `evidence/recovery/TEST-com.example.lms.team.TeamRecoveryTest.xml`; passed |
| PR-10 | Invalid/corrected browser tasks, keyboard and axe/Lighthouse comparison | `evidence/usability/`; heading fixed; contrast/name findings open |
| PR-11 | Passive ZAP and resolved Maven/OSV inventory | `evidence/security/`; CSP/SRI/advisory triage open |

## Generated API and integration cases (#14 and #15)

The draft contract, generator and smoke runner are in [api/](api/README.md).
Generated required-field cases map to FR-B02 and PR-05. The generated item count
boundary maps to FR-B03, BR-C01 and PR-03. The smoke flow also
maps to FR-B01, FR-B04, FR-R01, FR-R05, BR-C03 and BR-C04. These cases do
not establish full requirement coverage. See the API guide for current execution
status and limitations; do not count generator unit tests as application tests.

The broader suite covers FR-B01?FR-B06, FR-R01?FR-R06 and BR-C01?BR-C05.
See the [executed coverage and risk mapping](evidence/api-integration-2026-11-21.md).

## Three-point estimate

Estimates are person-hours, not calendar duration. PERT expected effort is
`(optimistic + 4 × most likely + pessimistic) / 6`. Assumes Java 21 and local
H2 are available, contributors can review promptly, and the Phase 1 fixture
guide is usable. MySQL, browser, and mutation tooling may increase actuals.

| Work area | O (h) | M (h) | P (h) | PERT expected |
| --- | ---: | ---: | ---: | ---: |
| Requirements and business rules | 2 | 3 | 5 | 3h 10m |
| Six use-case specifications and review | 4 | 6 | 10 | 6h 20m |
| Risk plan and register | 3 | 5 | 8 | 5h 10m |
| Traceability and estimation | 2 | 3 | 5 | 3h 10m |
| Phase 2 integration and review | 1 | 2 | 4 | 2h 10m |
| **Phase 2 total** | **12** | **19** | **32** | **20h** |

## Phase 2 completion checklist

- [x] Draft at least eight requirements across both workflows, with more than three per workflow.
- [x] Draft at least four source-backed rules, including boundary, two-condition decision, and state transition.
- [x] Prepare and complete six numbered use cases with preconditions, main, alternate, exception, and persisted postconditions; all are centrally authored under the documented 2026-11-22 takeover.
- [x] Draft the risk plan, eight product risks, two project risks, 5×5 scores, controls, owners, and measurable criteria.
- [x] Map each requirement/rule to planned tests, risks, owner, and evidence placeholder.
- [x] Record reported actual person-hours and compare them with estimates where the scopes align.


## Follow-up traceability and estimates

`T-BORROW-CONCURRENT` and `T-RETURN-CONCURRENT` now pass for all three
catalogue types on [disposable MySQL 8.4.11](evidence/mysql-concurrency-2026-11-26.json).
Both forced lock timeouts returned 409 and preserved state. FR-R04 now
includes [two-student isolation](evidence/security/roles-playwright-2026-11-26.json)
with both students' records present. The unsupported request media type
case extends FR-B02 and PR-05. These results supersede the pending entries
above for the current evidence set.

## Reported actual effort and comparison

Taha Sohail provided these retrospective figures for work already completed.
Rows marked Team are team totals supplied by Taha. Rows with a named member
record that person's reported contribution. No individual breakdown was
provided for the team rows. The ten figures total **14 person-hours of
reported effort**. GitHub issues corroborate task scope, assignment and
closure. Issue or commit timestamps do not measure working time.

| Area | Reported effort | Attribution | Closed GitHub references |
| --- | ---: | --- | --- |
| Setup and baseline | 30m | Team | [#6](https://github.com/Artfever/libris-SQE-Project/issues/6), [#7](https://github.com/Artfever/libris-SQE-Project/issues/7) |
| Requirements and business rules | 40m | Team | [#8](https://github.com/Artfever/libris-SQE-Project/issues/8) |
| Use-case specifications and review | 2h | Team | [#9](https://github.com/Artfever/libris-SQE-Project/issues/9) |
| Test plan and risk register | 50m | Abdullah | [#10](https://github.com/Artfever/libris-SQE-Project/issues/10) |
| Traceability and effort estimation | 1h | Taha | [#11](https://github.com/Artfever/libris-SQE-Project/issues/11) |
| SonarQube, white-box tests, mutation and CI | 2h | Team | [#12](https://github.com/Artfever/libris-SQE-Project/issues/12), [#13](https://github.com/Artfever/libris-SQE-Project/issues/13), [#17](https://github.com/Artfever/libris-SQE-Project/issues/17), [#22](https://github.com/Artfever/libris-SQE-Project/issues/22) |
| API, OpenAPI generation and MySQL integration | 3h | Team | [#14](https://github.com/Artfever/libris-SQE-Project/issues/14), [#15](https://github.com/Artfever/libris-SQE-Project/issues/15), [MySQL follow-up](https://github.com/Artfever/libris-SQE-Project/pull/56) |
| Browser, usability, accessibility and security | 1h | Shaheer | [#16](https://github.com/Artfever/libris-SQE-Project/issues/16), [#18](https://github.com/Artfever/libris-SQE-Project/issues/18), [#19](https://github.com/Artfever/libris-SQE-Project/issues/19) |
| Performance and recovery | 1h | Taha | [#20](https://github.com/Artfever/libris-SQE-Project/issues/20), [#21](https://github.com/Artfever/libris-SQE-Project/issues/21) |
| Final integration, review, report and archive | 2h | Abdullah | [#24](https://github.com/Artfever/libris-SQE-Project/issues/24), [#25](https://github.com/Artfever/libris-SQE-Project/issues/25) |
| **Total reported** | **14h** | Mixed team totals and named contributions | |

The issue assignee and the reported contributor can differ. Abdullah was the
assignee for #11. Shaheer, using the Artfever account, was the assignee
for #20?#21. Issue #16 was assigned to Taha. This evidence preserves those
assignments and the reported effort in separate fields. The 2h for use cases
is a team effort figure and gives no breakdown of case authorship or
individual ownership. The [individual case record](RUBRIC_EVIDENCE.md) separately documents Taha's completion confirmation and the linked contributions. The historical authorship of the consolidated specifications still applies.

### Phase 2 estimate versus reported effort

| Matched area | PERT expected | Reported | Difference |
| --- | ---: | ---: | --- |
| Requirements and business rules | 3h 10m | 40m | 2h 30m below |
| Six use-case specifications and review | 6h 20m | 2h | 4h 20m below |
| Test plan and risk register | 5h 10m | 50m | 4h 20m below |
| Traceability and estimation | 3h 10m | 1h | 2h 10m below |
| **Matched subtotal** | **17h 50m** | **4h 30m** | **13h 20m below** |

Setup has no matching recorded estimate. The historical 2h 10m Phase 2
integration and review estimate excludes the final report and archive,
so the broader 2h entry has no direct variance. Comparing the 14h total
to the 20h Phase 2 estimate would compare different scopes.

### Technical planning scenarios versus reported effort

These scenarios estimate repeating the technical work. The differences
provide context for a repeat run. They do not measure the forecast
accuracy of the original Phase 2 plan.

| Area | O (h) | M (h) | P (h) | PERT expected | Reported | Difference |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Sonar, white-box, mutation and CI | 3 | 5 | 9 | 5h 20m | 2h | 3h 20m below |
| API generation, integration and MySQL | 3 | 5 | 9 | 5h 20m | 3h | 2h 20m below |
| Browser, usability, accessibility and security | 4 | 6 | 10 | 6h 20m | 1h | 5h 20m below |
| Performance and recovery | 2 | 3 | 6 | 3h 20m | 1h | 2h 20m below |

Potential causes of variance include tool installation, dependency indexing
and CI feedback. The retrospective entries do not show which activities
account for the differences. A future run should log each member's time
against the same areas used for the estimate, with waiting time distinguished
from hands-on work.
