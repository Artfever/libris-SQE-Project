"""Verify circulation access using Chromium and a disposable H2 database."""

import argparse
import secrets
import sys
from datetime import date
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fixtures"))
from circulation import Api, seed, write_json
from verify_h2 import JAR, start_app, stop_app

BASE = "http://127.0.0.1:18084"
LOANS = "/api/borrow-records"


def request(page, method, path, body=None, *, csrf=True):
    return page.evaluate(
        """async ({method, path, body, csrf}) => {
            const headers = {Accept: "application/json"};
            if (method !== "GET" && csrf) {
                const token = document.cookie.split("; ")
                    .find(cookie => cookie.startsWith("XSRF-TOKEN="));
                if (!token) throw new Error("Missing CSRF cookie");
                headers["X-XSRF-TOKEN"] = decodeURIComponent(token.slice("XSRF-TOKEN=".length));
            }
            if (body !== null) headers["Content-Type"] = "application/json";
            const response = await fetch(path, {
                method, headers, body: body === null ? undefined : JSON.stringify(body)
            });
            const text = await response.text();
            return [response.status, text ? JSON.parse(text) : null];
        }""",
        {"method": method, "path": path, "body": body, "csrf": csrf},
    )


def login(browser, username, password):
    context = browser.new_context()
    page = context.new_page()
    assert page.goto(BASE + "/api/auth/csrf").status == 200
    assert request(page, "POST", "/api/auth/login", {"username": username, "password": password})[0] == 200
    assert request(page, "GET", "/api/auth/csrf")[0] == 200
    cookie = next(item for item in context.cookies() if item["name"] == "JSESSIONID")
    assert cookie["httpOnly"] and cookie["sameSite"] == "Lax", "Unexpected session cookie attributes"
    return page


def verify(browser, api, fixture, admin_secret, student_secret):
    admin = login(browser, "admin", admin_secret)
    student = login(browser, fixture["student"]["username"], student_secret)
    second_secret = secrets.token_urlsafe(24) + "Aa1!"
    other = api.call("POST", "/api/students", {
        "username": "sqe_history_isolation",
        "password": second_secret,
        "name": "Synthetic isolation student",
        "email": "sqe-history-isolation@example.test",
        "phone": "03000000000",
    }, expected=201)
    other_page = login(browser, "sqe_history_isolation", second_secret)
    book = fixture["items"]["book"]["id"]
    magazine = fixture["items"]["magazine"]["id"]
    payload = {"bookId": book, "studentId": fixture["student"]["id"], "borrowDate": date.today().isoformat()}
    decisions = []

    def check(page, role, action, status, method, path, body=None, *, csrf=True):
        observed, data = request(page, method, path, body, csrf=csrf)
        assert observed == status, f"{role} {action}: HTTP {observed}, expected {status}"
        decisions.append({"role": role, "action": action, "expected_http": status, "observed_http": observed})
        return data

    def snapshot():
        return (
            [api.call("GET", f"/api/{kind}/{item}")["available"]
             for kind, item in (("books", book), ("magazines", magazine))],
            api.call("GET", LOANS)["content"],
        )

    empty = snapshot()
    assert empty == ([True, True], [])
    check(student, "STUDENT A", "borrow book", 403, "POST", LOANS, payload)
    assert snapshot() == empty
    check(admin, "ADMIN", "borrow without CSRF", 403, "POST", LOANS, payload, csrf=False)
    assert snapshot() == empty
    loan = check(admin, "ADMIN", "borrow book", 201, "POST", LOANS, payload)
    other_body = {"magazineId": magazine, "studentId": other["id"], "borrowDate": payload["borrowDate"]}
    other_loan = check(admin, "ADMIN", "borrow magazine", 201, "POST", LOANS, other_body)
    active = snapshot()
    assert active[0] == [False, False]
    assert {(item["id"], item["status"]) for item in active[1]} == {
        (loan["id"], "BORROWED"), (other_loan["id"], "BORROWED"),
    }

    check(student, "STUDENT A", "list all loans", 403, "GET", LOANS)
    for page, label, allowed in ((student, "STUDENT A", loan), (other_page, "STUDENT B", other_loan)):
        own = check(page, label, "read own history when both students have loans", 200, "GET", LOANS + "/my")
        assert [item["id"] for item in own["content"]] == [allowed["id"]]

    path = f"{LOANS}/{loan['id']}/return"
    check(student, "STUDENT A", "return book", 403, "POST", path)
    assert snapshot() == active
    check(admin, "ADMIN", "return without CSRF", 403, "POST", path, csrf=False)
    assert snapshot() == active
    check(admin, "ADMIN", "return book", 204, "POST", path)
    check(admin, "ADMIN", "return magazine", 204, "POST", f"{LOANS}/{other_loan['id']}/return")
    final = snapshot()
    assert final[0] == [True, True]
    assert {(item["id"], item["status"]) for item in final[1]} == {
        (loan["id"], "RETURNED"), (other_loan["id"], "RETURNED"),
    }
    return {
        "profile": "h2", "browser": f"Chromium {browser.version}", "driver": "Playwright",
        "decisions": decisions, "cross_student_history_isolated": True,
        "local_session_cookie": {"httpOnly": True, "sameSite": "Lax"},
        "final_available": {"book": True, "magazine": True}, "returned_loans": len(final[1]),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not JAR.is_file():
        raise RuntimeError("Build the backend JAR first")
    admin_secret = secrets.token_urlsafe(24) + "Aa1!"
    student_secret = secrets.token_urlsafe(24) + "Aa1!"
    process = start_app(18084, admin_secret)
    try:
        api = Api(BASE)
        api.login(admin_secret)
        fixture = seed(api, student_secret)
        with sync_playwright() as playwright:
            with playwright.chromium.launch() as browser:
                result = verify(browser, api, fixture, admin_secret, student_secret)
        write_json(args.output, result)
        print(f"{len(result['decisions'])} Playwright role decisions passed")
    finally:
        stop_app(process)


if __name__ == "__main__":
    main()
