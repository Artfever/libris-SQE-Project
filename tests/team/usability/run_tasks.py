"""Browser usability tasks and full axe scans on disposable circulation screens."""

import json
import secrets
import sys
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tests/team/fixtures"))
from circulation import Api, seed
from verify_h2 import start_app, stop_app

BASE = "http://127.0.0.1:18086"
AXE = Path(__file__).with_name("node_modules") / "axe-core" / "axe.min.js"
EVIDENCE = ROOT / "tests/team/evidence/usability"


def axe_scan(page, label, run_name, selector=None):
    page.add_script_tag(path=str(AXE))
    result = page.evaluate(
        "async selector => await axe.run(selector ? document.querySelector(selector) : document)",
        selector,
    )
    report = {"url": page.url, "label": label, "violations": result["violations"],
              "incomplete": result["incomplete"], "passes": len(result["passes"]),
              "inapplicable": len(result["inapplicable"])}
    (EVIDENCE / f"axe-{label}-{run_name}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    remaining = {v["id"] for v in result["violations"]} & {
        "color-contrast", "label-content-name-mismatch"
    }
    if run_name.endswith("after"):
        assert not remaining, f"Accessibility regressions remain on {label}: {sorted(remaining)}"
    return {"screen": label, "violation_count": len(report["violations"]),
            "violations": [v["id"] for v in report["violations"]]}


def run(run_name):
    if not AXE.is_file():
        raise RuntimeError("Run npm.cmd ci in tests/team/usability first")
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    admin_secret = secrets.token_urlsafe(24) + "Aa1!"
    student_secret = secrets.token_urlsafe(24) + "Aa1!"
    process = start_app(18086, admin_secret)
    try:
        api = Api(BASE)
        api.login(admin_secret)
        fixture = seed(api, student_secret)
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            try:
                context = browser.new_context(base_url=BASE)
                context.add_cookies([{"name": c.name, "value": c.value, "url": BASE} for c in api.cookies])
                page = context.new_page()
                page.goto("/borrow.html")
                expect(page.get_by_role("heading", name="Borrow records", exact=True)).to_be_visible()
                expect(page.locator("#circulationTable .loading-state")).to_have_count(0)
                scans = [axe_scan(page, "borrow", run_name)]
                page.locator("#topbar-theme button").evaluate("button => button.click()")
                page.wait_for_timeout(500)
                scans.append(axe_scan(page, "borrow-light", run_name))
                page.locator("#topbar-theme button").evaluate("button => button.click()")
                page.wait_for_timeout(500)
                page.locator("#issueItemBtn").click()
                form = page.locator("#borrow-form")
                expect(form).to_be_visible()
                scans.append(axe_scan(page, "borrow-modal", run_name, "#modal-root"))

                # Invalid item is rejected with a correction instruction, then repaired.
                form.get_by_role("button", name="Issue item").click()
                error = page.locator("[data-borrow-error]")
                expect(error).to_contain_text("Choose an item, a student, and an issue date.")
                book_id = fixture["items"]["book"]["id"]
                student_id = fixture["student"]["id"]
                item = form.get_by_label("Item")
                item.select_option(f"book:{book_id}")
                form.get_by_label("Student").select_option(str(student_id))

                # Check sequential keyboard focus and submit with Enter.
                item.focus()
                focus_order = []
                for _ in range(12):
                    focus_order.append(page.evaluate("document.activeElement.getAttribute('name') || document.activeElement.textContent.trim()"))
                    if "Cancel" in focus_order[-1]:
                        break
                    page.keyboard.press("Tab")
                assert focus_order[:2] == ["item", "studentId"], focus_order
                assert focus_order.index("borrowDate") < focus_order.index("dueDate"), focus_order
                assert "Cancel" in focus_order[-1], focus_order
                form.get_by_role("button", name="Issue item").focus()
                page.keyboard.press("Enter")
                expect(page.locator("#borrow-form")).to_have_count(0)
                expect(page.locator(".circulation-row")).to_contain_text(fixture["items"]["book"]["title"])
                assert api.call("GET", f"/api/books/{book_id}")["available"] is False
                history = api.call("GET", "/api/borrow-records")
                assert history["totalElements"] == 1 and history["content"][0]["status"] == "BORROWED"
                loan_id = history["content"][0]["id"]
                scans.append(axe_scan(page, "return", run_name))
                page.locator("#topbar-theme button").evaluate("button => button.click()")
                page.wait_for_timeout(500)
                scans.append(axe_scan(page, "return-light", run_name))

                # A stale row ID gives a visible failure; the real ID succeeds on retry.
                button = page.locator(".return-book").first
                button.evaluate("(el) => el.dataset.id = '999999999'")
                button.click()
                expect(page.locator(".toast").last).to_be_visible()
                assert api.call("GET", f"/api/books/{book_id}")["available"] is False
                assert api.count("/api/borrow-records") == 1
                button.evaluate(f"(el) => el.dataset.id = '{loan_id}'")
                button.click()
                expect(page.locator(".circulation-row")).to_contain_text("Returned")
                assert api.call("GET", f"/api/books/{book_id}")["available"] is True
                history = api.call("GET", "/api/borrow-records")
                assert history["totalElements"] == 1 and history["content"][0]["status"] == "RETURNED"
                result = {"profile": "h2", "browser": browser.version,
                          "tasks": ["invalid borrow then keyboard correction and submit",
                                    "stale return ID then corrected return"],
                          "focus_order": focus_order, "scans": scans,
                          "final_book_available": True, "loan_history_count": 1}
                (EVIDENCE / f"tasks-{run_name}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
                print(json.dumps(result, indent=2))
            finally:
                browser.close()
    finally:
        stop_app(process)


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "before")
