# Repository rules for the three-person SQE team

These rules apply to work on the SQE fork. They supplement the upstream `CONTRIBUTING.md` and `AGENTS.md`; application security and contribution rules there still apply.

## Starting team and area ownership

| GitHub account | Primary owned area | Expected deliverables |
| --- | --- | --- |
| `@Artfever` | Static analysis, white-box unit tests, mutation analysis, CI quality gates | SonarQube report and complexity comparison, coverage/MC/DC, PIT and custom operators, blocked/passing PR evidence |
| `@TahaSohail-Goat` | API/integration testing and generated test data | OpenAPI spec, EP/BVA generator, API test suite, cross-workflow and database read-back results |
| `@Abdullah-SE-bit` | Use-case coordination, browser automation, usability/accessibility, security, performance/recovery | Playwright flow coverage, Lighthouse/axe, access/ZAP/dependency results, k6 and recovery evidence |

These are starting assignments for planning, not a claim that the team has agreed to them. All three jointly maintain the risk register, test plan, traceability, weekly metrics, defect triage, final report, and AI-use record. Each member must author at least two use cases and commit identifiable work in the area they can explain during the viva. Ownership can change by a documented team decision; record the change in this table before work is reassigned.

## Branch and pull request workflow

1. Keep `main` as the reproducible integration branch. Create a short-lived branch from current `main` for each issue or focused task, named `sqe/<area>/<issue-number>-<short-name>` (for example, `sqe/api/12-borrow-boundaries`). The initial repository-rules branch may omit the issue number because Issues were disabled when these rules were drafted.
2. Open an issue before implementation. Assign an owner and add requirement/rule/risk IDs. Use the SQE defect template for defects; link its reproduction and evidence.
3. Push work to the task branch and open a PR to `main`. Use the PR template; include commands and actual results. Do not present upstream test counts as the team's tests.
4. Ask another team member to review when useful. Resolve review comments and rerun affected checks after changes. Approval is encouraged but not a merge requirement.
5. Merge only after required CI checks pass. Use squash merge for a coherent task, preserving the human author in Git history. Do not force-push or delete `main`, bypass checks, or merge a known failing test just to make progress.
6. Keep commits focused, imperative, and at most 72 characters on the first line. Preserve correct human author/committer metadata. Follow the upstream rule against automated co-author trailers and generated tool attribution in commit messages.

## Test and evidence rules

- Put team tests, generators, fixtures, and non-secret evidence under `tests/team/`. Keep raw outputs alongside a short interpretation and the exact commit/profile/tool version that produced them.
- Use synthetic records and test accounts. Keep passwords and tokens out of Git, issues, PRs, screenshots, and logs. Never print resolved Compose secrets.
- For every circulation test, record the starting state, action, expected response, item availability, and borrow-record state after both success and rejection.
- Update requirement and risk traceability whenever a test is added, changed, or removed. Record failed runs honestly and link a defect or documented environment issue.
- Do not change the upstream baseline commit record. Keep the original repository URL and baseline SHA in the report.

## GitHub `main` rule

The repository was transferred to `@Artfever`, whose connected GitHub CLI account has admin access. Issues were enabled on 20 November 2026. The `main` ruleset is configured in **Settings → Rules → Rulesets** for the SQE fork:

| Setting | Value |
| --- | --- |
| Target | Default branch `main`; enforcement **Active** |
| Require a pull request before merging | On |
| Required approvals | 0; teammate review is optional |
| Dismiss stale approvals when new commits are pushed | Off |
| Require review from Code Owners | Off (`.github/CODEOWNERS` lists area contacts only) |
| Require status checks to pass | On; current CI job contexts are `build`, `javascript`, `phase5`, `backup-script`, and `docker-build`; add the SQE quality jobs when implemented |
| Require branches to be up to date before merging | On |
| Block force pushes and deletions | On |
| Bypass list | Empty for the three members, including admins when GitHub permits |

The active ruleset is [SQE main branch CI](https://github.com/Artfever/libris-SQE-Project/rules/27724105), created on 20 November 2026 and updated to remove mandatory reviews, with no bypass actors. GitHub reports all five rules as effective on `main`. The five status-check contexts match the jobs in the live verification PR. Keep the ruleset active through the required blocked and passing PR demonstration. The files in this repository document the process; the live GitHub ruleset enforces branch protection.

Live repository settings at setup: Issues enabled; `@TahaSohail-Goat` and `@Abdullah-SE-bit` have write access; squash is the only allowed merge method; merged branches are deleted automatically. Recheck these settings before the final report if they change.
