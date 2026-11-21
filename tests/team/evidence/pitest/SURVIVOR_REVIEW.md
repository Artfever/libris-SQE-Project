# Phase 4 PIT survivor review (#17)

The calibration suite `TeamMutationCalibrationTest` intentionally asserts only that one book borrow returns a non-null response. It is **not** a quality gate. PIT gave 14 surviving, executed mutants under this weak suite. The full team suite killed all 14. The full suite also has two equivalent survivors in `OverdueCalculator`, for 16 survivors inspected across the two runs. Raw results: [calibration](calibration-mutations.xml) and [full](phase4-mutations.xml).

Full scope: 74 mutants, 72 killed, 2 survived, score 97.3% (90% gate). No `RUN_ERROR` or `NO_COVERAGE`. PIT 1.19.4, JUnit 5 plugin 1.2.3, Java 21, `h2` only for the separate recovery test. Both custom BR-C01 and BR-C05 operators were killed.

| # | Class:line | Mutation | Classification | Full-suite result / evidence |
| ---: | --- | --- | --- | --- |
| 1 | `BorrowRecordService.borrow:102` | BR-C05: default due date uses thirteen days | Weak assertion in calibration smoke test | KILLED by `itemSelectionMcc(int)` |
| 2 | `BorrowRecordService.borrow:89` | removed conditional - replaced equality check with false | Weak assertion in calibration smoke test | KILLED by `itemSelectionMcc(int)` |
| 3 | `BorrowRecordService.borrow:102` | removed conditional - replaced equality check with false | Weak assertion in calibration smoke test | KILLED by `itemSelectionMcc(int)` |
| 4 | `BorrowRecordService.borrow:110` | removed conditional - replaced equality check with false | Weak assertion in calibration smoke test | KILLED by `unavailableItemStopsBorrow(com.example.lms.team.TeamCirculationTest$Kind)` |
| 5 | `BorrowRecordService.borrow:98` | removed call to com/example/lms/entity/BorrowRecord::setBorrowerName | Weak assertion in calibration smoke test | KILLED by `itemSelectionMcc(int)` |
| 6 | `BorrowRecordService.borrow:99` | removed call to com/example/lms/entity/BorrowRecord::setBorrowerEmail | Weak assertion in calibration smoke test | KILLED by `itemSelectionMcc(int)` |
| 7 | `BorrowRecordService.borrow:100` | removed call to com/example/lms/entity/BorrowRecord::setBorrowerPhone | Weak assertion in calibration smoke test | KILLED by `itemSelectionMcc(int)` |
| 8 | `BorrowRecordService.borrow:101` | removed call to com/example/lms/entity/BorrowRecord::setBorrowDate | Weak assertion in calibration smoke test | KILLED by `itemSelectionMcc(int)` |
| 9 | `BorrowRecordService.borrow:102` | removed call to com/example/lms/entity/BorrowRecord::setDueDate | Weak assertion in calibration smoke test | KILLED by `itemSelectionMcc(int)` |
| 10 | `BorrowRecordService.borrow:112` | removed call to com/example/lms/entity/Book::setAvailable | Weak assertion in calibration smoke test | KILLED by `itemSelectionMcc(int)` |
| 11 | `BorrowRecordService.borrow:113` | removed call to com/example/lms/entity/BorrowRecord::setBook | Weak assertion in calibration smoke test | KILLED by `itemSelectionMcc(int)` |
| 12 | `BorrowRecordService.borrow:141` | removed call to org/springframework/context/ApplicationEventPublisher::publishEvent | Weak assertion in calibration smoke test | KILLED by `itemSelectionMcc(int)` |
| 13 | `BorrowRecordService.response:212` | removed conditional - replaced equality check with false | Weak assertion in calibration smoke test | KILLED by `routesStaffHistorySearchAndFilters()` |
| 14 | `BorrowRecordService.response:241` | removed conditional - replaced equality check with false | Weak assertion in calibration smoke test | KILLED by `itemSelectionMcc(int)` |
| 15 | `OverdueCalculator.daysOverdue:35` | Remove null-record guard | Equivalent | SURVIVED: a null record flows to `effectiveDueDate(null)`, which returns null; both original and mutant then return false/zero. |
| 16 | `OverdueCalculator.isOverdue:22` | Remove null-record guard | Equivalent | SURVIVED: a null record flows to `effectiveDueDate(null)`, which returns null; both original and mutant then return false/zero. |

The weak suite misses BR-C01 item selection, BR-C05 due-date defaults, item availability, borrower snapshots, audit publication, response type/status and history branches. The full team tests assert those outcomes and kill all 14 killable calibration survivors. The two null-guard survivors are equivalent for this implementation and are retained in the 90% threshold denominator. The raw XML records exact mutant indexes and killing tests.
