# Frontend

The site and dashboard are one static bundle in [services/frontend/static](../services/frontend/static), served by nginx. There is no SPA framework, no bundler and no node toolchain: pages are classic multi-page HTML navigations, and the dynamic parts are vanilla-JS [web components](https://developer.mozilla.org/en-US/docs/Web/API/Web_components) loaded as plain `<script>` tags. The API lives on a separate hostname (`api.counter.dev` / `api.counterdev.test`) and is reached cross-origin with session cookies — see [api.md](api.md).

## Layout

| Path | Role |
|---|---|
| `static/*.html` | The app pages: `index.html` (landing), `welcome.html` (sign up / sign in tabs), `dashboard.html`, `setup.html` (post-registration wizard). |
| `static/components/` | Web components, one file per `<base-…>`/`<dashboard-…>` custom element. `components/base/` holds the site chrome (navbar, footer, edit-account, flash, pay-what-you-want); `components/dashboard/` holds the dashboard widgets (graph, pie, time-graph, selector, settings, …) all sharing the `BaseGraph` canvas helper in `_base.js`. |
| `static/js/` | Page scripts: `dashboard.js`, `welcome.js`, `setup.js` plus `utils.js`, the shared helper library. |
| `static/load.js` | The only script tag each page needs to add by hand; it injects every component file (order matters, hence the manual list — new components must be registered here). |
| `content/` + `templates/` + `Makefile` | The generated part of the site: blog posts via Pelican, help and plain pages via yasha, rendered into `out/`. |
| `nginx.conf` | Static file server on :8080 (internal; the gateway publishes :80). `absolute_redirect off` keeps directory redirects relative so the internal port never leaks into `Location` headers. |

The `build` compose service regenerates `out/` on every `docker compose up` (see the frontend `compose.yaml`), so the site can be served without host-side tooling. Content sources live in `content/{posts,pages,help}`.

## Shared plumbing (`static/js/utils.js`)

- **`apiBase()` / `apiUrl()`** — rewrite API paths to the API hostname based on the current hostname (`counter.dev` → `https://api.counter.dev`, `counterdev.test` → `http://api.counterdev.test`, anything else → same origin, which is what the e2e suite and direct backend access rely on).
- **`apiGetJSON(path)`** — GET with `credentials: "include"`, forwarding the page's query string so guest (`?user=&token=`) and demo (`?demo=1`) access flow through. Returns `null` on 401 instead of throwing; this is the "not signed in" signal.
- **`simpleForm(selector, target)`** — intercepts a form submit and POSTs it as `application/x-www-form-urlencoded` via fetch; on success either redirects (`target` is a URL) or calls the callback with the response text. All auth forms (login, sign up, recover, feedback) go through this.
- Modal system (`openModal`/`closeModal`), `notify()`, tabs, slide helpers — minimal vanilla replacements for the previously used jQuery plugins.

## Auth bootstrap and the navbar

There is no client-side session state store. Every page load establishes auth the same way:

1. `<base-navbar>` (`components/base/navbar.js`) injects its markup in `connectedCallback` and calls `loadUser()`.
2. `loadUser()` calls `apiGetJSON("/me")`. On success it dispatches `push-navbar-dump` (with the `/me` payload) on `document`; on 401 or error it dispatches `push-navbar-nouser`. The navbar renders the username vs. the Log in/Sign up links from these events.
3. Any other code that needs auth state uses `navbar.loggedInUserCallback(loggedInCb, notLoggedInCb)` or listens for the `userloaded` event — e.g. `welcome.js` redirects signed-in visitors from the login page to the dashboard.

To avoid a navbar flicker between the HTML arriving and `/me` responding, the username is cached in `sessionStorage` under `navbar-username-cache-<hash(document.cookie)>` and replayed before the network answer. The hash key is a heuristic to invalidate the cache when cookies change; it is best-effort only — `/me` remains the source of truth, and `noUser()` resets the rendered user UI (hides `.has-user`, clears `.fill-username`).

Sign out is a client-side action: the navbar intercepts clicks on its Sign out links, fetches the backend `GET /logout` (which ends the Django session) with credentials, clears the `navbar-username-cache-*` sessionStorage entries, and redirects to `/welcome.html`. The plain href stays as the no-JS fallback.

Note the session cookie is set on the API hostname, not the site hostname, so the site's `document.cookie` never contains it — do not gate any UI on reading it client-side.

## Gotchas

- **Adding a component requires editing `static/load.js`** — nothing auto-discovers files, and the component tag name is derived from the script path (`_base.js`'s `tagName()`), so a component's file location is its API.
- `apiGetJSON` forwards the full page query string to every JSON endpoint; an unexpected `?…` on a page URL silently changes what the API sees (this is how guest/demo access works).
- The login form posts to `/login` on the API host via fetch with `credentials: "include"`; the session cookie therefore lands on `api.*`. Locally this only works under `counterdev.test` (see [getting-started.md](getting-started.md) for why a bare `counterdev` host drops the cookie).
- The Russia overlay and the `simple-web-analytics.com` redirect in `navbar.js` are legacy behaviors kept for production parity; the overlay fetches `/lang` on every page load.
- `components/dashboard/pie.js.bak` and similar leftovers are dead; `load.js` is the definitive list of what actually runs.