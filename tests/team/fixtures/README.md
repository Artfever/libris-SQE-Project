# Circulation fixture and reset (issue #7)

This fixture is for a **fresh, disposable local H2 instance**. It uses the application's authenticated API to create one synthetic student and one book, magazine, and newspaper. It refuses to seed if any students, catalog items, or borrow records already exist. It never assumes database IDs. It records server-assigned IDs in a non-secret manifest, checks that all three items are available, and checks that loan history has zero records.

The account password and session/CSRF tokens stay in process memory. No credential is printed or committed. Use a unique private password for the H2 admin and another for the synthetic student. The generated student username is in the manifest so later tests can use it with the private student password. The static input data is in `circulation.json` and uses the reserved `example.invalid` email domain.

## Automated H2 proof

With Java 21 on the path, build the app JAR and run the verifier from the repository root:

```powershell
cd backend
.\mvnw.cmd -q -DskipTests package
cd ..
python tests/team/fixtures/verify_h2.py --output tests/team/evidence/fixture-h2-2026-11-20.json --manifest tests/team/evidence/fixture-h2.local.json
```

The verifier generates private credentials in memory, starts a fresh H2 app on loopback port 18081, checks all counts are zero, seeds the fixture, reads each record back, stops the app, restarts it, checks all counts are zero again, and stops it. It writes a non-secret evidence JSON file and an ignored local manifest. It aborts if the port is already in use. Use `--port` for another free local port. The runner overrides `server.servlet.session.cookie.secure=false` only for this loopback HTTP H2 process so its authenticated session works; the production configuration is untouched.

## Start and seed in PowerShell

From the repository root, set private process environment values using a prompt or secret manager:

```powershell
$env:JAVA_HOME = 'C:\Program Files\Eclipse Adoptium\jdk-21.0.13.9-hotspot'
$env:Path = "$env:JAVA_HOME\bin;$env:Path"
function Read-PrivateValue($prompt) {
  $secret = Read-Host $prompt -AsSecureString
  $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
  try { [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
  finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
}
$env:LMS_ADMIN_PASSWORD = Read-PrivateValue 'Unique local admin password'
$env:SQE_STUDENT_PASSWORD = Read-PrivateValue 'Unique synthetic student password'
cd backend
.\mvnw.cmd spring-boot:run '-Dspring-boot.run.profiles=h2' '-Dspring-boot.run.arguments=--server.servlet.session.cookie.secure=false'
```

In another PowerShell terminal, set the **same** two process environment values privately, return to the repository root, and run:

```powershell
python tests/team/fixtures/circulation.py verify-empty
python tests/team/fixtures/circulation.py seed --output tests/team/evidence/fixture-h2.local.json
python tests/team/fixtures/circulation.py inspect --manifest tests/team/evidence/fixture-h2.local.json
```

`fixture-h2.local.json` contains no secrets but is ignored by Git because IDs and usernames vary by run. The `seed` output itself records zero initial students/items/borrow records and one of each fixture afterward. Each item has `available: true`; `borrow-records` remains zero. The `inspect` command reads each server-assigned ID back through the API and checks the same conditions. Use `--base-url http://127.0.0.1:18081` if the app runs on a different local port. The tool rejects non-local URLs.

## Reset and prove it

Stop the app with Ctrl+C. H2's in-memory database is dropped. Restart the same `h2` command with the admin password and run:

```powershell
python tests/team/fixtures/circulation.py verify-empty
```

Expected counts are zero for students, books, magazines, newspapers, and borrow records. To repeat the fixture, run `seed` again; it creates a fresh synthetic username and uses the new server-assigned IDs. Stop the app when finished. Do not use database deletion, `docker compose down -v`, or a production endpoint for this reset.

## MySQL-specific follow-up

The local Docker CLI is installed, but the Docker Desktop engine was unavailable on 20 November 2026. When it is available, create a disposable local MySQL stack with separate credentials, run the same seed/read-back checks against its loopback-bound app endpoint, and record the result under `tests/team/evidence/`. Do not reset or remove a persistent named volume without confirming it belongs to the disposable test stack. The current script's `verify-empty` and `seed` modes intentionally require an empty database; arrange a dedicated database for the MySQL check.
