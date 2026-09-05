import { expect, test, type Page } from "@playwright/test";
import {
  API_BASE,
  addSite,
  readMe,
  signUp,
  trackVisit,
  uniqueName,
  waitForVisits,
} from "./helpers";

// A fresh account whose one site receives tracking data sent as plain HTTP
// requests to the tracker, exactly like the external tracking script does.
// The dashboard is then expected to visualize it via the /query endpoint.
const SITE = "e2e-dashboard.example";

async function accountWithData(page: Page, visits: number) {
  const user = uniqueName();
  await signUp(page, user);
  await addSite(page, SITE);

  await page.goto("/dashboard.html");

  // 5 search-engine visits, 2 from another site, 1 direct visit (no
  // referrer) and 2 pageviews — 10 tracked requests in total, all today.
  for (let i = 0; i < 5; i++) {
    await trackVisit(SITE, user, { referrer: "https://google.com/search?q=stuff", country: "DE" });
  }
  for (let i = 0; i < 2; i++) {
    await trackVisit(SITE, user, { referrer: "https://news.ycombinator.com/item", country: "DE" });
  }
  await trackVisit(SITE, user, { country: "DE" });
  await trackVisit(SITE, user, { page: "/" });
  await trackVisit(SITE, user, { page: "/about" });

  await waitForVisits(page, SITE, visits);

  // The dashboard only fetches on load and on user interactions; reload to
  // pick up the data immediately.
  await page.reload();
  await expect(page.locator("#site-select")).toHaveValue(SITE, { timeout: 15_000 });

  return user;
}

test("the selected range is remembered across reloads", async ({ page }) => {
  await accountWithData(page, 10);

  await page.locator("#range-select").selectOption("all");
  // "All time" is a superset of today, so the total stays the same.
  await expect(page.locator("dashboard-counter-visitors dashboard-number")).toHaveText("10");

  await page.reload();
  await expect(page.locator("#range-select")).toHaveValue("all", { timeout: 15_000 });
  await expect(page.locator("dashboard-counter-visitors dashboard-number")).toHaveText("10");
});

test("guest share access shows the dashboard without a session", async ({ page, browser }) => {
  await accountWithData(page, 10);

  // Enable guest access and grab the account uuid from the /me endpoint.
  const res = await page.request.post(`${API_BASE}/reset_token`);
  expect(res.status()).toBe(200);
  const { token } = await res.json();
  const me = await readMe(page);
  const uuid = me?.user?.uuid;
  expect(uuid).toBeTruthy();

  // An anonymous visitor with the share link sees the same data.
  const guest = await browser.newContext();
  const guestPage = await guest.newPage();
  await guestPage.goto(`/dashboard.html?user=${uuid}&token=${token}`);
  await expect(guestPage.locator("#site-select")).toHaveValue(SITE, { timeout: 15_000 });
  await expect(guestPage.locator("dashboard-counter-visitors dashboard-number")).toHaveText("10");

  // A wrong token is rejected like no session at all.
  const intruder = await guest.newPage();
  await intruder.goto(`/dashboard.html?user=${uuid}&token=wrong-token`);
  await expect(intruder).toHaveURL(/welcome\.html$/, { timeout: 15_000 });

  await guest.close();
});

test("no live connection remains open after the dashboard loaded", async ({ page }) => {
  await accountWithData(page, 10);

  // The dashboard fetches only on load and on user interactions; there is
  // no SSE /dump connection to the backend anymore.
  const dumpRequests = await page.evaluate(
    () =>
      performance
        .getEntriesByType("resource")
        .filter((e) => new URL(e.name).pathname === "/dump").length,
  );
  expect(dumpRequests).toBe(0);
  // Let any live reconnects surface; nothing should re-request /dump.
  await page.waitForTimeout(2000);
  const dumpRequestsLater = await page.evaluate(
    () =>
      performance
        .getEntriesByType("resource")
        .filter((e) => new URL(e.name).pathname === "/dump").length,
  );
  expect(dumpRequestsLater).toBe(0);
});