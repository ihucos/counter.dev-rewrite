import { expect, test } from "@playwright/test";

test("landing page renders", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveTitle(/Counter/);
  await expect(page.locator("h1").first()).toContainText(
    /analytics|visitor|simple/i,
  );
});

test("static assets load", async ({ page }) => {
  const failed: string[] = [];
  page.on("response", (r) => {
    if (r.url().startsWith("http://localhost:8080") && r.status() >= 400) {
      // App pages load API endpoints without an extension (e.g. /dump);
      // only flag broken static files.
      if (/\.[a-z0-9]+$/i.test(new URL(r.url()).pathname)) {
        failed.push(`${r.status()} ${r.url()}`);
      }
    }
  });
  await page.goto("/");
  expect(failed).toEqual([]);
});