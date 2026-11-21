# Repository rules for the three-person SQE team

These rules apply to work on the SQE fork. They supplement the upstream `CONTRIBUTING.md` and `AGENTS.md`; application security and contribution rules there still apply.

## Team and phase ownership

| GitHub account | Phase responsibility | Issues |
| --- | --- | --- |
| `@Abdullah-SE-bit` | Phase 2 test basis and management documents; Phase 5 quality gates, metrics, report, and submission coordination | #8–#11 and #22–#25 |
| `@TahaSohail-Goat` | Phase 3 static analysis, unit/API tests, OpenAPI generator, and browser flows | #12–#16 |
| `@Artfever` | Phase 4 mutation, accessibility, security, performance, and recovery evidence | #17–#21 |

The repository owner assigned these phase owners on 21 November 2026. The issue assignee is the lead responsible for coordinating and finishing that issue; it does not replace required contributions from the rest of the team. In particular, each member must author two of the six Phase 2 use cases and commit identifiable work for #9. All three must review and contribute evidence for the shared Phase 5 completion report, submission package, AI-use record, and viva preparation. The phase lead integrates those contributions. Record later ownership changes here and in GitHub Issues.

## Central-owner takeover for issues #9, #23, and #25

On 22 November 2026, `@Abdullah-SE-bit` explicitly requested that the remaining
work previously allocated to other members be completed by the central owner.
For this completion run, the six use cases, consolidated defect triage, weekly
metrics, package, and technical mock viva are authored and verified under
Abdullah's identity with Codex assistance. The prior three-person distribution
is superseded for these deliverables. Do not add co-author credit or claim that
another member personally reviewed, tested, or rehearsed. The takeover record is
[`evidence/central-takeover-2026-11-22.md`](evidence/central-takeover-2026-11-22.md).
No human oral viva performance is claimed.

Task exception recorded 20 November 2026: the repository owner requested that Phase 1 fixture issue #7 be completed under `@Artfever`. Issue #7 was reassigned from `@TahaSohail-Goat` to `@Artfever` and closed after the fixture evidence merged.

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
| Require status checks to pass | On; live required contexts observed 21 November 2026 are `build`, `sonarqube`, `javascript`, `phase5`, `backup-script`, and `docker-build`. `team-tests` and `mutation` now run on PRs but are not yet required by the live ruleset. |
| Require branches to be up to date before merging | On |
| Block force pushes and deletions | On |
| Bypass list | Empty for the three members, including admins when GitHub permits |

The active ruleset is [SQE main branch CI](https://github.com/Artfever/libris-SQE-Project/rules/27724105), created on 20 November 2026 and updated to remove mandatory reviews, with no bypass actors. The 21 November API read confirmed the six contexts above. The attempted ruleset update was rejected for the connected account, whose repository permission is `write` and `admin` is false. A repository owner/admin must add `team-tests` and `mutation`; until then, do not claim those two contexts are enforced. See [the CI gate demonstration record](evidence/ci-gate-demonstration-2026-11-21.md). The SonarQube job starts an ephemeral Community Build server, analyzes the Java module with JaCoCo coverage, and waits for its quality gate; it needs no repository secret. Keep the ruleset active through the required blocked and passing PR demonstration. The files in this repository document the process; the live GitHub ruleset enforces branch protection.

Live repository settings at setup: Issues enabled; `@TahaSohail-Goat` and `@Abdullah-SE-bit` have write access; squash is the only allowed merge method; merged branches are deleted automatically. Recheck these settings before the final report if they change.
