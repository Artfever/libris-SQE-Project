"""Exercise circulation role decisions against a disposable local H2 server."""

import json
import secrets
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fixtures"))
from circulation import Api, seed, write_json
from verify_h2 import JAR, start_app, stop_app

BASE = "http://127.0.0.1:18084"
LOANS = "/api/borrow-records"


def login(username, password):
    client = Api(BASE)
    client.refresh_csrf()
    client.call("POST", "/api/auth/login", {"username": username, "password": password})
    client.refresh_csrf()
    return client


def request(client, method, path, body=None):
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if method != "GET" and client.csrf_token:
        headers["X-XSRF-TOKEN"] = client.csrf_token
    payload = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=payload, headers=headers, method=method)
    try:
        response = client.opener.open(req, timeout=15)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        data = response.read()
        return response.status, json.loads(data) if data else None


def check(rows, role, action, expected, observed):
    rows.append({"role": role, "action": action, "expected_http": expected, "observed_http": observed})
    if observed != expected:
        raise AssertionError(f"{role} {action}: HTTP {observed}, expected {expected}")


def main():
    if not JAR.is_file():
        raise RuntimeError("Build the backend JAR first")
    admin_secret = secrets.token_urlsafe(24) + "Aa1!"
    student_secret = secrets.token_urlsafe(24) + "Aa1!"
    process = start_app(18084, admin_secret)
    try:
        admin = login("admin", admin_secret)
        fixture = seed(admin, student_secret)
        student = login(fixture["student"]["username"], student_secret)
        book_id = fixture["items"]["book"]["id"]
        student_id = fixture["student"]["id"]
        body = {"bookId": book_id, "studentId": student_id, "borrowDate": date.today().isoformat()}
        rows = []

        status, _ = request(student, "POST", LOANS, body)
        check(rows, "STUDENT", "borrow book", 403, status)
        assert admin.call("GET", f"/api/books/{book_id}")["available"] is True
        assert admin.count(LOANS) == 0

        status, _ = request(student, "GET", LOANS)
        check(rows, "STUDENT", "list all loans", 403, status)
        status, own = request(student, "GET", LOANS + "/my")
        check(rows, "STUDENT", "read own loans", 200, status)
        assert own["totalElements"] == 0

        status, loan = request(admin, "POST", LOANS, body)
        check(rows, "ADMIN", "borrow book", 201, status)
        assert loan["status"] == "BORROWED"
        assert admin.call("GET", f"/api/books/{book_id}")["available"] is False
        assert admin.count(LOANS) == 1

        status, _ = request(student, "POST", f"{LOANS}/{loan['id']}/return")
        check(rows, "STUDENT", "return book", 403, status)
        assert admin.call("GET", f"/api/books/{book_id}")["available"] is False
        assert admin.count(LOANS) == 1

        status, own = request(student, "GET", LOANS + "/my")
        check(rows, "STUDENT", "read own active loan", 200, status)
        assert own["totalElements"] == 1

        status, _ = request(admin, "POST", f"{LOANS}/{loan['id']}/return")
        check(rows, "ADMIN", "return book", 204, status)
        assert admin.call("GET", f"/api/books/{book_id}")["available"] is True
        history = admin.call("GET", LOANS)
        assert history["totalElements"] == 1 and history["content"][0]["status"] == "RETURNED"
        result = {"profile": "h2", "decisions": rows, "final_book_available": True,
                  "loan_history_count": 1, "final_loan_status": "RETURNED"}
        output = Path(__file__).resolve().parents[1] / "evidence" / "security-roles-2026-11-21.json"
        write_json(output, result)
        print(json.dumps(result, indent=2))
    finally:
        stop_app(process)


if __name__ == "__main__":
    main()
