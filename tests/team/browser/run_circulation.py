"""Browser flows for the six Libris circulation use cases against local H2."""
import json
import re
import secrets
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fixtures"))
from circulation import Api, seed
from verify_h2 import start_app, stop_app

PORT = 18083
LOANS = "/api/borrow-records"
KINDS = {"book": "books", "magazine": "magazines", "newspaper": "newspapers"}
FLOW_IDS = ("main", "alternate_1", "alternate_2", "exception_1", "exception_2")


class BrowserCirculation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        password = secrets.token_urlsafe(24) + "Aa1!"
        student_password = secrets.token_urlsafe(24) + "Aa1!"
        librarian_password = secrets.token_urlsafe(24) + "Aa1!"
        cls.base = f"http://127.0.0.1:{PORT}"
        cls.process = start_app(PORT, password)
        cls.addClassCleanup(stop_app, cls.process)
        admin = Api(cls.base)
        admin.login(password)
        cls.staff = admin
        cls.fixture = seed(admin, student_password)
        admin.call("POST", "/api/librarians", {
            "username": "sqe_browser_librarian", "password": librarian_password,
            "name": "Synthetic Librarian", "age": 30, "phone": "03000000000",
        }, expected=201)
        cls.accounts = {"admin": admin}
        for role, username, secret in (
            ("librarian", "sqe_browser_librarian", librarian_password),
            ("student", cls.fixture["student"]["username"], student_password),
        ):
            api = Api(cls.base)
            api.refresh_csrf()
            api.call("POST", "/api/auth/login", {"username": username, "password": secret})
            api.refresh_csrf()
            cls.accounts[role] = api
        playwright = sync_playwright().start()
        cls.addClassCleanup(playwright.stop)
        cls.browser = playwright.chromium.launch()
        cls.addClassCleanup(cls.browser.close)
        print(f"Chromium {cls.browser.version}", flush=True)

    def page(self, role):
        context = self.browser.new_context(base_url=self.base)
        self.addCleanup(context.close)
        context.add_cookies([
            {"name": cookie.name, "value": cookie.value, "url": self.base}
            for cookie in self.accounts[role].cookies
        ])
        page = context.new_page()
        page.goto("/borrow.html")
        expect(page.get_by_role("heading", name="Borrow records", exact=True)).to_be_visible()
        return page

    def item(self, kind):
        return self.fixture["items"][kind]

    def snapshot(self):
        availability = {
            kind: self.staff.call("GET", f"/api/{route}/{self.item(kind)['id']}")["available"]
            for kind, route in KINDS.items()
        }
        result = self.staff.call("GET", LOANS + "?size=100")
        self.assertEqual(result["totalElements"], len(result["content"]))
        return availability, {row["id"]: row for row in result["content"]}

    def create_active(self, kind):
        return self.staff.call("POST", LOANS, {
            f"{kind}Id": self.item(kind)["id"], "studentId": self.fixture["student"]["id"],
            "borrowDate": date.today().isoformat(),
        }, expected=201)

    def finish_active(self, record):
        self.staff.call("POST", f"{LOANS}/{record['id']}/return", expected=204)

    def open_form(self, page, kind):
        issue = page.locator("#issueItemBtn")
        self.wait_for_rows(page)
        issue.click()
        form = page.get_by_role("dialog", name="Issue an item")
        form.get_by_label("Item").select_option(f"{kind}:{self.item(kind)['id']}")
        form.get_by_label("Student").select_option(str(self.fixture["student"]["id"]))
        return form

    def row(self, page, kind):
        return page.locator(".circulation-row").filter(has_text=self.item(kind)["title"])

    def wait_for_rows(self, page):
        expect(page.locator(".table-foot .muted")).to_contain_text("Showing")
        expect(page.locator("#circulationTable .loading-state")).to_have_count(0)

    def find_action(self, page, kind, record_id):
        self.wait_for_rows(page)
        button = self.row(page, kind).locator(f"button[data-id='{record_id}']")
        page_count = (len(self.snapshot()[1]) + 9) // 10
        for number in range(page_count):
            if button.count():
                return button
            if number + 1 < page_count:
                with page.expect_response(lambda response: f"{LOANS}?page={number + 1}&" in response.url):
                    page.locator(".pager").get_by_role("button", name=str(number + 2), exact=True).click()
                expect(page.locator(".pager button.active")).to_have_text(str(number + 2))
        self.fail(f"Active record {record_id} not found in {page_count} pages")

    def toast(self, page, message):
        expect(page.get_by_role("status").filter(has_text=message)).to_be_visible()

    def borrow_flow(self, kind, flow, role):
        page = self.page(role)
        form = self.open_form(page, kind)
        due_field = form.get_by_label("Due date")
        borrow_date = date.fromisoformat(form.get_by_label("Issue date").input_value())
        if flow == "alternate_1":
            due_field.fill("")
        if flow == "alternate_2":
            due_field.fill((borrow_date + timedelta(days=21)).isoformat())

        if flow == "exception_1":
            competing = self.create_active(kind)
            try:
                before = self.snapshot()
                form.get_by_role("button", name="Issue item").click()
                expect(form.locator("[data-borrow-error]")).to_contain_text("not available")
                self.assertEqual(self.snapshot(), before)
            finally:
                self.finish_active(competing)
            return
        if flow == "exception_2":
            # Simulate an obsolete dropdown ID while retaining the real POST and response.
            form.get_by_label("Item").evaluate("(select) => { select.selectedOptions[0].value = " +
                                               json.dumps(f"{kind}:-1") + "; }")
            before = self.snapshot()
            form.get_by_role("button", name="Issue item").click()
            expect(form.locator("[data-borrow-error]")).to_contain_text("not found")
            self.assertEqual(self.snapshot(), before)
            return

        expected_due = due_field.input_value() or (borrow_date + timedelta(days=14)).isoformat()
        availability, old_loans = self.snapshot()
        with page.expect_response(lambda response: f"{LOANS}?page=" in response.url):
            form.get_by_role("button", name="Issue item").click()
        self.toast(page, "Item issued successfully.")
        after, loans = self.snapshot()
        new_ids = loans.keys() - old_loans.keys()
        self.assertEqual(len(new_ids), 1)
        created = loans[new_ids.pop()]
        self.addCleanup(self.finish_active, created)
        row = self.find_action(page, kind, created["id"]).locator("xpath=ancestor::tr")
        expect(row.get_by_text(expected_due, exact=True)).to_be_visible()
        self.assertEqual(after, availability | {kind: False})
        self.assertEqual({key: loans[key] for key in old_loans}, old_loans)
        self.assertEqual((created["itemId"], created["itemType"], created["studentId"],
                          created["borrowDate"], created["dueDate"], created["status"]),
                         (self.item(kind)["id"], kind.upper(), self.fixture["student"]["id"],
                          borrow_date.isoformat(), expected_due, "BORROWED"))
        profile = self.staff.call("GET", f"/api/students/{created['studentId']}")
        for name in ("name", "email", "phone"):
            self.assertEqual(created["borrower" + name.capitalize()], profile[name])

    def return_flow(self, kind, flow, main_role):
        record = self.create_active(kind)
        record_id = record["id"]

        def cleanup():
            if self.snapshot()[1][record_id]["status"] == "BORROWED":
                self.finish_active(record)
        self.addCleanup(cleanup)
        role = ("admin" if main_role == "librarian" else "librarian") if flow == "alternate_1" else main_role
        if flow == "exception_2" and kind != "newspaper":
            page = self.page("student")
            expect(page.get_by_text("Circulation management is available to library staff.", exact=False)).to_be_visible()
            expect(page.get_by_role("button", name="Return")).to_have_count(0)
            before = self.snapshot()
            status = page.evaluate("""async (path) => {
                const token = document.cookie.split('; ').find(s => s.startsWith('XSRF-TOKEN=')).split('=')[1];
                return (await fetch(path, {method: 'POST', headers: {'X-XSRF-TOKEN': token}})).status;
            }""", f"{LOANS}/{record_id}/return")
            self.assertEqual(status, 403)
            self.assertEqual(self.snapshot(), before)
            return

        page = self.page(role)
        button = self.find_action(page, kind, record_id)
        if kind == "newspaper" and flow == "exception_1":
            self.finish_active(record)
            before = self.snapshot()
            button.click()
            self.toast(page, "Already returned.")
            self.assertEqual(self.snapshot(), before)
            return
        if flow.startswith("exception"):
            # No staff UI deletes a loan. Substitute an obsolete row ID and
            # exercise the application's actual click handler and server response.
            button.evaluate("(button) => { button.dataset.id = '-1'; }")
            before = self.snapshot()
            self.row(page, kind).locator("button[data-id='-1']").click()
            self.toast(page, "Borrow record not found.")
            self.assertEqual(self.snapshot(), before)
            return

        availability, loans = self.snapshot()
        today = date.today()
        closed = self.row(page, kind).get_by_role("button", name="Closed")
        old_closed = closed.count()
        button.click()
        self.toast(page, "Item returned successfully.")
        expect(closed).to_have_count(old_closed + 1)
        after, history = self.snapshot()
        returned = history[record_id]
        self.assertIn(date.fromisoformat(returned["returnDate"]), {today, date.today()})
        expected = loans[record_id] | {"status": "RETURNED", "returnDate": returned["returnDate"], "daysOverdue": returned["daysOverdue"]}
        self.assertEqual(history, loans | {record_id: expected})
        self.assertEqual(after, availability | {kind: True})
        if flow == "alternate_2" and kind != "newspaper":
            learner = closed.first.locator("xpath=ancestor::tr").locator("a[href^='student-profile.html']")
            learner.click()
            expect(page.get_by_role("heading", name="Borrow history", exact=True)).to_be_visible()
            history_row = page.locator(".tl-row").filter(has_text=self.item(kind)["title"])
            expect(history_row.get_by_text("Returned", exact=True).last).to_be_visible()
        if flow == "alternate_2" and kind == "newspaper":
            student = self.page("student")
            expect(student.get_by_role("link", name="Open student dashboard")).to_be_visible()
            student.get_by_role("link", name="Open student dashboard").click()
            expect(student).to_have_url(re.compile(r"/index.html$"))
            expect(student.get_by_text("No active borrows", exact=True)).to_be_visible()
            history_response = student.request.get(f"{LOANS}/my?size=100")
            self.assertEqual(history_response.status, 200)
            own = {row["id"]: row for row in history_response.json()["content"]}
            self.assertEqual(own[record_id]["status"], "RETURNED")


def scenario(action, kind, flow, role):
    def run(self):
        getattr(self, action + "_flow")(kind, flow, role)
    return run


for use_case, action, kind, role in (
    (1, "borrow", "book", "librarian"), (2, "borrow", "magazine", "admin"),
    (3, "borrow", "newspaper", "librarian"), (4, "return", "book", "librarian"),
    (5, "return", "magazine", "admin"), (6, "return", "newspaper", "librarian"),
):
    for index, flow in enumerate(FLOW_IDS):
        name = f"test_uc_{use_case:02}_{index}_{flow}"
        setattr(BrowserCirculation, name, scenario(action, kind, flow, role))


if __name__ == "__main__":
    unittest.main(verbosity=2)
