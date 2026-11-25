const AxeBuilder = require("@axe-core/playwright").default;
const { chromium, expect } = require("playwright/test");
const { readFileSync } = require("node:fs");

async function main() {
  const { baseURL, password, bookId, studentId } = JSON.parse(readFileSync(0, "utf8"));
  const browser = await chromium.launch();
  try {
    const context = await browser.newContext({ baseURL });
    const page = await context.newPage();
    await page.goto("/api/auth/csrf");
    await page.evaluate(async (secret) => {
      const csrfCookie = document.cookie.split("; ").find(value => value.startsWith("XSRF-TOKEN="));
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": decodeURIComponent(csrfCookie.slice(11)) },
        body: JSON.stringify({ username: "admin", password: secret })
      });
      if (!response.ok) throw new Error("Fixture login failed");
    }, password);
    await page.goto("/borrow.html");
    const issue = page.locator("#issueItemBtn");
    await expect(issue).toBeVisible();
    await expect(page.locator("#circulationTable .loading-state")).toHaveCount(0);
    const reports = [];

    async function scan(screen) {
      const { url, testEngine, violations, incomplete, passes, inapplicable } =
        await new AxeBuilder({ page }).analyze();
      reports.push({ screen, url, testEngine, violations, incomplete, passes, inapplicable });
    }

    await scan("borrow");
    await issue.click();
    const dialog = page.getByRole("dialog", { name: "Issue an item" });
    await expect(dialog).toBeVisible();
    await scan("borrow-dialog");
    await dialog.getByLabel("Item").selectOption(`book:${bookId}`);
    await dialog.getByLabel("Student").selectOption(String(studentId));
    await dialog.getByRole("button", { name: "Issue item" }).click();
    await expect(page.getByText("Item issued successfully.")).toBeVisible();
    const returnButton = page.getByRole("button", { name: "Return", exact: true });
    await expect(returnButton).toBeVisible();
    await scan("return");
    await returnButton.click();
    await expect(page.getByText("Item returned successfully.")).toBeVisible();
    console.log(JSON.stringify({ integration: "@axe-core/playwright", browser: browser.version(), reports }));
  } finally {
    await browser.close();
  }
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
