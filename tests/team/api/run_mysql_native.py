"""Start a disposable MySQL 8.4 binary distribution for circulation tests."""

import argparse
import os
import secrets
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pymysql

from run_mysql_concurrency import DATABASE, JAR, stop_app
from verify_h2 import port_is_open


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mysql-home", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mysql-port", type=int, default=13384)
    args = parser.parse_args()
    installation = args.mysql_home.resolve()
    server = installation / "bin" / ("mysqld.exe" if os.name == "nt" else "mysqld")
    if not server.is_file() or not JAR.is_file() or port_is_open(args.mysql_port):
        parser.error("Use a MySQL 8.4 binary distribution, a built JAR, and a free port")

    password = secrets.token_urlsafe(30)
    root_password = secrets.token_urlsafe(30)
    state = Path(tempfile.mkdtemp(prefix="libris-sqe-native-mysql-"))
    options = [str(server), "--no-defaults", f"--basedir={installation}", f"--datadir={state / 'db'}"]
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    with (state / "initialize.log").open("wb") as log:
        subprocess.run(options + ["--initialize-insecure"], stdout=log,
                       stderr=subprocess.STDOUT, creationflags=flags, check=True)
    bootstrap = state / "bootstrap.sql"
    bootstrap.write_text(
        f"ALTER USER 'root'@'localhost' IDENTIFIED BY '{root_password}';\n"
        f"CREATE DATABASE {DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;\n"
        f"CREATE USER '{DATABASE}'@'127.0.0.1' IDENTIFIED BY '{password}';\n"
        f"GRANT ALL ON {DATABASE}.* TO '{DATABASE}'@'127.0.0.1';\n"
        f"GRANT SELECT ON performance_schema.data_lock_waits TO '{DATABASE}'@'127.0.0.1';\n"
        f"GRANT SELECT ON performance_schema.data_locks TO '{DATABASE}'@'127.0.0.1';\n",
        encoding="ascii",
    )
    process = None
    try:
        with (state / "server.log").open("wb") as log:
            process = subprocess.Popen(
                options + [f"--port={args.mysql_port}", "--bind-address=127.0.0.1",
                           "--mysqlx=OFF", f"--init-file={bootstrap}"],
                stdout=log, stderr=subprocess.STDOUT, creationflags=flags,
            )
            wait_until_ready(process, args.mysql_port, password, state)
        bootstrap.unlink()
        subprocess.run(
            [sys.executable, str(Path(__file__).with_name("run_mysql_concurrency.py")),
             "--mysql-port", str(args.mysql_port), "--output", str(args.output)],
            env={**os.environ, "LIBRIS_SQE_MYSQL_PASSWORD": password}, check=True,
        )
    finally:
        stop_app(process)
        bootstrap.unlink(missing_ok=True)
    print(f"Stopped disposable MySQL. Local logs and data: {state}")


def wait_until_ready(process, port, password, state):
    for _ in range(60):
        if process.poll() is not None:
            break
        try:
            with pymysql.connect(host="127.0.0.1", port=port, user=DATABASE,
                                 password=password, database=DATABASE, connect_timeout=1):
                return
        except (OSError, pymysql.MySQLError):
            time.sleep(1)
    raise RuntimeError(f"Disposable MySQL did not initialize. Inspect {state} locally.")


if __name__ == "__main__":
    main()
