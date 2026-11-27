# AI-use record

Prepared for the Section B Libris SQE submission, 21 November 2026. This record
retains the relevant user prompts, tools, purposes, outputs, and checks/changes.
No passwords, session cookies, CSRF values, tokens, or secret environment
values were included.

## Retained prompts

| Prompt | Purpose | Output and human checks / changes |
| --- | --- | --- |
| “read agents.md and ingest whole rep end 2 end then inform me” | Establish repository instructions, structure, and project context. | Read the repository instructions and source/docs; later work followed `AGENTS.md`, `CONTRIBUTING.md`, and team rules. |
| “now complete phase 2 of implentation plan make pr merge it while solving related issues of phase2 donot do anything else” | Complete Phase 2 implementation and reviewable PR. | Produced Phase 2 artifacts and PR work; subsequent user feedback clarified coding and scope expectations. |
| “why havent u written single line of code and just md files for this ohase” | Correct course toward implementation rather than documentation-only changes. | Steered later work to executable tests, API error-handler code, CI gates, and regression fixes in addition to evidence documents. |
| “pull latest changes from main and then report me that if i have any paending issue/phase that i need to complete and is assigned to me” | Refresh assignment state from main and GitHub. | Fetched current `main`; confirmed open assigned issues #9 and #22–#25, and that #17–#21 are assigned to @Artfever. |
| “end to end fully complete the issues that were assigned to me” | Finish assigned issue work and required PR/evidence steps. | Led to CI PR #37, newspaper use-case PR #40, malformed-input fix PR #41, blocked demonstration PR #42, defect metrics, report, and package preparation. |
| “Yes, contact them” (answer to the question asking whether @Artfever and @TahaSohail-Goat may be contacted on GitHub for their assigned use-case contributions/reviews) | Authorize a specific Phase 2 coordination request. | Posted one issue #9 request assigning the contributors their two use cases and review; no authorship was attributed without their commits. |
| “Abdullah-SE-bit = Name: Abdullah Adnan Roll No: 24I-3020; Artfever = Name: Muhammad Shaheer Roll No: 24I-3063; TahaSohail-Goat = Name: Taha Sohail Roll No: 24I-3165” and “B” | Provide real team identities and section for output names. | Used the provided identities and section in package metadata and filenames. |

## Tools, purpose, outputs, and verification

| Tool | Purpose and output | Checks or changes made |
| --- | --- | --- |
| Codex language model | Analyze the assigned issues, inspect repository evidence, draft code/tests/evidence/report, and assemble submission artifacts. | Compared implementation and test expectations against Java/Spring source, CI workflow, existing API contract, issue acceptance criteria, and observed GitHub results. Code and generated test assertions were changed after failures and rerun. |
| PowerShell, Git, Maven Wrapper, Python | Read/modify repository files; branch, commit, push, rebase, build, test, generate evidence and package files. | After the Boot and dependency updates, Java 21 `clean verify` passed: 210 tests, zero failures/errors/skips, JaCoCo gate met. On 2026-11-22 a fresh Java 21.0.11/Maven 3.9.11 `clean verify` again passed 210 tests with zero failures/errors/skips. The fresh H2 API suite passed 7 tests, Playwright passed 30, and the usability workflow passed 2 tasks with five axe states at zero violations. A focused `SecurityHardeningTest` comprised 26 of the passing Maven tests. API generator tests: 4 passed; generated smoke: 1 passed; H2 fixture seed/read-back/reset passed. Lighthouse accessibility 90 for both flows in both themes. The updated OSV audit checked 137 packages; one package/two Spring MVC advisory IDs remain assessed as not applicable to current source paths. An initial post-fix ZAP image pull did not finish; the later ZAP 2.17.0 passive retest completed successfully after CSP hardening, proxied 52 messages, and reported three informational alerts only. |
| GitHub CLI (`gh`) and GitHub REST API | Read assigned issues, PRs, checks, actions, branch protections, and post explicitly authorized coordination comments on #9, #23, and #25; create and merge PRs. | PR #37's eight checks passed and it merged by squash. PR #42 is intentionally retained open and blocked with failing required checks. Ruleset update was attempted without bypass; API reported this account has write permission but not admin permission, so the live context change was not made. |
| Playwright / Chromium | Run browser acceptance workflows against local synthetic H2 state. | 30 browser tests passed in the recorded run; visible behavior was checked against persisted API state. |
| PIT and SonarQube Community Build | Measure focused mutation behavior and static-analysis gate/metrics. | PIT killed 72/72 mutants in targeted classes; Sonar quality gate passed. Scope is recorded; neither result is presented as whole-project mutation coverage. |
| ReportLab and Poppler / PDF inspection tools | Create and visually inspect the final PDF output. | The final PDF was rendered page-by-page to PNG and visually checked for clipping, overlap, page numbering, and readable tables; extracted text and page metadata were checked. |

## Ownership and review

