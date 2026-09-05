import { expect, type Page } from "@playwright/test";
import { request as httpRequest } from "node:http";

// The tracker is reached through the gateway as t.counterdev.test (the
// gateway routes by Host header). We talk to 127.0.0.1 directly with an
// explicit Host header, so /etc/hosts entries aren't required to run the
// suite. The tracker records visits in Redis; the `sync` container moves them into
// Postgres (within a second), from where the dashboard's /query endpoint
// reads them.
export const TRACKER_HOST = "t.counterdev.test";

// The API lives on its own hostname, routed through the gateway.
export const API_BASE = "http://api.counterdev.test";

// A realistic desktop Chrome user agent — the tracker silently drops bot
// user agents (including Playwright's default HeadlessChrome).
export const CHROME_UA =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36";

// Usernames must be unique across runs because the backend rejects duplicates.
export const uniqueName = () => `e2e-user-${Date.now()}-${Math.floor(Math.random() * 1000)}`;

export async function signUp(page: Page, user: string, password = "hunter2secret") {
  await page.goto("/welcome.html?sign-up");
  const form = page.locator("#sign-up form");
  await form.locator("input[name='user']").fill(user);
  await form.locator("input[name='password']").fill(password);
  // The form is submitted via AJAX; wait until the request has actually been
  // processed (success redirects to setup.html, failure shows a modal).
  const done = Promise.race([
    page.waitForURL(/\/setup\.html$/),
    page.locator("#modal-notify").waitFor(),
  ]);
  await form.locator("button[type='submit']").click();
  await done;
}

// Add a site through the same endpoint the settings form posts to.
export async function addSite(page: Page, site: string) {
  const res = await page.request.post(`${API_BASE}/account_edit`, {
    form: { sites: `https://${site}`, utcoffset: "0" },
  });
  expect(res.status()).toBe(200);
}

export type VisitSpec = {
  referrer?: string;
  country?: string;
  // When set, the visit is sent as a pageview (/trackpage); otherwise as a
  // plain visit (/track).
  page?: string;
};

// Ingest a single visit with an HTTP request to the tracker, mimicking what
// the external tracking script does. The `id` must be the account username
// (sync.py maps Redis visit keys to accounts by username), the Origin header
// must be the tracked site and must not be localhost (dropped by the tracker).
export async function trackVisit(site: string, id: string, spec: VisitSpec = {}) {
  const isPageview = spec.page !== undefined;
  const params = new URLSearchParams({ id, utcoffset: "0" });
  if (isPageview) params.set("page", spec.page);
  if (spec.referrer) params.set("referrer", spec.referrer);
  if (spec.country) params.set("country", spec.country);

  const headers: Record<string, string> = {
    "Content-Type": "application/x-www-form-urlencoded",
    Origin: `https://${site}`,
    "User-Agent": CHROME_UA,
  };
  // Only /track derives the language from Accept-Language.
  if (!isPageview) headers["Accept-Language"] = "de-DE,de;q=0.9";

  const path = isPageview ? "/trackpage" : "/track";
  const res = await new Promise<{ statusCode?: number; text: string }>((resolve, reject) => {
    const req = httpRequest(
      {
        host: "127.0.0.1",
        port: 80,
        path,
        method: "POST",
        headers: { ...headers, Host: TRACKER_HOST },
      },
      (res) => {
        let text = "";
        res.on("data", (chunk) => (text += chunk));
        res.on("end", () => resolve({ statusCode: res.statusCode, text }));
      },
    );
    req.on("error", reject);
    req.end(params.toString());
  });
  if (res.statusCode === undefined || res.statusCode >= 400) {
    throw new Error(`${path} returned ${res.status}: ${await res.text()}`);
  }
}

export type Me = {
  user: { id: string; uuid: string; prefs: Record<string, unknown>; timezone?: number };
  meta: { utcoffset: number; sessionless: boolean; demo: boolean };
};

// Read the signed-in user's state via /me with the page's session cookies
// (or guest parameters). Returns null on 401 ("not signed in").
export async function readMe(page: Page, query = "utcoffset=0"): Promise<Me | null> {
  return page.evaluate(
    ([base, q]) =>
      fetch(`${base}/me?${q}`, { credentials: "include" }).then(
        (r) => (r.status === 401 ? null : r.json()),
      ),
    [API_BASE, query],
  );
}

// The sites an account has (the /sites list is the source of truth).
// Returns null on 401 ("not signed in").
export async function listSites(page: Page, query = ""): Promise<Array<{ name: string }> | null> {
  return page.evaluate(
    ([base, q]) =>
      fetch(`${base}/sites${q ? "?" + q : ""}`, { credentials: "include" }).then(
        (r) => (r.status === 401 ? null : r.json()),
      ),
    [API_BASE, query],
  );
}

export function sumVisits(visits: Record<string, number>): number {
  return Object.values(visits).reduce((acc, n) => acc + n, 0);
}

// Query the analytics data for a site via /query; `start`/`end` are ISO
// dates and either may be null (open-ended).
export async function queryVisits(
  page: Page,
  site: string,
  start: string | null,
  end: string | null,
  query = "utcoffset=0",
): Promise<Record<string, Record<string, number>>> {
  const params = new URLSearchParams({ site, ...(query ? Object.fromEntries(new URLSearchParams(query)) : {}) });
  if (start) params.set("start", start);
  if (end) params.set("end", end);
  return page.evaluate(
    ([base, q]) => fetch(`${base}/query?${q}`, { credentials: "include" }).then((r) => r.json()),
    [API_BASE, params.toString()],
  );
}

// The "date" category buckets one item per day, so summing it gives the
// total number of visits in the range.
export function dayTotals(visits: Record<string, Record<string, number>>): Record<string, number> {
  return visits?.date ?? {};
}

// Wait until the ingested visits have made it through Redis and the sync
// service into Postgres, i.e. until /query reports them for the given site
// today.
export async function waitForVisits(page: Page, site: string, min: number) {
  const today = new Date().toISOString().slice(0, 10);
  await expect
    .poll(async () => sumVisits(dayTotals(await queryVisits(page, site, today, today))), {
      timeout: 20_000,
      intervals: [500],
    })
    .toBeGreaterThanOrEqual(min);
}