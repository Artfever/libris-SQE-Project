# Circulation OpenAPI and generated test data

For issue #15, this OpenAPI 3.0.3 JSON contract covers the two selected circulation write endpoints. It was drafted from `BorrowRequest`, `BorrowRecordController`, `BorrowRecordService`, `SecurityConfig` and the exception handlers. The exactly-one-item rule and the existence/availability of records are service rules, documented as service rules. The contract records the exactly-one-item boundary in the x-non-null-count extension, which the generator reads. The DTO accepts borrower contact fields but the service uses the student profile instead. No numeric identifier minimum or date-order constraint is asserted by the source; do not mistake synthetic demo constraints for actual application rules.

Generate candidate field partitions and three-point boundary values for declared integer and string length limits:

```powershell
python tests/team/api/generate_cases.py tests/team/api/openapi.json --output tests/team/api/generated-cases.json
python -m unittest discover -s tests/team/api -p 'test_*.py' -v
python tests/team/api/demo_constraint_changes.py
```

The generated JSON describes individual field partitions and the non-null item count rule. `schema_expected` is an OpenAPI schema classification, not a measured server response: actual behavior also depends on other fields, persistent IDs, business rules, Jackson coercion, authentication and CSRF. `$omit` indicates that a field must be omitted, not sent literally. Date-format cases are generated, but their runtime response still requires verification. No artificial limits are imposed on the real spec merely to create boundary cases. The current generator supports integer inclusive minimum/maximum and string minLength/maxLength, date and primitive type/null/omission cases; it deliberately fails on unsupported exclusive bounds. It does not yet exhaustively handle all OpenAPI constraints, composite schemas, all invalid types, or other cross-field business rules. Expand it and the API suite before claiming EP/BVA coverage.

`constraint-change-demo.json` is reproducible output from two **hypothetical** changes: `studentId.minimum = 2` and `borrowerName.maxLength = 3`. These are not current application validations. The output shows before and after partitions and BVA. Actual API tests must not assume the changed constraints are enforced until the application itself is changed.

## Initial local integration smoke test

Build the app using Java 21 and the Maven wrapper, then run the generated-data smoke script from the repository root:

```powershell
cd backend
.\mvnw.cmd -DskipTests package
cd ..
python tests/team/api/run_generated_smoke.py
```

The script launches a fresh disposable H2 application on loopback port 18082 with generated private credentials, seeds synthetic data, checks four generated required-field rejections and the three generated item-count values (0, 1, 2). For rejected requests it checks availability and history. The one-item case uses a generated date and exercises borrow and return. It stops the application afterwards. It is an initial smoke test, **not** full API coverage; ID existence, all item combinations, remaining input classes, dates, roles, CSRF, repeated requests, decision tables and state transitions still need tests and evidence. It refuses to start if the port is occupied. Do not use real or production data.

## Traceability and progress

- Generator and four required-field rejection cases: FR-B02, PR-05.
- Item count boundary: FR-B03, BR-C01, PR-03.
- Success and read-back smoke path: FR-B01, FR-B04, FR-R01, FR-R05, BR-C03, BR-C04; PR-01 and PR-08.
- The generator unit tests validate generator behavior only; they are not application test results.
- See the [execution evidence](../evidence/api-smoke-2026-11-21.md) for the generator and H2 results. The full API suite and remaining workflow cases are tracked in #14.

On Windows, the bundled `mvnw.cmd` failed in a workspace path containing an apostrophe because it embeds the path in a PowerShell single-quoted string. For a temporary workaround, map the repository root to an unused drive letter and run the wrapper there; remove the mapping afterward. Do not use a drive letter that is already in use. Example, from the repository root:

```powershell
subst Q: (Get-Location).Path
try { cmd /c 'cd /d Q:\backend && call Q:\backend\mvnw.cmd -DskipTests package' }
finally { subst Q: /D }
```

Confirm that `Q:` is free before running this example. Java 21 must be on `PATH` for both Maven and the smoke runner.
