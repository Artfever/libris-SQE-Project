# SQE project plan: Libris circulation

## Baseline and scope

- Upstream: https://github.com/prathamkashyap/libris (MIT).
- Baseline commit: `faf2bc0d28b68d4c8ff8c0ffb0fcf5bb87d42804`. The local fork and upstream `main` matched at setup.
- Module: Circulation Management. Workflows: borrow and return a book, magazine, or newspaper.
- Shared state: an item's availability, the active borrow record, and the retained loan history. Borrow changes available to unavailable; return restores it and dates the record.
- Test roles: `ADMIN` or `LIBRARIAN` for state changes; `STUDENT` for denied mutations and allowed own-history reads. Confirm exact route rules in `SecurityConfig`.
- Keep our test code, data generators, and evidence under `tests/team/` so upstream tests remain distinguishable.
- Team of three: `@Artfever`, `@TahaSohail-Goat`, and `@Abdullah-SE-bit`. Follow `tests/team/REPOSITORY_RULES.md` for area ownership, branches, reviews, and evidence.

## Phase 1 — establish a reproducible baseline

1. Register the repository, module, and two workflows in the section's shared sheet within the brief's deadline. The owner confirmed the section B entry on 20 November 2026; retain [the registration record](evidence/registration-2026-11-20.md) and cite it in the final report.
2. Record the commit, license, Java/Maven/Node/Python/Docker versions, and exact commands used. Save a clean Git baseline.
3. Run `backend\mvnw.cmd clean verify` using Java 21. Record actual results and existing coverage; never count upstream tests as our own.
4. Start the `h2` profile for fast local API and browser work. Use a private local admin password. Record fixture creation and reset steps; H2 resets on restart.
5. When a Docker engine is running, use a disposable local MySQL stack to check behavior that H2 cannot prove. Preserve named volumes unless an explicitly disposable test volume is used.

The Phase 1 fixture and H2 reset procedure are in [the circulation fixture guide](fixtures/README.md). The MySQL-specific check remains conditional on a local Docker engine.

## Phase 2 — write the test basis and management documents

