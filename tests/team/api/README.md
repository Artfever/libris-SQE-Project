# Circulation OpenAPI and generated test data

For issue #15, this OpenAPI 3.0.3 JSON contract covers the two selected circulation write endpoints. It was drafted from `BorrowRequest`, `BorrowRecordController`, `BorrowRecordService`, `SecurityConfig` and the exception handlers. The exactly-one-item rule and the existence/availability of records are service rules, documented as service rules. The contract records the exactly-one-item boundary in the x-non-null-count extension, which the generator reads. The DTO accepts borrower contact fields but the service uses the student profile instead. No numeric identifier minimum or date-order constraint is asserted by the source; do not mistake synthetic demo constraints for actual application rules.

Generate candidate field partitions and three-point boundary values for declared integer and string length limits:

```powershell
python tests/team/api/generate_cases.py tests/team/api/openapi.json --output tests/team/api/generated-cases.json
python -m unittest discover -s tests/team/api -p 'test_*.py' -v
python tests/team/api/demo_constraint_changes.py
```

The generated JSON describes every input partition in the selected contract that the two circulation endpoints expose. `schema_expected` is an OpenAPI schema classification, not a measured server response; the H2 integration suite consumes generated request-body, field, path, and item-count cases and asserts the HTTP result plus persisted state. `$omit` means the field or whole request body is omitted. Required request bodies also generate omitted-body and JSON-null cases. Malformed JSON, empty bodies, non-object JSON, wrong media type, authentication, CSRF, persistence existence, availability, and state transitions are additional explicit API cases because they are not property-schema partitions.

For this contract, equivalence partitions include required/optional, omitted/null, valid and wrong-type primitive values, valid/invalid ISO dates, the integer `int64` domain, and the exactly-one-item rule. The generator emits just-below/at/just-above cases at both signed `int64` limits and at both item-count limits (0, 1, 2). Those are the actual declared/format limits; the spec has no string-length or date-order business limit to test. The application’s 14-day default due date is separately checked as a business rule, and explicit due dates are tested as supplied. No artificial limits are added to the real contract.

The current generated file contains 80 candidates: 68 body cases, 10 return-path ID cases, and two required-body presence cases. The generator supports the primitive request schemas and constraints present here, including integer inclusive bounds and string `minLength`/`maxLength` when declared. It fails loudly on unsupported validation keywords, formats, and exclusive numeric bounds rather than silently omitting their partitions. Composite schemas and other OpenAPI features are outside these two endpoints’ current request contract; if the spec adds one, generation fails or the new constraint must be implemented and tested before the contract change is accepted. The current generated-data integration suite executes every generated input case and compares complete catalogue/loan snapshots after rejection, while successful cases read back the created and returned records.

`constraint-change-demo.json` is reproducible output from two **hypothetical** schema changes: `studentId.minimum = 2` and `borrowerName.maxLength = 3`. It records the before/after generated partition sets and demonstrates the three points for each new limit. These are demonstration inputs, not current application validations; the API runtime suite does not claim the unmodified application enforces them.

## Initial local integration smoke test

Build the app using Java 21 and the Maven wrapper, then run the generated-data smoke script from the repository root:

```powershell
cd backend
.\mvnw.cmd -DskipTests package
cd ..
python tests/team/api/run_generated_smoke.py
```

The script launches a fresh disposable H2 application on loopback port 18082 with generated private credentials, seeds synthetic data, checks generated required-field rejections and the three item-count values (0, 1, 2). For rejected requests it checks availability and history. The one-item case uses a generated date and exercises borrow and return. This is the smaller smoke suite; the full `run_circulation_integration.py` suite below executes every generated field and path partition plus all item combinations, business-rule outcomes, security cases, and state transitions. The smoke runner refuses to start if the port is occupied. Do not use real or production data.

## Traceability and progress

- Generator and four required-field rejection cases: FR-B02, PR-05.
- Item count boundary: FR-B03, BR-C01, PR-03.
- Success and read-back smoke path: FR-B01, FR-B04, FR-R01, FR-R05, BR-C03, BR-C04; PR-01 and PR-08.
- The generator unit tests validate generator behavior only; they are not application test results.
- See the [execution evidence](../evidence/api-smoke-2026-11-21.md) for the generator and H2 results. The broader integration suite for #14 is described below.

On Windows, the bundled `mvnw.cmd` failed in a workspace path containing an apostrophe because it embeds the path in a PowerShell single-quoted string. For a temporary workaround, map the repository root to an unused drive letter and run the wrapper there; remove the mapping afterward. Do not use a drive letter that is already in use. Example, from the repository root:

```powershell
subst Q: (Get-Location).Path
try { cmd /c 'cd /d Q:\backend && call Q:\backend\mvnw.cmd -DskipTests package' }
finally { subst Q: /D }
```

Confirm that `Q:` is free before running this example. Java 21 must be on `PATH` for both Maven and the smoke runner.

## Full circulation integration run (#14)

After building the Java 21 JAR as above, run `python tests/team/api/run_circulation_integration.py` from the repository root. It starts a fresh H2 server on loopback and stops it when finished. The runner loads the contract directly, substitutes real fixture IDs for positive cases, and uses the generated signed 64-bit boundary values for integer binding. The exactly-one-item rule gets all eight selection combinations across book, magazine and newspaper. The complete availability and loan history snapshots are compared around each rejection and expected transition. See [the coverage matrix and findings](../evidence/api-integration-2026-11-21.md).

## MySQL concurrency and conflict verification

Run from the repository root after packaging the Java 21 application. Install
`PyMySQL[rsa]==1.1.2` for the SQL observation connections. On a Docker
workstation use `bash tests/team/api/run_mysql_container.sh output/mysql.json`.
The runner starts a disposable MySQL 8.4 container bound at loopback 13384
with generated credentials and no named volume. It removes its own container
on exit. The runner requires port 18091 for its local app.

For native MySQL, provision a fresh, isolated MySQL 8.4 instance listening
only on loopback, with an empty database and account both called
`libris_sqe`. Grant that account permissions on its disposable schema and
SELECT on `performance_schema.data_locks` and `data_lock_waits`. Set
`LIBRIS_SQE_MYSQL_PASSWORD` privately, then run
`python tests/team/api/run_mysql_concurrency.py --output output/mysql.json`.
Flyway builds the empty schema. Never reuse a shared or live database.
On Windows, use the MySQL ZIP binary distribution and let the harness
provision its own loopback instance:

```powershell
python tests/team/api/run_mysql_native.py --mysql-home 'C:/tools/mysql-8.4' --output output/mysql.json
```

For each catalogue type, a test transaction holds its own fixture row lock
until MySQL confirms that both independent HTTP sessions are waiting. Once
released, exactly one borrow succeeds. A second race on the loan record
confirms that only one return succeeds. The same runner holds a lock past
the test-only timeout to verify HTTP 409 and unchanged persisted state
for each operation. The application uses its normal service, controller
and migrations. See the [observed results](../evidence/mysql-concurrency-2026-11-26.json).
