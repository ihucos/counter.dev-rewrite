import { expect, test } from "@playwright/test";
import { API_BASE, signUp, uniqueName } from "./helpers";

test("signing up lands on the setup page showing the new user", async ({ page }) => {
  const user = uniqueName();
  await signUp(page, user, "correct horse battery staple");

  await expect(page).toHaveURL(/\/setup\.html$/);
  await expect(page.locator(".fill-username").first()).toHaveText(user);
  // The tracking code keys on the username: sync.py and the dashboard's
  // visit-log lookup map the data-id back to the account by username.
  await expect(page.locator("counter-trackingcode input")).toHaveValue(
    new RegExp(`data-id="${user}"`),
  );
  await expect(page.locator("counter-trackingcode input")).toHaveValue(/data-utcoffset="[-0-9]+"/);
});

test("signing up twice with the same username shows an error", async ({ page }) => {
  const user = uniqueName();
  await signUp(page, user);
  await expect(page).toHaveURL(/\/setup\.html$/);

  // Sign-up redirects logged-in users away from the welcome page, so use a
  // logged-out context for the second attempt.
  await page.context().clearCookies();
  await signUp(page, user);
  await expect(page.locator("#modal-notify")).toContainText("user already exists");
});

test("logging in with a wrong password shows an error", async ({ page }) => {
  const user = uniqueName();
  await signUp(page, user);

  // Sign-up redirects logged-in users away from the welcome page.
  await page.context().clearCookies();
  await page.goto("/welcome.html?sign-up");
  // Switch to the log in tab.
  await page.locator(".tabs-menu a[href='#sign-in']").click();
  const form = page.locator("#sign-in form");
  await form.locator("input[name='user']").fill(user);
  await form.locator("input[name='password']").fill("wrong-password");
  await form.locator("button[type='submit']").click();

  await expect(page.locator("#modal-notify")).toContainText("wrong password");
});

test("logging in with a fresh account (no sites yet) ends on the setup page", async ({ page }) => {
  const user = uniqueName();
  await signUp(page, user, "login-password-1");

  // Log out by clearing the session, then log back in through the UI.
  await page.context().clearCookies();
  await page.goto("/welcome.html");
  await page.locator(".tabs-menu a[href='#sign-in']").click();
  const form = page.locator("#sign-in form");
  await form.locator("input[name='user']").fill(user);
  await form.locator("input[name='password']").fill("login-password-1");
  await form.locator("button[type='submit']").click();

  // Login redirects to dashboard.html, but an account without sites is sent
  // on to setup.html by the dashboard.
  await expect(page).toHaveURL(/\/setup\.html$/, { timeout: 15_000 });
  await expect(page.locator(".fill-username").first()).toHaveText(user);
});

test("the navbar hides Log in/Sign up for logged-in users", async ({ page }) => {
  const user = uniqueName();
  await signUp(page, user);

  await page.goto("/index.html");
  await expect(page.locator(".fill-username").first()).toHaveText(user);
  // hasUser() must also hide the guest links, which noUser() may have shown
  for (const el of await page.locator(".no-user").all()) {
    await expect(el).toBeHidden();
  }
  await expect(page.locator(".has-user.dropdown")).toBeVisible();

  // After signing out, the guest links come back. /logout is a GET link in
  // the navbar and redirects, so navigate like the real sign-out link does.
  await page.goto(`${API_BASE}/logout`, { waitUntil: "commit" });
  await page.reload();
  await expect(page.locator(".no-user.profile-guest")).toBeVisible();
  await expect(page.locator(".has-user.dropdown")).toBeHidden();
});

test("the dashboard requires a session", async ({ page }) => {
  await page.goto("/dashboard.html");
  // push-nouser sends anonymous visitors back to the welcome page.
  await expect(page).toHaveURL(/welcome\.html$/, { timeout: 15_000 });
});

test("account recovery never reveals whether the account exists", async ({ request }) => {
  const mail = `e2e-${Date.now()}@example.com`;
  const res = await request.post(`${API_BASE}/recover`, { form: { user: "no-such-user", mail } });
  expect(res.status()).toBe(200);
  await expect(res.text()).resolves.toBe("ok");
});

test("deleting the account removes it", async ({ page }) => {
  const user = uniqueName();
  await signUp(page, user);

  const res = await page.request.post(`${API_BASE}/delete_user`);
  expect(res.status()).toBe(200);

  // The session is gone with the account.
  await page.context().clearCookies();
  await page.goto("/welcome.html");
  await page.locator(".tabs-menu a[href='#sign-in']").click();
  const form = page.locator("#sign-in form");
  await form.locator("input[name='user']").fill(user);
  await form.locator("input[name='password']").fill("hunter2secret");
  await form.locator("button[type='submit']").click();
  await expect(page.locator("#modal-notify")).toContainText("no such user");
});