Lead: `@Abdullah-SE-bit` (#8–#11). All three members author two use cases each for #9.

1. Derive at least eight functional requirements across both workflows, at least three per workflow. Include validation, dates, availability, history, repeat requests, and role access.
2. State at least four business rules. Include a boundary/limit, a decision with at least two Boolean conditions, and a state transition. Cite the code/docs or label assumptions.
3. Define two use cases per team member (six total), each with main, at least two alternate, and two exception flows; record preconditions and postconditions.
4. Create the risk-based test plan: scope, levels, roles/owners, environment, fixtures, schedule, entry/exit/suspension/resumption criteria, and at least three measurable release criteria (including one tied to each highest risk).
5. Create a risk register with at least eight product and two project risks, likelihood and impact scored 1–5 on a 5×5 matrix, and test controls mapped to each.
6. Build the requirement-to-test traceability matrix and a three-point effort estimate. Update estimates with actual effort at completion.

Draft artifacts are maintained in [the test basis](TEST_BASIS.md),
[the use cases](USE_CASES.md), [the risk-based test plan](TEST_PLAN.md), and
[the traceability/estimate](TRACEABILITY_ESTIMATE.md). The phase remains open
until each teammate has revised and committed their own two use cases and the
contributors record actual effort; the integrated drafts do not substitute for
those human contributions.

## Phase 3 — design and automate functional tests

Lead: `@TahaSohail-Goat` (#12–#16).

1. Run SonarQube and record complexity, duplication, smells, bugs, vulnerabilities, coverage, debt, and ratings. Hand-calculate cyclomatic complexity for a circulation business-rule function and compare it with SonarQube.
2. Unit-test all circulation server-side business logic to 100% statement and branch coverage; justify exclusions. Model the critical decision with an MCC table and cover its MC/DC pairs.
3. API/integration-test all input equivalence classes and three-point boundaries (just below, at, and just above each limit). Include all item types, valid/invalid dates, exactly-one-item selection, unavailable items, duplicate returns, missing IDs, permissions, CSRF, response contracts/statuses, invalid state transitions, repeated requests, and read-back of availability and history after changes and rejections. Keep one invalid value per equivalence-partition test.
4. Write an OpenAPI specification for the selected endpoints and a generator that outputs the planned EP/BVA cases. Demonstrate that changing two constraints changes the generated cases.
5. Automate every use-case flow in Playwright against a seeded local app. Assert the displayed outcome and the persisted postcondition.

## Phase 4 — other quality evidence

Lead: `@Artfever` (#17–#21).

1. Use PIT for circulation mutation analysis, add two custom operators tied to the business rules, inspect at least 15 survivors, and justify the score threshold.
2. Run one browser task per workflow with an invalid value followed by correction; include keyboard-only form navigation in one, checking focus order and keyboard submission. Run Lighthouse (accessibility, best practices, SEO) and a full axe-core scan on both key screens, record each issue's affected element and user impact, then rerun both tools after fixing one issue. Keep before/after reports; no participants or manual walkthroughs are required.
3. Automate at least four role/access decisions across two roles, including allowed and denied actions with actual responses. Run OWASP ZAP passive scanning while the workflows execute and a dependency audit; document component versions, evidence, impact, correction, and verified controls. Assess only local synthetic data and test accounts.
4. Set p95 latency and unexpected-failure targets for one operation per workflow. Use k6 at one and at least five users, twice each, for at least 60 seconds after reaching target load. Save raw outputs and compare like-for-like runs.
5. Automate a controlled failure and recovery of a state-changing operation; verify no duplicate record and the correct final availability.

## Phase 5 — gate, defects, and final submission

Lead: `@Abdullah-SE-bit` (#22–#25). All three contribute and review the final report, package, AI-use record, and viva preparation.

1. Add GitHub Actions gates for SonarQube, all team tests, coverage, and mutation score. Demonstrate both a blocked and passing pull request without bypasses.
2. Track defects as GitHub issues with severity, priority, status, triage decision, and risk links. Perform 5 Whys plus fishbone for two major defects with corrective and preventive actions; report a defect-category Pareto and weekly progress/GQM metrics (defect density, requirements coverage, reopen rate) against the plan with control actions.
3. Produce the completion report with tested/not tested scope, deviations, open defects, residual risks, and release/hold recommendation. Compare actuals with all three release criteria.
4. Package the PDF report and repository ZIP including `.git`, scripts, fixtures, CI, raw evidence, AI-use record (tool, purpose, output, and what was checked/changed), and each member's identifiable commits. Use the exact `Project_RollNumber1_RollNumber2_RollNumber3_Section` base name for both files; pair members omit the third roll number. Rehearse rerunning a selected test and predicting the result of a live business-rule/specification change for the viva.

## Submission gate — all must be true before submitting

- The shared-sheet registration is complete, and the report identifies the upstream URL, MIT license, exact baseline commit, module, workflows, four rules, eight requirements, two roles, and shared state.
- Every phase above has its requested runnable scripts, raw reports/screenshots, recorded results, and requirement/risk links. Results are from this team's own tests; upstream tests are clearly labeled baseline evidence.
- The final PDF includes the full test-management documents, SonarQube and hand complexity comparison, unit/API/use-case results, mutation analysis, accessibility/usability before-and-after results, defensive security evidence, k6 and recovery evidence, defect/root-cause analysis, CI blocked/passing evidence, weekly metrics, and completion report.
- The completion report compares actual results with the three measurable release criteria, states untested scope and deviations, lists open defects and residual risk, and gives an evidence-backed release or hold decision.
- The ZIP contains the repository including `.git`, baseline history, team code and test data, setup/reset instructions, CI configuration, raw evidence, and an AI-use record. Every member has identifiable work and can explain and rerun their area in the viva.
- File names match the required format, and the final PDF/ZIP open correctly. Do not treat a checked box in this plan as evidence; verify the corresponding artifact and result.

## Immediate next action

Have each teammate revise and commit their two assigned use cases in
`tests/team/USE_CASES.md`, then record actual effort in
`tests/team/TRACEABILITY_ESTIMATE.md`. The test basis and initial H2 fixture
evidence are available for the next phase; continue to distinguish planned
tests from executed results.
