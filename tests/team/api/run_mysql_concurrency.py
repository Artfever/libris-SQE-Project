"""Verify same-record races and lock timeout recovery in disposable MySQL 8.4."""

import argparse
import json
import os
import secrets
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import date
from pathlib import Path

import pymysql

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fixtures"))
from circulation import Api, seed, write_json
from verify_h2 import JAR, start_app, stop_app

BASE = "http://127.0.0.1:18091"
LOANS = "/api/borrow-records"
DATABASE = "libris_sqe"
KINDS = {"book": "books", "magazine": "magazines", "newspaper": "newspapers"}


def write(api, path, payload=None):
    request = urllib.request.Request(
        BASE + path, method="POST",
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Accept": "application/json", "Content-Type": "application/json",
                 "X-XSRF-TOKEN": api.csrf_token},
    )
    try:
        response = api.opener.open(request, timeout=20)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        data = response.read()
        return response.status, json.loads(data) if data else None


@contextmanager
def hold_row(connection, table, row_id):
    with connection.cursor() as cursor:
        connection.begin()
        try:
            # Table names come only from the fixture's three known table names or borrow_records.
            cursor.execute(f"SELECT id FROM `{table}` WHERE id = %s FOR UPDATE", (row_id,))
            assert cursor.fetchone() == (row_id,)
            yield
        finally:
            connection.rollback()


def waiting_transactions(observer, table, expected):
    deadline = time.monotonic() + 4
    with observer.cursor() as cursor:
        while time.monotonic() < deadline:
            cursor.execute(
                """SELECT COUNT(DISTINCT waits.REQUESTING_ENGINE_TRANSACTION_ID)
                   FROM performance_schema.data_lock_waits AS waits
                   JOIN performance_schema.data_locks AS locks
                     ON locks.ENGINE = waits.ENGINE
                    AND locks.ENGINE_LOCK_ID = waits.REQUESTING_ENGINE_LOCK_ID
                   WHERE locks.OBJECT_SCHEMA = %s AND locks.OBJECT_NAME = %s""",
                (DATABASE, table),
            )
            count = cursor.fetchone()[0]
            if count == expected:
                return count
            time.sleep(0.03)
    raise AssertionError(f"Expected {expected} simultaneous waiters on {table}, observed {count}")


def race(blocker, observer, clients, table, row_id, path, payload=None):
    starting_line = threading.Barrier(len(clients))

    def attempt(client):
        starting_line.wait(timeout=5)
        return write(client, path, payload)

    with ThreadPoolExecutor(max_workers=len(clients)) as executor:
        with hold_row(blocker, table, row_id):
            requests = [executor.submit(attempt, client) for client in clients]
            waiters = waiting_transactions(observer, table, len(clients))
        return [request.result(timeout=20) for request in requests], waiters


