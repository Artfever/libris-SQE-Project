# Circulation traceability and estimate

## Requirement and rule traceability

Planned test IDs identify future executable tests; `UC-*` are the reviewed use
case flows in `USE_CASES.md`. Evidence paths and actual results remain pending
until the corresponding tests run. Never report a planned case as passed.

| Requirement/rule | Planned tests / use case | Risk | Owner | Evidence / status |
| --- | --- | --- | --- | --- |
| FR-B01 | T-BORROW-ROLE; UC-01, UC-02, UC-03 | PR-06 | `@TahaSohail-Goat` | Pending automation |
| FR-B02 | T-REQ-VALIDATION | PR-05 | `@TahaSohail-Goat` | Pending automation |
| FR-B03 | T-ITEM-COUNT-0; T-ITEM-COUNT-2; T-ITEM-COUNT-3 | PR-03 | `@TahaSohail-Goat` | Pending automation |
| FR-B04 | T-BORROW-AVAILABLE; T-BORROW-UNAVAILABLE; UC-01–UC-03 | PR-01, PR-03 | `@TahaSohail-Goat` | Pending automation |
| FR-B05 | T-DUE-DEFAULT; T-DUE-EXPLICIT; T-DATE-BOUNDARY | PR-07 | `@TahaSohail-Goat` | Pending automation |
| FR-B06 | T-BORROW-SNAPSHOT; UC-01–UC-03 | PR-08 | `@Artfever` | Pending automation |
| FR-R01 | T-RETURN-ALL-TYPES; UC-04–UC-06 | PR-01 | `@TahaSohail-Goat` | Pending automation |
| FR-R02 | T-RETURN-REPEAT; UC-06 | PR-04 | `@TahaSohail-Goat` | Pending automation |
| FR-R03 | T-RETURN-MISSING | PR-05 | `@TahaSohail-Goat` | Pending automation |
| FR-R04 | T-STUDENT-OWN-HISTORY; T-STUDENT-MUTATION-DENIED | PR-06 | `@Artfever` | Pending automation |
| FR-R05 | T-HISTORY-READBACK; UC-04–UC-06 | PR-08 | `@Artfever` | Pending automation |
| FR-R06 | T-CSRF-MISSING; T-SESSION-MISSING | PR-06 | `@Artfever` | Pending automation |
| BR-C01 | T-ITEM-COUNT-* | PR-03 | `@TahaSohail-Goat` | Pending automation |
| BR-C02 | T-BORROW-EXISTS-AVAILABLE; T-BORROW-MISSING; T-BORROW-UNAVAILABLE | PR-01, PR-03, PR-05 | `@TahaSohail-Goat` | Pending automation |
| BR-C03 | T-BORROW-STATE-SUCCESS; T-BORROW-STATE-REJECTED; T-BORROW-CONCURRENT | PR-01, PR-02 | `@TahaSohail-Goat` | Pending automation |
| BR-C04 | T-RETURN-STATE; T-RETURN-REPEAT; T-RETURN-CONCURRENT | PR-04 | `@TahaSohail-Goat` | Pending automation |
| BR-C05 | T-DUE-DEFAULT; T-DUE-EXPLICIT; T-DATE-ORDER-POLICY | PR-07 | `@TahaSohail-Goat` | Pending; date-order policy is unspecified |

## Executed Phase 4 links (#17–#21)

The Phase 4 owner added these executed links without replacing the Phase 2
planned-case inventory above. See [the Phase 4 report](PHASE4_REPORT.md) and
the raw paths it references. A pending label in the original table above does
not override the executed evidence below.

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

| Work area | Owner | O (h) | M (h) | P (h) | Expected (h) | Actual (h) | Assumptions / evidence |
| --- | --- | -: | -: | -: | -: | --- | --- |
| Requirements and business rules (#8) | `@Abdullah-SE-bit` | 2 | 3 | 5 | 3.2 | Pending owner entry | Source review and review cycle; this draft exists. |
| Six use-case authoring/review (#9) | All three | 4 | 6 | 10 | 6.3 | Pending per contributor | Two cases per contributor; current integrated drafts need contributor revisions/commits. |
| Risk plan and register (#10) | `@Abdullah-SE-bit` | 3 | 5 | 8 | 5.2 | Pending owner entry | Risk scoring and control mapping; this draft exists. |
| Traceability and estimate (#11) | `@Abdullah-SE-bit` | 2 | 3 | 5 | 3.2 | Pending owner entry | Initial plan-to-test links; update after Phase 3/4 execution. |
| Integration and review | `@Abdullah-SE-bit` + reviewers | 1 | 2 | 4 | 2.2 | Pending owner entry | Reconcile IDs, review source links, record final PR feedback. |
| **Total** |  | **12** | **19** | **32** | **20.1** | **Pending** | Update actuals from contributors' time records when Phase 2 is accepted. |

## Phase 2 completion checklist

- [x] Draft at least eight requirements across both workflows, with more than three per workflow.
- [x] Draft at least four source-backed rules, including boundary, two-condition decision, and state transition.
- [x] Prepare six numbered use-case drafts with preconditions, main, alternate, exception, and persisted postconditions.
- [ ] Each teammate reviews, revises, and records their two cases in an identifiable human-authored commit (required by #9).
- [x] Draft the risk plan, eight product risks, two project risks, 5×5 scores, controls, owners, and measurable criteria.
- [x] Map each requirement/rule to planned tests, risks, owner, and evidence placeholder.
- [ ] Record actual effort from each contributor and update estimates at phase acceptance.

