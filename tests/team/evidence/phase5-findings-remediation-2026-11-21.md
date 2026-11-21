# Phase 5 remediation of Phase 4 findings

Snapshot: 21 November 2026. Findings #44–#47 were assigned to
`@Abdullah-SE-bit` after Phase 4 evidence was merged in PR #43. All checks in
this file use a disposable H2 database, synthetic accounts, and local tooling.
These results do not establish production behavior or MySQL concurrency.

## #44 — UX-02 contrast

- **Triage:** Medium, P2; usability/accessibility; risk PR-10. The failing text
  used low-contrast faint-text tokens on dark surfaces and white text on the
  green primary action. The light theme reused an accent too bright for text.
- **Fix:** Raised text contrast tokens, paired theme-specific accent colors
  with a matching foreground token, and applied those tokens to active
  navigation and primary actions. Keyboard focus styles remain visible.
- **Verification:** Axe-core 4.14.1 reported zero violations on the borrow
  screen, borrow dialog, and return screen in both dark and light themes.
  Lighthouse accessibility scored 90 on borrow and return in both themes.
  The Playwright workflow also checked the rendered borrow/return result and
  persisted state.

## #45 — UX-03 accessible names

- **Triage:** Medium, P2; accessibility; risk PR-10. `aria-label` on the brand
  and profile links replaced their visible text in the computed accessible
  name, so voice control could not use the visible wording.
- **Fix:** Removed redundant overriding labels from the visible brand and
  profile links. Kept the icon-only profile control named `Profile`.
- **Verification:** Axe-core reported zero label/content-name mismatch
  violations on borrow, borrow dialog, and return in both themes.

## #46 — CSP and external stylesheet

- **Triage:** Medium, P2; security; risk PR-11. The application had no
  Content-Security-Policy response header and loaded Google Fonts CSS without
  integrity metadata.
- **Fix:** Added a CSP to Spring Security responses (`default-src 'self'`,
  same-origin form/base/connect/font/image sources, `object-src 'none'`, and
  `frame-ancestors 'self'`, `script-src 'self'`, and `style-src 'self'`).
  Removed the third-party Google Fonts stylesheet and its preconnects from
  static pages and Swagger theme CSS; system font fallbacks are used. Moved
  repeated first-paint scripts/styles, inline styles, and dynamic style
  mutations to same-origin assets and CSS classes, so the policy does not need
  `unsafe-inline`.
- **Verification:** `SecurityHardeningTest.responsesIncludeRestrictiveContentSecurityPolicy`
  passed in the full Java 21 suite (210 tests total; JaCoCo gate met). The
  six-flow Playwright suite passed all 30 cases. Axe reported zero violations
  on borrow, borrow modal, and return in dark and light themes. ZAP 2.17.0
  first proxied 52 messages through a successful borrow/return and reported
  eight medium `unsafe-inline` CSP alerts plus three informational alerts.
  After the policy and static assets were hardened, a second 52-message passive
  scan reported three informational alerts only, with no missing-CSP, SRI, or
  unsafe-inline alerts. Sanitized evidence is in
  `security/zap-passive-2026-11-21-postfix.json` and
  `security/zap-passive-2026-11-21-csp-hardening.json`; no active scan ran.

## #47 — Maven advisory triage

- **Triage:** High for initial review, P1; security; risk PR-11. The original
  OSV inventory checked 137 resolved packages and found IDs in 20 packages.
  No exploit was demonstrated.
- **Fix:** Upgraded Spring Boot from 3.5.0 to supported 3.5.16 and pinned
  affected managed components to fixed stable releases: Jackson 2.21.7,
  Log4j 2.25.5, Tomcat 10.1.61, and Commons Lang 3.18.0. Spring Boot 3.5.16
  is the latest 3.5.x release documented by Spring at this snapshot.
- **Verification:** Full `clean verify` passed on Java 21 after the upgrades:
  210 tests, no failures/errors/skips, with the JaCoCo gate met. The refreshed
  OSV audit checked 137 packages; only two IDs remain, both on Spring MVC
  6.2.19. They concern SSE fragment-stream corruption and XSLT view path
  limitation. Source review found no WebFlux/SSE, fragment rendering, or
  `XsltView` usage; this application serves static HTML and REST controllers.
  They are recorded as not applicable to the exercised application paths,
  rather than hidden or treated as fixed. The stable Spring 6.2 line remains
  at 6.2.19; the next release was still a snapshot. Reassess when a stable
  patch is available or if these features are introduced.

## Change and evidence links

Contrast, accessible-name, CSP baseline, and dependency upgrades are in merged
[PR #48](https://github.com/Artfever/libris-SQE-Project/pull/48). The CSP
hardening and post-fix scan evidence are submitted for review in PR #50. Raw
browser results are in `usability/tasks-after.json`, `usability/axe-*-after.json`,
and the Lighthouse JSON files. The refreshed OSV inventory is
`security/osv-2026-11-21-postfix.json`; the resolved dependency tree is
`security/dependency-tree-2026-11-21.json`. The pre-fix inventory and original
report remain available for comparison.
