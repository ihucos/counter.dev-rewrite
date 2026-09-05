import { expect, test } from "@playwright/test";
import { gotoExpectingRedirect } from "./helpers";

test("/welcome.html serves with the right title", async ({ page }) => {
  const response = await page.goto("/welcome.html");
  expect(response?.status()).toBe(200);
  await expect(page).toHaveTitle("Counter: Welcome");
});

test("setup redirects anonymous visitors to the landing page", async ({ page }) => {
  // The 401 boot answer redirects to the landing page; the client-side
  // redirect can abort the goto, so tolerate that.
  await gotoExpectingRedirect(page, "/setup.html", /index\.html$/);
});

test("unknown paths 404", async ({ request }) => {
  const response = await request.get("http://counterdev.test/no-such-page.html");
  expect(response.status()).toBe(404);
});