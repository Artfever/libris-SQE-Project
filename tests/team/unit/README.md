# Team circulation unit verification (#13)

Run from the backend folder with Java 21:

```sh
./mvnw clean test -Dtest=TeamCirculationTest,TeamOverdueCalculatorTest
```

The 30 team cases are in the `com.example.lms.team` test package. This
focused command keeps upstream cases out of the JaCoCo run. Use the
API and browser suites for HTTP binding, authorization, transactions,
and the database postconditions that mocks cannot prove.

| Scope | Instructions | Lines | Branches |
| --- | ---: | ---: | ---: |
| BorrowRecordService | 561/567 | 145/146 | 45/46 |
| OverdueCalculator | 73/73 | 21/21 | 20/20 |
| Total without unreachable code | 634/634 | 166/166 | 65/65 |

JaCoCo reports Java instructions and source lines as coverage proxies.
The raw report marks one branch at line 125 and six instructions at line
136. For an immutable request, the count guard rejects a count other than
one before dispatch. If neither book nor magazine is selected after that
guard, newspaper must be selected. The final fallback is unreachable for
every legitimate request. All reachable scoped instructions and branches
were covered. JaCoCo's raw denominator stays intact.

## Multiple-condition coverage

`itemSelectionMcc` executes the full three-condition table. Each bit
indicates that the corresponding ID is present.

| Mask | Book | Magazine | Newspaper | Exactly one | Expected |
| ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 0 | 0 | 0 | 0 | INVALID_REQUEST |
| 1 | 1 | 0 | 0 | 1 | Borrow book |
| 2 | 0 | 1 | 0 | 1 | Borrow magazine |
| 3 | 1 | 1 | 0 | 0 | INVALID_REQUEST |
| 4 | 0 | 0 | 1 | 1 | Borrow newspaper |
| 5 | 1 | 0 | 1 | 0 | INVALID_REQUEST |
| 6 | 0 | 1 | 1 | 0 | INVALID_REQUEST |
| 7 | 1 | 1 | 1 | 0 | INVALID_REQUEST |

MC/DC pairs for Book, Magazine and Newspaper respectively are 0↔1,
0↔2, and 0↔4. Each pair holds the other two conditions fixed.

For each item type, the availability decision covers missing (no availability
flag to read), present/unavailable, and present/available. Missing and
present/unavailable reject before save. The missing item's flag is
infeasible, so both Boolean values for it are immaterial. The
short-circuit search test covers null, blank, and nonblank search text.
Each record state has success or rejection checks for the applicable
operation, including unknown return records and repeated returns.

| Behavior | Team verification | Traceability |
| --- | --- | --- |
| Selection, missing student/item, availability | Full table and per-type negative cases | FR-B01, FR-B03, FR-B04, BR-C01–BR-C03, PR-01, PR-03, PR-05 |
| Loan dates and borrower snapshots | Default and explicit dates, retained profile, due-date boundary | FR-B05–FR-B06, BR-C05, PR-07, PR-08 |
| Returns and history | Date and availability transition, repeat rejection, orphaned history, status filters and student lookup | FR-R01–FR-R05, BR-C04, PR-04, PR-05, PR-08 |

Execution on Windows, JDK 21, Maven 3.9.11 and JaCoCo 0.8.12.
Surefire reported 30 tests, zero failures, errors or skips. The
[coverage extract](coverage.json) preserves the reported counters and
missed source rows. The first Windows attempt failed before test execution
because Surefire split the Mockito agent at a space in the repository cache
path. Quoting the Java agent argument resolved the problem.

Codex drafted the cases and evidence, ran the focused suite, inspected
JaCoCo data, and corrected the Maven argument quoting. Team review is pending.