Commits use the configured repository Git identity for `Abdullah-SE-bit`; no
automated-agent co-author trailer or generated-tool attribution was added.
PR #40 originally contained Abdullah's newspaper use cases. On 2026-11-22,
Abdullah explicitly directed a central-owner takeover of the remaining work.
The consolidated specification text and additional defect-triage and package
records were therefore prepared under Abdullah with Codex assistance. The
original workflow allocation remains separately credited: Shaheer's UC-01/04,
Taha's UC-02/05, and Abdullah's UC-03/06. Taha confirmed that he and Shaheer
completed their assigned pairs; the contribution links and the distinction
between earlier workflow contributions and later specification consolidation
are recorded in `USE_CASES.md`. At the 22 November snapshot, no peer review of
the consolidated artifacts or personal oral-viva performance was claimed.
Taha later reported that a teammate reviewed the consolidated project/report;
see the 27 November closeout below. The fresh commands, results, predictions,
and limits are in `evidence/central-takeover-2026-11-22.md`.

## Latest continuation prompt

| Prompt | Purpose | Output and human checks / changes |
| --- | --- | --- |
| “pull latest changes and procedd with my tasks and end this completely” | Resume after the team confirmed their contributions would arrive later; sync and finish the work that does not depend on teammate authorship. | Fetched latest `origin/main` at `41de64b`, fixed assigned Phase 4 findings #44–#47 in [PR #48](https://github.com/Artfever/libris-SQE-Project/pull/48), refreshed Phase 5 reports and evidence, and retained truthful limits for ZAP, MySQL concurrency, team-owned use cases, and viva rehearsal. |
| “after merging ur prs u can stop working because they will not be giving there work anytime soon when there work is done ill inform u” | Define the stopping point for teammate-dependent work. | Proceeded with Abdullah-owned fixes and deliverables; did not attribute team member contributions or wait for them before preparing a reviewable PR. |
| “complete it end to end” (with the open-issues snapshot) | Finish the individually verifiable work for Phase 2 and Phase 5, refresh the deliverables, and assess remaining assigned issue criteria. | Reran Java 21 `clean verify` (210 tests passed; JaCoCo gate met), all 30 browser acceptance cases, and axe scans (zero violations on five dark/light borrow/modal/return states). Ran ZAP 2.17.0 passive-only twice: the first retest exposed `unsafe-inline` CSP alerts; after externalizing first-paint code/styles, the final scan proxied 52 messages and returned three informational alerts only. Preserved Phase 4 baseline evidence, updated metrics after #44–#47 closed via PRs #48/#50, and prepared the viva worksheet. Teammate-owned commits/reviews and each member's own viva record remain unclaimed until contributed by that member. |
| “complete all issues” | Continue the full issue-completion goal and audit every live open assigned issue. | Refreshed `main`, verified the final package and merged PR #52, and rechecked issues #9, #23, and #25. No new peer-authored use-case commits, triage contributions, or member viva records had arrived. Posted the remaining #25 personal evidence request under prior user authorization. These issues remain open until their contributor-specific acceptance evidence is supplied. |
| “overtake this plan of other peoples contribution and do it all your self” | Replace the waiting plan with a central-owner completion path. | Reassigned all remaining artifacts to Abdullah without inventing peer contributions; completed all six use cases, consolidated triage and GQM, ran fresh Java/API/browser/accessibility checks, and prepared an AI-assisted technical mock viva. PR #54 merged, issues #9/#23/#25 were closed with transparent takeover comments, and the PDF/ZIP were regenerated from the merged main. No student oral performance is claimed. |

## 26 November rubric follow-up

| Tool and retained prompt | Purpose and output | Verification and attribution |
| --- | --- | --- |
| Codex. “You need to compelete each and everything end to end so I can get full marks all parts 1 to 5 , read carefully everything should be completed and should be analyzed properly” | Implement and review test and evidence gaps across the five parts. Drafted the MySQL race harness, browser security and keyboard checks, CI and release preflight changes, troubleshooting and report updates. | Model-assisted work run against synthetic fixtures. [Current evidence](RUBRIC_EVIDENCE.md) gives observed results and limitations. Team review and acceptance should be recorded by the actual reviewer. |
| Maven, SonarQube, Chromium, MySQL, k6, ZAP, OWASP Dependency-Check, ReportLab | Execute and cross-check runtime evidence, static analysis, dependencies, and package integrity. | Keep historical raw evidence and distinguish additional results by date and scope. No new individual use-case authorship, actual effort, registration, or instructor approval has been inferred. |

Taha later supplied ten retrospective effort figures and confirmed registration.
Codex calculated the total and comparable differences, checked the closed GitHub
issues for task references, and refreshed the package. The hours are attributed
to Taha's report. Issue assignments and closure events support task history.

Taha subsequently confirmed that he and Shaheer completed their assigned
use-case pairs. Codex recorded that confirmation beside the existing GitHub
evidence and kept the consolidated specification history intact.

## 27 November rubric closeout

Codex compared the 120-mark rubric with the current evidence and main-branch
workflow. After confirming that PR #56 was merged and that the 26 November
main run passed all nine jobs, the authenticated GitHub CLI closed issue #57
as completed. Codex updated the API finding status, clarified the historical
completion report against the newer concurrency and CI results, regenerated
the PDF with the marking rubric, and checked its extracted text and rendered
pages. On 27 November, Taha reported that a teammate had reviewed the
consolidated project/report. The reviewer identity and review comments were
not supplied, so this records Taha's confirmation rather than a named formal
approval. No instructor approval or personal oral-viva performance is claimed.
