import { expect, test } from "@playwright/test";

const pages = [
  // dashboard/setup redirect anonymous visitors (no /dump session), so only
  // the welcome page can be asserted on directly.
  { url: "/welcome.html", title: "Counter: Welcome" },
];

for (const p of pages) {
  test(`${p.url} serves with the right title`, async ({ page }) => {
    const response = await page.goto(p.url);
    expect(response?.status()).toBe(200);
    await expect(page).toHaveTitle(p.title);
  });
}

test("dashboard redirects anonymous visitors to the welcome page", async ({ page }) => {
  await page.goto("/dashboard.html");
  await expect(page).toHaveURL(/welcome\.html$/);
});

test("setup redirects anonymous visitors to the landing page", async ({ page }) => {
  await page.goto("/setup.html");
  await expect(page).toHaveURL(/index\.html$/);
});

test("unknown paths 404", async ({ request }) => {
  const response = await request.get("/no-such-page.html");
  expect(response.status()).toBe(404);
});