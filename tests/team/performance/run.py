"""Run four comparable, disposable H2 circulation workloads with k6."""

import argparse
import json
import secrets
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fixtures"))
from circulation import Api, seed
from verify_h2 import JAR, start_app, stop_app

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE = "http://127.0.0.1:18085"


def one_run(vus, repeat, evidence):
    admin_secret = secrets.token_urlsafe(24) + "Aa1!"
    student_secret = secrets.token_urlsafe(24) + "Aa1!"
    process = start_app(18085, admin_secret)
    try:
        api = Api(BASE)
        api.login(admin_secret)
        fixture = seed(api, student_secret)
        template = json.loads((ROOT / "tests/team/fixtures/circulation.json").read_text())
        users = []
        for index in range(5):
            secret = secrets.token_urlsafe(24) + "Aa1!"
            username = f"sqe_perf_{repeat}_{vus}_{index}"
            api.call("POST", "/api/librarians", {
                "username": username, "password": secret,
                "name": f"Synthetic Performance Librarian {index}",
                "age": 30, "phone": "03000000000",
            }, expected=201)
            if index == 0:
                book_id = fixture["items"]["book"]["id"]
            else:
                book = dict(template["book"])
                book["title"] += f" perf {repeat} {vus} {index}"
                book["isbn"] = f"9780000000{repeat}{vus}{index}"
                book_id = api.call("POST", "/api/books", book, expected=201)["id"]
            users.append({"username": username, "password": secret, "book_id": book_id})

        if api.count("/api/borrow-records") != 0:
            raise AssertionError("Workload must start with no loans")
        config = {"base_url": BASE, "student_id": fixture["student"]["id"],
                  "borrow_date": date.today().isoformat(), "users": users}
        local = HERE / "k6-config.local.json"
        local.write_text(json.dumps(config), encoding="utf-8")
        summary = evidence / f"k6-{vus}vu-{repeat}.json"
        stdout = evidence / f"k6-{vus}vu-{repeat}.txt"
        try:
            with stdout.open("w", encoding="utf-8") as output:
                completed = subprocess.run(
                    ["k6", "run", "--summary-export", str(summary),
                     "-e", f"CONFIG={local}", "-e", f"VUS={vus}", str(HERE / "circulation.js")],
                    cwd=ROOT, stdout=output, stderr=subprocess.STDOUT, timeout=110,
                    check=False,
                )
        finally:
            local.unlink(missing_ok=True)
        # Keep console evidence readable in Git without changing measured values.
        stdout.write_text("\n".join(line.rstrip() for line in stdout.read_text(encoding="utf-8").splitlines()) + "\n",
                          encoding="utf-8")
        history = api.call("GET", "/api/borrow-records?size=10000")
        active = [row for row in history["content"] if row["status"] == "BORROWED"]
        availability = [api.call("GET", f"/api/books/{user['book_id']}")["available"] for user in users]
        result = {"vus": vus, "repeat": repeat, "k6_exit": completed.returncode,
                  "initial_loan_count": 0, "final_loan_count": history["totalElements"],
                  "active_loans": len(active), "books_available": availability,
                  "summary": summary.name, "raw_output": stdout.name}
        if completed.returncode != 0 or active or not all(availability):
            raise AssertionError(f"Workload failed; see {stdout}: {result}")
        return result
    finally:
        stop_app(process)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "output/performance")
    args = parser.parse_args()
    evidence = args.output_dir.resolve()
    if not JAR.is_file():
        raise RuntimeError("Build the backend JAR first")
    evidence.mkdir(parents=True, exist_ok=True)
    results = []
    for vus in (1, 5):
        for repeat in (1, 2):
            result = one_run(vus, repeat, evidence)
            results.append(result)
            print(json.dumps(result), flush=True)
    (evidence / "runs.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