def check_database(blocker, observer, clients, fixture):
    staff = clients[0]
    student = fixture["student"]["id"]
    payload = {"studentId": student, "borrowDate": date.today().isoformat()}
    results = []

    def snapshot():
        availability = {
            kind: staff.call("GET", f"/api/{table}/{fixture['items'][kind]['id']}")["available"]
            for kind, table in KINDS.items()
        }
        history = staff.call("GET", LOANS + "?size=100")["content"]
        return availability, {entry["id"]: entry for entry in history}

    expected_ids = set()
    for kind, table in KINDS.items():
        item = fixture["items"][kind]["id"]
        body = payload | {kind + "Id": item}
        before_availability, before_history = snapshot()
        assert all(before_availability.values())
        assert before_history.keys() == expected_ids
        borrow, borrow_waiters = race(blocker, observer, clients, table, item, LOANS, body)
        assert sorted(status for status, _ in borrow) == [201, 400], borrow
        loan = next(data for status, data in borrow if status == 201)
        assert next(data["code"] for status, data in borrow if status == 400) == "UNAVAILABLE"
        loan_id = loan["id"]
        expected_ids.add(loan_id)
        availability, records = snapshot()
        assert availability == before_availability | {kind: False}
        assert records.keys() == expected_ids
        assert records[loan_id]["status"] == "BORROWED"
        assert {key: records[key] for key in before_history} == before_history

        return_path = f"{LOANS}/{loan_id}/return"
        returned, return_waiters = race(blocker, observer, clients, "borrow_records", loan_id, return_path)
        assert sorted(status for status, _ in returned) == [204, 400], returned
        assert next(data["code"] for status, data in returned if status == 400) == "ALREADY_RETURNED"
        availability, records = snapshot()
        assert availability == before_availability
        assert records.keys() == expected_ids
        assert records[loan_id]["status"] == "RETURNED" and records[loan_id]["returnDate"]
        assert {key: records[key] for key in before_history} == before_history
        results.append({
            "item": kind, "borrow_http": [201, 400], "borrow_rejection": "UNAVAILABLE",
            "return_http": [204, 400], "return_rejection": "ALREADY_RETURNED",
            "borrow_simultaneous_waiters": borrow_waiters,
            "return_simultaneous_waiters": return_waiters,
            "loan_id": loan_id, "final_available": True, "final_loan_status": "RETURNED",
        })

    # Force the documented conflict, observe no state change, then retry.
    book = fixture["items"]["book"]["id"]
    before = snapshot()
    with hold_row(blocker, "books", book):
        status, problem = write(staff, LOANS, payload | {"bookId": book})
    assert status == 409 and problem["code"] == "CONCURRENT_MODIFY", (status, problem)
    assert snapshot() == before
    status, loan = write(staff, LOANS, payload | {"bookId": book})
    assert status == 201 and loan["id"] not in expected_ids
    expected_ids.add(loan["id"])
    active_state = snapshot()
    assert active_state[0] == before[0] | {"book": False}
    assert active_state[1].keys() == expected_ids
    return_path = f"{LOANS}/{loan['id']}/return"
    with hold_row(blocker, "borrow_records", loan["id"]):
        status, problem = write(staff, return_path)
    assert status == 409 and problem["code"] == "CONCURRENT_MODIFY", (status, problem)
    assert snapshot() == active_state
    assert write(staff, return_path) == (204, None)
    availability, records = snapshot()
    assert all(availability.values()) and records.keys() == expected_ids
    assert all(record["status"] == "RETURNED" for record in records.values())
    return {
        "races": results, "borrow_timeout_http": 409, "return_timeout_http": 409,
        "conflict_code": "CONCURRENT_MODIFY", "retry_http": [201, 204],
        "failed_writes_preserved_state": True, "final_returned_loans": len(records),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mysql-port", type=int, default=13384)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    password = os.environ.get("LIBRIS_SQE_MYSQL_PASSWORD")
    if not password or not JAR.is_file():
        parser.error("Build the backend JAR and set the disposable LIBRIS_SQE_MYSQL_PASSWORD")
    connect = {"host": "127.0.0.1", "port": args.mysql_port, "user": DATABASE,
               "password": password, "database": DATABASE, "autocommit": True,
               "connect_timeout": 5, "read_timeout": 12, "write_timeout": 12}
    db_env = {
        "LMS_DB_URL": f"jdbc:mysql://127.0.0.1:{args.mysql_port}/{DATABASE}"
                      "?useSSL=false&allowPublicKeyRetrieval=true&connectionTimeZone=UTC",
        "LMS_DB_USERNAME": DATABASE, "LMS_DB_PASSWORD": password,
    }
    app = None
    admin_password = secrets.token_urlsafe(24) + "Aa1!"
    with pymysql.connect(**connect) as blocker, pymysql.connect(**connect) as observer:
        with observer.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            if not version.startswith("8.4."):
                raise RuntimeError("Use a disposable MySQL 8.4 server")
            cursor.execute("SHOW TABLES")
            if cursor.fetchone() is not None:
                raise RuntimeError("The disposable libris_sqe database must be empty")
        try:
            app = start_app(18091, admin_password, profile="default", database_environment=db_env,
                            extra_args=("--spring.datasource.hikari.connection-init-sql="
                                        "SET SESSION innodb_lock_wait_timeout=6",))
            clients = [Api(BASE), Api(BASE)]
            for api in clients:
                api.login(admin_password)
            fixture = seed(clients[0], secrets.token_urlsafe(24) + "Aa1!")
            evidence = {"mysql_version": version, "flyway_fresh_schema": True}
            evidence.update(check_database(blocker, observer, clients, fixture))
            write_json(args.output, evidence)
            print(json.dumps(evidence, indent=2))
        finally:
            stop_app(app)


if __name__ == "__main__":
    main()
