"""Proxy borrow and return through local ZAP and export sanitized passive alerts."""

import argparse
import json
import secrets
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tests/team/fixtures"))
from circulation import Api, seed
from verify_h2 import JAR, start_app, stop_app

PORT = 18088
DIRECT = f"http://127.0.0.1:{PORT}"
ZAP = "http://127.0.0.1:18090"
ZAP_STARTUP_TIMEOUT_SECONDS = 180


def zap(path, **params):
    url = ZAP + "/JSON/" + path + "/?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"Host": "zap"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Sanitized alert report path",
    )
    args = parser.parse_args()
    if not JAR.is_file():
        raise RuntimeError("Build the backend JAR first")
    for _ in range(ZAP_STARTUP_TIMEOUT_SECONDS):
        try:
            version = zap("core/view/version")["version"]
            break
        except (OSError, ValueError, KeyError):
            time.sleep(1)
    else:
        raise RuntimeError("Start the local ZAP daemon on port 18090")
    secret = secrets.token_urlsafe(24) + "Aa1!"
    student_secret = secrets.token_urlsafe(24) + "Aa1!"
    process = start_app(PORT, secret)
    try:
        api = Api(DIRECT)
        api.login(secret)
        fixture = seed(api, student_secret)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(proxy={"server": ZAP, "bypass": "<-loopback>"})
            try:
                context = browser.new_context(base_url=DIRECT)
                context.add_cookies([{"name": c.name, "value": c.value, "url": DIRECT}
                                     for c in api.cookies])
                page = context.new_page()
                page.route("https://**", lambda route: route.abort())
                page.goto("/borrow.html")
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
        else:
            raise RuntimeError("ZAP passive queue did not finish")
        message_count = int(zap("core/view/numberOfMessages", baseurl=DIRECT)["numberOfMessages"])
        if message_count < 2:
            raise RuntimeError("ZAP did not observe the local circulation traffic")
        raw = zap("alert/view/alerts", baseurl=DIRECT, start=0, count=500)["alerts"]
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
        path = args.output if args.output.is_absolute() else ROOT / args.output
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({key: value for key, value in report.items() if key != "alerts"}, indent=2))
    finally:
        stop_app(process)


if __name__ == "__main__":
    main()
