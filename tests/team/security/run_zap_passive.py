"""Proxy borrow and return through local ZAP and export sanitized passive alerts."""

import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tests/team/fixtures"))
from circulation import Api, seed
from verify_h2 import JAR, stop_app

PORT = 18088
APP = f"http://host.docker.internal:{PORT}"
DIRECT = f"http://127.0.0.1:{PORT}"
ZAP = "http://127.0.0.1:18090"


def zap(path, **params):
    url = ZAP + "/JSON/" + path + "/?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"Host": "zap"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def start_app(password):
    with socket.socket() as connection:
        if connection.connect_ex(("127.0.0.1", PORT)) == 0:
            raise RuntimeError(f"Port {PORT} is occupied")
    environment = dict(os.environ)
    environment["LMS_ADMIN_PASSWORD"] = password
    log_path = Path(tempfile.gettempdir()) / "libris-phase4-zap-app.log"
    with log_path.open("wb") as log:
        process = subprocess.Popen(
            ["java", "-jar", str(JAR), "--spring.profiles.active=h2",
             f"--server.port={PORT}", "--server.address=0.0.0.0",
             "--server.servlet.session.cookie.secure=false"],
            cwd=ROOT / "backend", env=environment, stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    for _ in range(60):
        if process.poll() is not None:
            raise RuntimeError(f"Application exited; inspect {log_path}")
        try:
            with urllib.request.urlopen(DIRECT + "/actuator/health", timeout=1) as response:
                if json.load(response).get("status") == "UP":
                    return process
        except (OSError, ValueError):
            pass
        time.sleep(1)
    stop_app(process)
    raise RuntimeError(f"Application not healthy; inspect {log_path}")


def main():
    if not JAR.is_file():
        raise RuntimeError("Build the backend JAR first")
    for _ in range(45):
        try:
            version = zap("core/view/version")["version"]
            break
        except (OSError, ValueError, KeyError):
            time.sleep(1)
    else:
        raise RuntimeError("Start the local ZAP daemon on port 18090")
    secret = secrets.token_urlsafe(24) + "Aa1!"
    student_secret = secrets.token_urlsafe(24) + "Aa1!"
    process = start_app(secret)
    try:
        api = Api(DIRECT)
        api.login(secret)
        fixture = seed(api, student_secret)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(proxy={"server": ZAP})
            try:
                context = browser.new_context(base_url=APP)
                context.add_cookies([{"name": c.name, "value": c.value, "url": APP}
                                     for c in api.cookies])
                page = context.new_page()
                page.route("https://**", lambda route: route.abort())
                page.goto(APP + "/borrow.html")
                expect(page.locator("#issueItemBtn")).to_be_visible()
                page.locator("#issueItemBtn").click()
                form = page.locator("#borrow-form")
                expect(form).to_be_visible()
                book_id = fixture["items"]["book"]["id"]
                form.get_by_label("Item").select_option(f"book:{book_id}")
                form.get_by_label("Student").select_option(str(fixture["student"]["id"]))
                form.get_by_role("button", name="Issue item").click()
                expect(page.locator(".return-book")).to_be_visible()
                assert api.call("GET", f"/api/books/{book_id}")["available"] is False
                page.locator(".return-book").click()
                expect(page.locator(".circulation-row")).to_contain_text("Returned")
                assert api.call("GET", f"/api/books/{book_id}")["available"] is True
                history = api.call("GET", "/api/borrow-records")
                assert history["totalElements"] == 1 and history["content"][0]["status"] == "RETURNED"
                context.close()
            finally:
                browser.close()
        for _ in range(30):
            if int(zap("pscan/view/recordsToScan")["recordsToScan"]) == 0:
                break
            time.sleep(1)
        message_count = int(zap("core/view/numberOfMessages")["numberOfMessages"])
        raw = zap("alert/view/alerts", baseurl=APP, start=0, count=500)["alerts"]
        alerts = []
        for item in raw:
            parsed = urllib.parse.urlsplit(item.get("url", ""))
            alerts.append({"plugin_id": item.get("pluginId"), "name": item.get("name"),
                           "risk": item.get("risk"), "confidence": item.get("confidence"),
                           "method": item.get("method"), "path": parsed.path})
        report = {"tool": "OWASP ZAP", "version": version, "mode": "passive proxy only",
                  "profile": "h2", "proxied_messages": message_count,
                  "borrow_and_return_completed": True, "loan_history_count": 1,
                  "alerts": alerts, "alert_count": len(alerts)}
        path = ROOT / "tests/team/evidence/security/zap-passive-2026-11-21.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({key: value for key, value in report.items() if key != "alerts"}, indent=2))
    finally:
        stop_app(process)


if __name__ == "__main__":
    main()
