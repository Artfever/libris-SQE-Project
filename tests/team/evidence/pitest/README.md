# PIT mutation gate baseline

Run from `backend` on Java 21:

```powershell
.\mvnw.cmd -B test-compile org.pitest:pitest-maven:1.19.4:mutationCoverage
```

The Maven configuration targets only `BorrowRecordService` and
`OverdueCalculator`, using team-owned tests in `com.example.lms.team`. The
initial run on the current PR changes generated 72 mutants; team tests killed
72 (100% mutation score), with 99% line coverage in mutated classes and zero
mutants with no test coverage. The CI floor is 90% mutation score and 90%
mutation coverage. The raw PIT XML is `mutations.xml`.

The first calibration run exposed survivors in the student history page return
and return audit description. The team tests now assert the returned page,
status-specific repository selection, and audit description; the rerun killed
all 72 mutants. Overall application verification separately passed 206 tests
and the existing 70% JaCoCo bundle gate. These are separate measurements.

Environment: JetBrains Runtime (JBR) 21.0.11, Maven Wrapper 3.9.11, PIT 1.19.4,
pitest-junit5-plugin 1.2.3. The scan is limited to service/domain logic and is
not an application-wide mutation score.
