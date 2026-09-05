import { expect, test, type Page } from "@playwright/test";
import { API_BASE, addSite, gotoDashboard, listSites, readMe, signUp, uniqueName } from "./helpers";

// Tests for the account-level flows reachable through the UI: sign out,
// the edit-account modal (settings + sites), deleting a site, feedback,
// and revoking guest share access.

// The desktop navbar shows the user menu on hover.
async function openUserMenu(page: Page) {
  await page.hover(".profile-user");
  await page.locator(".dropdown-content a", { hasText: "Sign out" }).waitFor();
}

test("signing out through the navbar ends the session", async ({ page }) => {
  const user = uniqueName();
  await signUp(page, user);
  await page.goto("/dashboard.html");
  await expect(page.locator(".profile-user")).toHaveText(user, { timeout: 15_000 });

  await openUserMenu(page);
  await page.locator(".dropdown-content a", { hasText: "Sign out" }).click();

  // The backend redirects back to the SPA the sign-out came from.
  await expect(page).toHaveURL(/\/welcome\.html$/, { timeout: 15_000 });

  // The session is really gone: the dashboard bounces anonymous visitors.
  await page.goto("/dashboard.html");
  await expect(page).toHaveURL(/welcome\.html$/, { timeout: 15_000 });
});

test("editing the account through the modal saves settings and sites", async ({ page }) => {
  const user = uniqueName();
  await signUp(page, user);
  await addSite(page, "e2e-edit-a.example");

  await gotoDashboard(page);
  await expect(page.locator("#site-select")).toHaveValue("e2e-edit-a.example", {
    timeout: 15_000,
  });

  await openUserMenu(page);
  await page.locator(".dropdown-content a", { hasText: "Edit account" }).click();
  const form = page.locator("#account-edit:visible");
  await form.locator("input[name='mail']").fill("e2e-keeper@example.com");
  await form.locator("select[name='utcoffset']").selectOption("2");
  // "Limit listed domains" reveals the sites textarea (hidden otherwise).
  await form.locator("select[name='usesites']").selectOption("1");
  await form.locator("textarea[name='sites']").fill(
    "https://e2e-edit-a.example\nhttps://e2e-edit-b.example",
  );
  await form.locator("button[type='submit']").click();

  // simpleForm redirects to the current page, i.e. reloads the dashboard.
  await expect(page.locator("#site-select")).toHaveValue("e2e-edit-a.example", {
    timeout: 15_000,
  });

  // The reload can still be in flight when the select reappears; poll
  // /me until the saved state shows up.
  let me: Awaited<ReturnType<typeof readMe>> = null;
  await expect
    .poll(
      async () => {
        me = await readMe(page).catch(() => null);
        return me?.user?.timezone;
      },
      { timeout: 15_000 },
    )
    .toBe(2);
  expect((await listSites(page))?.map((s) => s.name).sort()).toEqual([
    "e2e-edit-a.example",
    "e2e-edit-b.example",
  ]);
});

test("deleting the selected site through the settings modal", async ({ page }) => {
  const user = uniqueName();
  await signUp(page, user);
  await addSite(page, "e2e-delete.example");

  await gotoDashboard(page);
  await expect(page.locator("#site-select")).toHaveValue("e2e-delete.example", {
    timeout: 15_000,
  });

  // The backend deletes the *selected* site (prefs.site), which the
  // selector records via /set_pref_site on every change — so touch the
  // select once and wait for that request before deleting.
  await Promise.all([
    page.waitForResponse((r) => r.url().includes("/set_pref_site")),
    page.locator("#site-select").selectOption("e2e-delete.example"),
  ]);

  // The settings element redraws its modal markup, leaving stale hidden
  // copies; always talk to the visible instance.
  await page.locator("a[href='#modal-settings']:visible").click();
  await page.locator("#modal-settings .btn-confirm:visible").click();
  await page.locator("#modal-settings .confirm-input:visible").fill("e2e-delete.example");
  await page
    .locator("#modal-settings form#site-delete:visible")
    .locator("button")
    .click();

  // The settings form redirects to the dashboard; with no sites left the
  // dashboard sends the account back to the setup page.
  await expect(page).toHaveURL(/\/setup\.html$/, { timeout: 15_000 });
  const sites = await listSites(page);
  expect(sites?.map((s) => s.name) ?? []).toEqual([]);
});

test("revoking the share token locks out guest access", async ({ page, browser }) => {
  const user = uniqueName();
  await signUp(page, user);
  await addSite(page, "e2e-token.example");
  await gotoDashboard(page);
  await expect(page.locator("#site-select")).toHaveValue("e2e-token.example", {
    timeout: 15_000,
  });

  const res = await page.request.post(`${API_BASE}/reset_token`);
  const { token } = await res.json();
  const me = await readMe(page);
  const uuid = me?.user?.uuid;
  expect(uuid).toBeTruthy();

  await page.request.post(`${API_BASE}/delete_token`);

  // A guest with the now-revoked token is rejected like without any token.
  const guest = await browser.newContext();
  const guestPage = await guest.newPage();
  await guestPage.goto(`/dashboard.html?user=${uuid}&token=${token}`);
  await expect(guestPage).toHaveURL(/welcome\.html$/, { timeout: 15_000 });
  await guest.close();
});

test("the feedback form submits from the navbar", async ({ page }) => {
  await signUp(page, uniqueName());
  await page.goto("/dashboard.html");
  await expect(page.locator(".profile-user")).toBeVisible({ timeout: 15_000 });

  await page.locator(".nav-header a[href='#modal-feedback']").click();
  const form = page.locator("#modal-feedback form");
  await form.locator("textarea[name='feedback']").fill("e2e: nice analytics!");
  await form.locator("button[type='submit']").click();

  // The backend answers "ok", which the UI surfaces in the notify modal.
  await expect(page.locator("#modal-notify")).toContainText("ok", { timeout: 15_000 });
});