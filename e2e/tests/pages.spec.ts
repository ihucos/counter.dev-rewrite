import { expect, test } from "@playwright/test";

test("/welcome.html serves with the right title", async ({ page }) => {
  const response = await page.goto("/welcome.html");
  expect(response?.status()).toBe(200);
  await expect(page).toHaveTitle("Counter: Welcome");
});

test("setup redirects anonymous visitors to the landing page", async ({ page }) => {
  await page.goto("/setup.html");
  await expect(page).toHaveURL(/index\.html$/);
});

test("unknown paths 404", async ({ request }) => {
  const response = await request.get("http://counterdev.test/no-such-page.html");
  expect(response.status()).toBe(404);
});