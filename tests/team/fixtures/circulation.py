"""Seed and inspect disposable Libris circulation fixtures through its public API."""

import argparse
import http.cookiejar
import json
import os
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


HERE = Path(__file__).resolve().parent
KINDS = ("books", "magazines", "newspapers")


class Api:
    def __init__(self, base_url):
        parsed = urllib.parse.urlsplit(base_url)
        if parsed.scheme != "http" or parsed.hostname not in ("localhost", "127.0.0.1"):
            raise ValueError("Only a local HTTP Libris instance is supported")
        self.base_url = base_url.rstrip("/")
        self.cookies = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookies)
        )
        self.csrf_token = None

    def call(self, method, path, payload=None, expected=200):
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        if method != "GET" and self.csrf_token:
            headers["X-XSRF-TOKEN"] = self.csrf_token
        req = urllib.request.Request(
            self.base_url + path, data=body, headers=headers, method=method
        )
        try:
            with self.opener.open(req, timeout=15) as response:
                status = response.status
                data = response.read()
        except urllib.error.HTTPError as error:
            raise RuntimeError(f"{method} {path} returned HTTP {error.code}") from None
        if status != expected:
            raise RuntimeError(f"{method} {path} returned HTTP {status}; expected {expected}")
        return json.loads(data) if data else None

    def login(self, password):
        self.refresh_csrf()
        self.call("POST", "/api/auth/login", {"username": "admin", "password": password})
        self.refresh_csrf()

    def refresh_csrf(self):
        self.call("GET", "/api/auth/csrf")
        self.csrf_token = next(
            (cookie.value for cookie in self.cookies if cookie.name == "XSRF-TOKEN"), None
        )
        if not self.csrf_token:
            raise RuntimeError("The CSRF cookie was not issued")

    def count(self, path):
        return self.call("GET", path + "?size=1")["totalElements"]


def counts(api):
    paths = ["students", *KINDS, "borrow-records"]
    return {name: api.count("/api/" + name) for name in paths}


def require_empty(api):
    found = counts(api)
    if any(found.values()):
        raise RuntimeError(f"Expected a fresh disposable H2 database, found counts: {found}")
    return found


def write_json(path, value):
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def seed(api, student_password):
    before = require_empty(api)
    template = json.loads((HERE / "circulation.json").read_text(encoding="utf-8"))
    suffix = secrets.token_hex(4)
    student = template["student"]
    username = student["username_prefix"] + "_" + suffix
    created_student = api.call(
        "POST",
        "/api/students",
        {
            "username": username,
            "password": student_password,
            "name": student["name"],
            "email": username + "@" + student["email_domain"],
            "phone": student["phone"],
        },
        expected=201,
    )
    items = {}
    for singular, plural in (("book", "books"), ("magazine", "magazines"), ("newspaper", "newspapers")):
        payload = dict(template[singular])
        payload["title"] += " " + suffix
        response = api.call("POST", "/api/" + plural, payload, expected=201)
        items[singular] = {"id": response["id"], "title": response["title"], "available": response["available"]}
    result = {
        "profile": "h2",
        "student": {"id": created_student["id"], "username": created_student["username"]},
        "items": items,
        "before_counts": before,
        "after_counts": counts(api),
    }
    inspect(api, result)
    return result


def inspect(api, manifest):
    student = api.call("GET", f"/api/students/{manifest['student']['id']}")
    if student["username"] != manifest["student"]["username"]:
        raise RuntimeError("Student read-back did not match the manifest")
    for singular, plural in (("book", "books"), ("magazine", "magazines"), ("newspaper", "newspapers")):
        expected_item = manifest["items"][singular]
        actual = api.call("GET", f"/api/{plural}/{expected_item['id']}")
        if actual["title"] != expected_item["title"] or actual["available"] is not True:
            raise RuntimeError(f"{singular} read-back did not match an available fixture")
    actual_counts = counts(api)
    expected_counts = {"students": 1, "books": 1, "magazines": 1, "newspapers": 1, "borrow-records": 0}
    if actual_counts != expected_counts:
        raise RuntimeError(f"Fixture counts differ: {actual_counts}")
    return {"available": {kind: True for kind in manifest["items"]}, "counts": actual_counts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("seed", "inspect", "verify-empty"))
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--manifest", type=Path, help="Manifest from seed; required for inspect")
    parser.add_argument("--output", type=Path, help="Write non-secret JSON evidence")
    args = parser.parse_args()
    if args.command == "inspect" and args.manifest is None:
        parser.error("inspect requires --manifest")
    admin_password = os.environ.get("LMS_ADMIN_PASSWORD")
    if not admin_password:
        parser.error("Set LMS_ADMIN_PASSWORD privately before running this tool")
    student_password = os.environ.get("SQE_STUDENT_PASSWORD")
    if args.command == "seed" and not student_password:
        parser.error("Set SQE_STUDENT_PASSWORD privately before seeding")
    try:
        api = Api(args.base_url)
        api.login(admin_password)
        if args.command == "seed":
            result = seed(api, student_password)
        elif args.command == "inspect":
            result = inspect(api, json.loads(args.manifest.read_text(encoding="utf-8")))
        else:
            result = {"profile": "h2", "counts": require_empty(api)}
        write_json(args.output, result)
        print(json.dumps(result, indent=2))
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        print(f"Fixture check failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
