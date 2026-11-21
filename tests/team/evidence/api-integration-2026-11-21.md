# Circulation API integration coverage (#14)

The suite uses an H2 application packaged from application source
`0c794c01980cf82a7acbbfa924ff53e920d59ecd`. The application logic is unchanged by
the test branch. Environment: Windows, Temurin Java 21, Maven Wrapper 3.9.11,
and Python 3.15. The [API guide](../api/README.md) has the build and run commands.
GitHub records the committed suite revision in the associated pull request.

| Executable test | Coverage criteria and assertions | Requirements, rules and risks |
| --- | --- | --- |
| Generated request partitions | Exercise every generated JSON body field class. Replace nominal IDs with fixture IDs. Test the three points around both signed 64-bit limits for each applicable field. Within-range fixture misses return 404, and binding failures return 500 on this baseline. | FR-B01–FR-B06, BR-C01, BR-C03, BR-C05, PR-03, PR-05, PR-07, PR-08 |
| Item selection decision table | Execute all eight present/absent combinations. The three one-item combinations succeed. Zero, two and three selections fail with 400. | FR-B01, FR-B03, BR-C01, PR-03 |
| Existence, availability and transitions | For each item type, cover missing, available, and unavailable. Availability has no meaningful value for a missing item. For each loan type, cover borrow, repeat borrow, return, and repeat return. Unknown loan and student IDs return 404. | FR-B04, FR-R01–FR-R03, FR-R05, BR-C02–BR-C04, PR-01, PR-03–PR-05, PR-08 |
| Return path and method | Consume all generated return ID classes and signed 64-bit boundary points. An active fixture ID returns 204 with no body, missing route/records return 404, invalid path ID binding returns 500, and GET on the return route returns 405. | FR-R01, FR-R03, PR-05 |
| Roles and CSRF | For both write endpoints verify anonymous 401 with a valid CSRF token, student 403, and staff 403 when the CSRF header is missing. Verify librarian writes, administrator writes in other tests, and student own-history read-back. | FR-B01, FR-R01, FR-R04–FR-R06, PR-06 |
| Date ordering | Submit explicit due dates one day before, on and one day after the borrow date. All are stored as supplied. Other cases check the 14-day default. Date order is baseline behavior with no stated policy. | FR-B05, BR-C05, PR-07 |

The two write operations are covered using POST. The suite verifies implemented
success statuses 201 and 204 and rejection statuses 400, 401, 403, 404, 405
and 500. The controller advice advertises 409 for pessimistic lock failures.
This run covers sequential repeat requests. A forced lock conflict and MySQL
concurrency remain outside this H2 result. Test counts refer to the six
executable unittest methods, with repeated subcases and assertions reported as
coverage within those methods.

Every rejection compares the complete fixture availability and loan history
before and after the request. Every successful write checks the expected
change while retaining unrelated history and availability. Borrow checks the
Location header, IDs, dates, status and borrower snapshot. Return checks the
empty response, date and retained record.

| Finding | Root cause and severity | Risk and recommended fix |
| --- | --- | --- |
| Malformed body fields or return IDs receive 500 INTERNAL_ERROR. Validly bound but unknown IDs get 404, and Bean Validation failures get 400. | The controller advice has a general Exception handler and lacks specific handlers for JSON read and path argument conversion failures. Medium severity because input mistakes look like server outages and field details are lost. | PR-05. Persisted-state checks passed. Add specific handling for unreadable request bodies and argument type mismatches, return a structured 400, and update the contract and regression tests together. |

Codex drafted the integration tests and this run record in response to
“Complete the work”. Codex compared the assertions against persisted
responses, corrected the active loan date assertion for omitted JSON values,
and reran the suite. Team review is pending.

Raw output from `python tests/team/api/run_circulation_integration.py`:

```text
test_explicit_due_dates_around_borrow_date (__main__.CirculationIntegration.test_explicit_due_dates_around_borrow_date) ... ok
test_generated_body_field_partitions (__main__.CirculationIntegration.test_generated_body_field_partitions) ... ok
test_item_existence_availability_and_return_transitions (__main__.CirculationIntegration.test_item_existence_availability_and_return_transitions) ... ok
test_item_selection_decision_table (__main__.CirculationIntegration.test_item_selection_decision_table) ... ok
test_return_path_partitions_and_wrong_method (__main__.CirculationIntegration.test_return_path_partitions_and_wrong_method) ... ok
test_roles_and_csrf (__main__.CirculationIntegration.test_roles_and_csrf) ... ok

----------------------------------------------------------------------
Ran 6 tests in 43.452s

OK
```
