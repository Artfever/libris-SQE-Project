# Local test environment (Windows)

Recorded 20 November 2026. Upstream baseline commit: `faf2bc0d28b68d4c8ff8c0ffb0fcf5bb87d42804`; upstream `HEAD` matched this commit on 20 November 2026. The upstream repository is https://github.com/prathamkashyap/libris and its `LICENSE` at that commit is MIT. The team fork includes later setup and CI commits; keep the upstream baseline separate from those changes.

## Ready

- Java: Eclipse Temurin JDK 21.0.13 at `C:\Program Files\Eclipse Adoptium\jdk-21.0.13.9-hotspot`.
- Maven: bundled wrapper 3.9.11 (`backend\mvnw.cmd`); no separate Maven installation needed.
- Node.js: 24.18.0. Python: 3.12.10.
- Docker CLI: 29.9.2. Docker Compose: 5.6.1. `docker info` failed because the Docker Desktop Linux engine pipe was absent. A MySQL run is pending until the engine is available.
- Clean verification: from `backend`, `mvnw.cmd spotless:check clean verify` passed with 176 upstream tests, zero failures/errors/skips, and the configured JaCoCo check. Overall line coverage was 1425/1578 (90.3%); `BorrowRecordService` was 145/146 lines and 42/46 branches. These are upstream baseline results, not team test results.
- H2 startup: `spring-boot:run` with the `h2` profile and a private generated admin password started successfully on port 18080. `GET /actuator/health` returned `UP`; `GET /login.html` returned HTTP 200. The process was stopped and the port closed. See [the dated baseline evidence](evidence/baseline-2026-11-20.md).

## Reproduce the baseline

Open a new PowerShell terminal so it reads the installed Java environment. From the repository root:

```powershell
cd backend
.\mvnw.cmd -version
.\mvnw.cmd spotless:check clean verify
```

If an existing terminal still cannot find Java, set its process environment first:

```powershell
$env:JAVA_HOME = 'C:\Program Files\Eclipse Adoptium\jdk-21.0.13.9-hotspot'
$env:Path = "$env:JAVA_HOME\bin;$env:Path"
```

## Run the local application

The `h2` profile is suitable for initial API and browser tests. Supply a unique local `LMS_ADMIN_PASSWORD` through a private prompt or secret manager, then run from `backend`:

```powershell
.\mvnw.cmd spring-boot:run '-Dspring-boot.run.profiles=h2' '-Dspring-boot.run.arguments=--server.servlet.session.cookie.secure=false'
```

Visit `http://localhost:8080/login.html`; the local admin username is `admin`. The root path requires authentication and may return HTTP 401 to an anonymous request. Check `http://localhost:8080/actuator/health` for `UP`. H2 uses an in-memory database with `spring.jpa.hibernate.ddl-auto=create-drop`; stopping and restarting the app resets disposable fixtures. The admin account is recreated by `AdminSeeder` at startup. Record fixture creation separately when the team begins scenario testing.

The local H2 command overrides Secure session cookies because it uses loopback HTTP. The inherited `server.servlet.session.cookie.secure=true` otherwise allows a login response but prevents the browser or API client from returning the session cookie over HTTP. Keep Secure cookies enabled for HTTPS and production.

For the Phase 1 circulation fixture, follow [the fixture and reset guide](fixtures/README.md). It creates one synthetic student and one available item of each type through the authenticated API, then checks persisted state and empty loan history.

For MySQL-specific integration, start a local Docker engine and follow `docs/SETUP.md`. Use separate disposable credentials and data. The repository's Compose file selects the production profile, whose secure cookies require HTTPS for a working browser login; plan the browser suite around H2 or a reviewed local non-production configuration.
