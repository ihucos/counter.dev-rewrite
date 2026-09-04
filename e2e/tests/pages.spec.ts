import { expect, test } from "@playwright/test";

const pages = [
  { url: "/dashboard.html", title: "Counter: Dashboard" },
  { url: "/setup.html", title: "Counter: Tracking" },
  { url: "/welcome.html", title: "Counter: Welcome" },
];

for (const p of pages) {
  test(`${p.url} serves with the right title`, async ({ page }) => {
    const response = await page.goto(p.url);
    expect(response?.status()).toBe(200);
    await expect(page).toHaveTitle(p.title);
  });
}

test("unknown paths 404", async ({ request }) => {
  const response = await request.get("/no-such-page.html");
  expect(response.status()).toBe(404);
});