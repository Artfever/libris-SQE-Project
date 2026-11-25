"""Run the circulation fixture against a fresh H2 app, then prove restart reset."""

import argparse
import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

from circulation import Api, inspect, require_empty, seed, write_json


ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend"
JAR = BACKEND / "target" / "libris-0.0.1-SNAPSHOT.jar"


def port_is_open(port):
    with socket.socket() as connection:
        return connection.connect_ex(("127.0.0.1", port)) == 0


def start_app(port, password, *, profile="h2", database_environment=None, extra_args=()):
    if port_is_open(port):
        raise RuntimeError(f"Port {port} is already in use")
    log_path = Path(tempfile.gettempdir()) / f"libris-fixture-{profile}-{port}.log"
    environment = dict(os.environ)
    environment["LMS_ADMIN_PASSWORD"] = password
    environment["LMS_ADMIN_USERNAME"] = "admin"
    if database_environment:
        environment.update(database_environment)
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    with log_path.open("wb") as log:
        process = subprocess.Popen(
            [
                "java",
                "-jar",
                str(JAR),
                f"--spring.profiles.active={profile}",
                f"--server.port={port}",
                "--server.address=127.0.0.1",
                "--server.servlet.session.cookie.secure=false",
                *extra_args,
            ],
            cwd=BACKEND,
            env=environment,
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=flags,
        )
    health_url = f"http://127.0.0.1:{port}/actuator/health"
    for _ in range(60):
        if process.poll() is not None:
            raise RuntimeError(f"App exited during startup; inspect {log_path}")
        try:
            with urllib.request.urlopen(health_url, timeout=1) as response:
                if json.load(response).get("status") == "UP":
                    # Actuator can report UP before ApplicationRunner/CommandLineRunner
                    # initialization finishes. Wait for AdminSeeder before attempting login.
                    if "AdminSeeder: Completed" in log_path.read_text(
                        encoding="utf-8", errors="replace"
                    ):
                        return process
        except (OSError, ValueError, urllib.error.HTTPError):
            pass
        time.sleep(1)
    stop_app(process)
    raise RuntimeError(f"App did not become healthy; inspect {log_path}")


def stop_app(process):
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=18081)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("Choose a local port from 1024 to 65535")
    if not JAR.is_file():
        parser.error("Build backend/target/libris-0.0.1-SNAPSHOT.jar first")
    admin_password = secrets.token_urlsafe(24) + "Aa1!"
    student_password = secrets.token_urlsafe(24) + "Aa1!"
    base_url = f"http://127.0.0.1:{args.port}"
    process = None
    try:
        process = start_app(args.port, admin_password)
        api = Api(base_url)
        api.login(admin_password)
        initial = require_empty(api)
        manifest = seed(api, student_password)
        write_json(args.manifest, manifest)
        readback = inspect(api, manifest)
    finally:
        stop_app(process)
    if port_is_open(args.port):
        raise RuntimeError("App port remained open after stop")
    process = None
    try:
        process = start_app(args.port, admin_password)
        api = Api(base_url)
        api.login(admin_password)
        reset = require_empty(api)
    finally:
        stop_app(process)
    if port_is_open(args.port):
        raise RuntimeError("App port remained open after reset check")
    result = {
        "profile": "h2",
        "initial_counts": initial,
        "seeded": manifest,
        "readback": readback,
        "after_restart_counts": reset,
        "app_stopped": True,
    }
    write_json(args.output, result)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        print(f"H2 fixture verification failed: {error}", file=sys.stderr)
        raise SystemExit(1)
