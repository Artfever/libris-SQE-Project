# Local test environment (Windows)

Recorded 20 November 2026. Repository commit: `faf2bc0d28b68d4c8ff8c0ffb0fcf5bb87d42804`; upstream `main` matched this commit when checked.

## Ready

- Java: Eclipse Temurin JDK 21.0.13 at `C:\Program Files\Eclipse Adoptium\jdk-21.0.13.9-hotspot`.
- Maven: bundled wrapper 3.9.11 (`backend\mvnw.cmd`); no separate Maven installation needed.
- Node.js: 24.18.0. Python: 3.12.10.
- Baseline: from `backend`, `mvnw.cmd clean verify` passed, 176 upstream tests, zero failures/errors/skips, and the configured JaCoCo check. Overall line coverage was 1425/1578 (90.3%); `BorrowRecordService` was 145/146 lines and 42/46 branches. These are upstream baseline results, not team test results.
- Docker CLI and Compose are installed; the Docker engine was unavailable during setup. The initial H2/JUnit work does not require it.

## Reproduce the baseline

Open a new PowerShell terminal so it reads the installed Java environment. From the repository root:

```powershell
cd backend
.\mvnw.cmd -version
.\mvnw.cmd clean verify
```

If an existing terminal still cannot find Java, set its process environment first:

```powershell
$env:JAVA_HOME = 'C:\Program Files\Eclipse Adoptium\jdk-21.0.13.9-hotspot'
$env:Path = "$env:JAVA_HOME\bin;$env:Path"
```

## Run the local application

The `h2` profile is suitable for initial API and browser tests. Supply a unique local `LMS_ADMIN_PASSWORD` through a private prompt or secret manager, then run from `backend`:

```powershell
.\mvnw.cmd spring-boot:run '-Dspring-boot.run.profiles=h2'
```

Visit `http://localhost:8080`; the local admin username is `admin`. H2 data is erased when the app stops, which is the reset procedure for disposable fixtures. The live app health check was not completed during this setup, so verify it before recording browser/API results.

For MySQL-specific integration, start a local Docker engine and follow `docs/SETUP.md`. Use separate disposable credentials and data. The repository's Compose file selects the production profile, whose secure cookies require HTTPS for a working browser login; plan the browser suite around H2 or a reviewed local non-production configuration.
