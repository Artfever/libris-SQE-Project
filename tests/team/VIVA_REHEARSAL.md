# Centralized mock viva and verification

On 22 November 2026, Abdullah Adnan (`@Abdullah-SE-bit`, 24I-3020) directed a
single-owner takeover of the outstanding work previously allocated to the
other members. The following commands were run by Codex for Abdullah against
repository source commit `b73456450a3bb53b8050237e8384d66d0f335ff4`. The test
results and predicted effects are central technical evidence, not individual
member records. AI assistance is disclosed in `AI_USE.md`.

## Executed test selection

Environment: Windows 11, JetBrains Runtime Java 21.0.11, Maven Wrapper 3.9.11,
Python 3.14.6, Chromium 159.0.8154.6, disposable H2 fixtures.

| Test area | Exact command | Result |
|---|---|---|
| API validation and security | From `backend`: `mvnw.cmd clean verify` | 210 tests passed; 0 failures/errors/skips; `BUILD SUCCESS`; JaCoCo gate met. `SecurityHardeningTest`: 26 tests passed. |
| API and persisted state | From repository root: `python -u tests/team/api/run_circulation_integration.py` | 7 tests passed; rejected cases preserved availability and history. |
| Six browser use cases | From repository root: `python -u tests/team/browser/run_circulation.py` | 30 tests passed across UC-01 through UC-06. |
| Accessibility and task flow | From repository root: `python -u tests/team/usability/run_tasks.py after` | 2 tasks passed; five axe states reported zero violations; final book availability was true and loan history count was one. |

## Mock viva prompts and model answers

### Malformed API input

**Prompt:** If malformed JSON again falls through to the generic exception
handler, which checks should fail, and how do we know a rejected request did
not alter circulation state?

**Prediction:** The API and security regression checks should fail if malformed
borrow bodies or nonnumeric return IDs produce 500 responses instead of
structured `400 INVALID_REQUEST` / `400 INVALID_ARGUMENT`. They snapshot all
fixture item availability and loan history before and after rejection and
assert equality.

**Observed:** The fresh seven-test H2 API integration run and full 210-test Java
verification passed, including those structured responses and unchanged-state
assertions.

### Contrast and accessible task outcomes

**Prompt:** If the earlier low-contrast foreground token is restored, what
should the accessibility check flag, and why do task tests read API state?

**Prediction:** Axe should report `color-contrast` for affected text or controls
in the impacted theme. The task's API read-back independently proves that a
visually successful action also persisted the expected availability and loan
history transition.

**Observed:** Axe reported zero violations in borrow, borrow-light, borrow
modal, return, and return-light. The task run read back one returned record and
an available book.

### Due-date rule change

**Prompt:** If the default due-date rule changes from 14 to 7 days, which
assertions change, and which flow should remain unaffected?

**Prediction:** Omitted-date cases should expect seven days and the existing
default-date assertions should fail until updated. The explicit-due-date flow
should continue to persist the supplied date unchanged.

**Observed:** The fresh API integration and six-flow browser runs passed with
the current 14-day default and explicit-date cases.

## Attribution boundary

This is a Codex-run, AI-assisted technical mock rehearsal prepared under
Abdullah's direction. It does not claim that Abdullah or another student
personally performed an oral rehearsal. No result or explanation is attributed
to Muhammad Shaheer or Taha Sohail. A human viva examiner can use the prompts
and answers for subsequent live practice.
