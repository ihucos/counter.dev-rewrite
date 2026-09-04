import { expect, type Page } from "@playwright/test";

// The tracker service is published on :8001 by the root compose file. It
// records visits in Redis; the `sync` container moves them into Postgres
// (within a second), from where the dashboard's /dump endpoint reads them.
export const TRACKER_URL = "http://localhost:8001";

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
  const res = await page.request.post("/account_edit", {
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
  const res = await fetch(`${TRACKER_URL}${path}`, {
    method: "POST",
    headers,
    body: params,
  });
  if (!res.ok) {
    throw new Error(`${path} returned ${res.status}: ${await res.text()}`);
  }
}

type Dump = {
  user: { uuid: string };
  sites: Record<string, { visits: Record<string, Record<string, Record<string, number>>> }>;
};

// Read the account state by listening for the first "dump" event of the
// /dump SSE stream with the page's session cookies (or guest parameters).
// Returns null if the stream reports no signed-in user.
export async function readFirstDump(page: Page, query = "utcoffset=0"): Promise<Dump | null> {
  return page.evaluate(
    (q) =>
      new Promise((resolve, reject) => {
        const es = new EventSource(`/dump?${q}`);
        const timeout = setTimeout(() => {
          es.close();
          reject(new Error("no dump event within 10s"));
        }, 10_000);
        es.onmessage = (ev) => {
          const { type, payload } = JSON.parse(ev.data);
          if (type === "dump" || type === "nouser") {
            clearTimeout(timeout);
            es.close();
            resolve(payload);
          }
        };
      }),
    query,
  );
}

export function bucketVisits(dump: Dump, site: string, range: string): Record<string, number> {
  return dump?.sites?.[site]?.visits?.[range]?.date ?? {};
}

export function sumVisits(visits: Record<string, number>): number {
  return Object.values(visits).reduce((acc, n) => acc + n, 0);
}

// Wait until the ingested visits have made it through Redis and the sync
// service into Postgres, i.e. until /dump reports them for the given site.
export async function waitForVisits(page: Page, site: string, min: number) {
  await expect
    .poll(async () => sumVisits(bucketVisits(await readFirstDump(page), site, "day")), {
      timeout: 20_000,
      intervals: [500],
    })
    .toBeGreaterThanOrEqual(min);
}