# CI gate demonstration (#22)

Snapshot: 21 November 2026. All changes use pull requests and the active
`main` ruleset; no check was skipped or bypassed. Links below point to the
public PRs and Actions runs.

## Passing quality-gate PR

- [PR #37](https://github.com/Artfever/libris-SQE-Project/pull/37) merged by
  squash as `e2b89dbe63bfffecefbacbc784cc7dcf057c6d0d`.
- [Run 44909720621](https://github.com/Artfever/libris-SQE-Project/actions/runs/44909720621)
  passed `build`, `javascript`, `phase5`, `backup-script`, `docker-build`,
  `sonarqube`, `team-tests`, and `mutation`. The team test job ran the focused
  Java tests/coverage, API generator, H2 smoke/integration, and browser flows;
  the mutation job reported 72/72 mutants killed.
- This is a passing PR demonstrating the configured gates. The PR added the
  workflows and coverage/mutation thresholds; it did not change the live
  ruleset contexts.

## Deliberately blocked regression PR

- [PR #42](https://github.com/Artfever/libris-SQE-Project/pull/42) is
  intentionally retained open and unmerged. Commit
  `5424223d0b6768ea8d37d1e1603806a34ebcc079` adds the malformed-input
  regression expectations without the production handler.
- [Run 44910758989](https://github.com/Artfever/libris-SQE-Project/actions/runs/44910758989)
  failed the required Maven `build`: `SecurityHardeningTest` expected
  `400 INVALID_ARGUMENT`, but the baseline handler returned 500. Maven reported
  206 tests, one failure. The `team-tests` job also failed during fixture setup
  because the disposable H2 launcher attempted admin login before
  `AdminSeeder` finished. These are distinct failures: the first is the
  intentional red regression; the second exposed a test-harness readiness race.
- At the failure snapshot GitHub marked the PR blocked. It remains open; after
  main advanced with the fix, it is also behind the base. It has not been
  force-merged or bypassed.

## Corrective passing PR

- [PR #41](https://github.com/Artfever/libris-SQE-Project/pull/41) added
  sanitized `400` handlers for unreadable request bodies and invalid path
  arguments, contract updates, state-preserving regression cases, and a
  readiness wait for admin seeding in the H2 launcher.
- [Run 44911315628](https://github.com/Artfever/libris-SQE-Project/actions/runs/44911315628)
  passed all 8 checks, including `build`, `sonarqube`, `team-tests`,
  `mutation`, and the dual-architecture Docker build. The local Java 21
  `clean verify` passed 206 project tests; the focused circulation HTTP suite
  passed 7 tests. PR #41 merged as
  `140c791bf372046797398a78ee9e06ad3893bb13`; defects #38 and #39 closed.
- After rebasing PR #40 on PR #41, [run 44912655691](https://github.com/Artfever/libris-SQE-Project/actions/runs/44912655691)
  passed all 8 checks, including generated smoke, API integration, and browser
  tests. This confirms the readiness fix removed the prior admin-seed race.

## Live enforcement and deployment boundary

The active ruleset `SQE main branch CI` currently requires six contexts:
`build`, `javascript`, `phase5`, `backup-script`, `docker-build`, and
`sonarqube`. The new `team-tests` and `mutation` checks ran and passed in PR #37
and PR #41, but they are not required by the live ruleset. The ruleset update
attempt returned HTTP 404; the connected account is a write collaborator, not
an admin. A repository owner/admin still needs to add those two contexts before
issue #22 can be considered complete. The blocked and passing PR demonstration
is recorded, but #22 remains open until that admin-only ruleset update is
verified. No bypass was attempted.

There is no deployment job in this repository. The required checks gate merges
to `main`; CI builds Docker images for `linux/amd64` and `linux/arm64` without
publishing or deploying them. Therefore there is no automated deployment path
for the quality jobs to gate.
