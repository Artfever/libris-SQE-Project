"""Run authenticated Lighthouse categories on borrow and return screens."""

import json
import secrets
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tests/team/fixtures"))
from circulation import Api, seed
from verify_h2 import start_app, stop_app

BASE = "http://127.0.0.1:18087"
EVIDENCE = ROOT / "tests/team/evidence/usability"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
LIGHTHOUSE = HERE / "node_modules/.bin/lighthouse.cmd"


def lighthouse(label, run_name):
    path = EVIDENCE / f"lighthouse-{label}-{run_name}.json"
    completed = subprocess.run(
        [str(LIGHTHOUSE), BASE + "/borrow.html", "--port=19223",
         "--only-categories=accessibility,best-practices,seo", "--output=json",
         f"--output-path={path}", "--disable-storage-reset", "--quiet"],
        cwd=HERE, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        timeout=120, check=False,
    )
    if completed.returncode:
        raise RuntimeError(f"Lighthouse failed: {completed.stdout[-1200:]}")
    report = json.loads(path.read_text(encoding="utf-8"))
    scores = {name: round(100 * report["categories"][name]["score"])
              for name in ("accessibility", "best-practices", "seo")}
    return {"screen": label, "scores": scores, "report": path.name}


def run(run_name):
    if not CHROME.is_file() or not LIGHTHOUSE.is_file():
        raise RuntimeError("Chrome and npm.cmd ci in tests/team/usability are required")
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    admin_secret = secrets.token_urlsafe(24) + "Aa1!"
    student_secret = secrets.token_urlsafe(24) + "Aa1!"
    process = start_app(18087, admin_secret)
    try:
        api = Api(BASE)
        api.login(admin_secret)
        fixture = seed(api, student_secret)
        with tempfile.TemporaryDirectory(prefix="sqe-lh-") as profile:
            with sync_playwright() as pw:
                context = pw.chromium.launch_persistent_context(
                    profile, executable_path=str(CHROME), headless=True,
                    args=["--remote-debugging-port=19223"])
                try:
                    context.add_cookies([{"name": c.name, "value": c.value, "url": BASE}
                                         for c in api.cookies])
                    page = context.new_page()
                    page.goto(BASE + "/borrow.html")
                    page.locator("#issueItemBtn").wait_for()
                    results = [lighthouse("borrow", run_name)]
                    book_id = fixture["items"]["book"]["id"]
                    api.call("POST", "/api/borrow-records", {
                        "bookId": book_id, "studentId": fixture["student"]["id"],
                        "borrowDate": date.today().isoformat(),
                    }, expected=201)
                    page.reload()
                    page.locator(".return-book").wait_for()
                    results.append(lighthouse("return", run_name))
                    output = EVIDENCE / f"lighthouse-scores-{run_name}.json"
                    output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
                    print(json.dumps(results, indent=2))
                finally:
                    context.close()
    finally:
        stop_app(process)


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "after")
