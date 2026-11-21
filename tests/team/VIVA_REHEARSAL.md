# Viva rehearsal and individual verification

This worksheet prepares the Section B viva. It is not evidence that a member
has personally rerun a test, reviewed another member's work, or completed a
rehearsal. Each person should fill their own row after performing the command
and explaining the change prediction without reading the code first.

## Suggested individual exercises

| Member | Selected test | Change-prediction prompt |
| --- | --- | --- |
| Abdullah Adnan (24I-3020) | From `backend`, run `mvnw.cmd test -Dtest=SecurityHardeningTest` with Java 21. | If malformed JSON falls through to the generic exception handler again, which response assertions should fail, and how do the integration checks prove that rejected input did not change availability or history? |
| Muhammad Shaheer (24I-3063) | From the repository root, run `python -u tests/team/usability/run_tasks.py after` after installing `tests/team/usability` dependencies. | If the circulation foreground token is changed to the old low-contrast value, which theme/element should the axe scan flag, and why does the task test also read persisted API state? |
| Taha Sohail (24I-3165) | From the repository root, run `python -u tests/team/browser/run_circulation.py` after installing `tests/team/browser/requirements.txt`. | If the default due-date rule changes from 14 days to 7, which borrow flows and persisted-date assertions should change, and which explicit-due-date flow should remain unaffected? |

## Member completion records

Complete one row per member. Record the actual output and commit link; do not
copy another person's result or use this worksheet as proof of a run that did
not happen.

| Member | Date and commit | Exact test command and result | Predicted change and observed effect | Review / explanation |
| --- | --- | --- | --- | --- |
| Abdullah Adnan (24I-3020) | Pending member entry | Pending member rerun | Pending member explanation | Pending |
| Muhammad Shaheer (24I-3063) | Pending member entry | Pending member rerun | Pending member explanation | Pending |
| Taha Sohail (24I-3165) | Pending member entry | Pending member rerun | Pending member explanation | Pending |

The code-level regression suite passed in CI and a local Java 21 `clean verify`
passed 210 tests with the JaCoCo gate. Those results establish automated test
evidence; they do not substitute for these personal viva entries.
