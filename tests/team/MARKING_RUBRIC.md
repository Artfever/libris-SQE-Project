# SE3002 Software Quality Engineering — Marking Rubric

This table reproduces the 120-mark rubric from the project brief supplied for
the Fall 2026 submission. The report's evidence mapping appears in
[`RUBRIC_EVIDENCE.md`](RUBRIC_EVIDENCE.md); the rubric below preserves the
component marks, CLOs, and assessment descriptions. **Total weighting: 120
marks.**

| Component | Marks | CLO | Evidence assessed |
| --- | ---: | --- | --- |
| System and scope | 5 | CLO3 | Registered repository, reproducible baseline, and two related workflows with requirements, business rules and a defensible test basis analysed from the documentation. |
| Static analysis and metrics | 5 | CLO3 | SonarQube metrics reported and analysed for what they reveal about quality and risk; hand-calculated cyclomatic complexity compared with the tool. |
| Test plan, estimation and traceability | 7 | CLO3 | Complete test plan with justified scope, approach and criteria; three-point estimates compared with actual effort; traceability matrix and requirements coverage. |
| Risk register and exit criteria | 5 | CLO3 | Product and project risks scored and mapped to techniques and depth; measurable exit criteria tied to the highest risks. |
| White-box unit testing | 16 | CLO2 | 100% statement and branch coverage of server-side business logic, with any uncovered code defended; complete MCC and MC/DC pairs identified from MCC on the critical module. |
| API and integration testing | 10 | CLO2 | EP and 3-point BVA on all inputs, all API coverage criteria met, and cross-workflow checks. |
| Automated test data generation | 7 | CLO2 | OpenAPI specification, working generator, and correct regeneration for a changed specification. |
| Use case specification | 3 | CLO3 | Use cases derived from the requirements, with complete alternative and exception flows, preconditions and postconditions. |
| Use case test automation | 6 | CLO2 | Automated tests for every flow, with postcondition checks. |
| Mutation analysis and CI quality gate | 8 | CLO3 | Mutation score, custom operators, surviving-mutant analysis, gate thresholds justified from the evidence, and a correctly blocked pull request. |
| Usability and accessibility evaluation | 5 | CLO3 | Lighthouse and axe-core findings interpreted and prioritised; improvements made and verified by before-and-after comparison; automated task and keyboard tests. |
| Defensive security | 6 | CLO2 | Access decisions, passive and dependency evidence. |
| Performance and recovery | 5 | CLO2 | Comparable load runs and verified recovery state. |
| Defect management and root cause analysis | 7 | CLO3 | Defects logged with severity, priority, lifecycle and triage; root cause analysis with corrective and preventive actions; Pareto analysis; weaknesses linked to the risk register. |
| Monitoring and test completion report | 5 | CLO3 | Weekly progress against plan with control actions; GQM metrics read in context; completion report with residual risk and an evidence-based release or hold recommendation. |
| Viva, live task and AI-use record | 20 | CLO1 | Individual explanation of the owned area, the live task, and responsible, disclosed use of generative AI. |
