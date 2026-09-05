# Running the tests

The backend tests (`services/backend/core/tests/`) need Postgres (localhost:5432)
and Redis (localhost:6379), provided by the root `compose.yaml`.

```sh
docker compose up -d postgres redis   # from the repo root
cd services/backend
uv run pytest core/tests              # add -n 4 for parallel, -x to stop on first failure
docker compose down                   # when done
```

Notes:

- The suite creates its own `test_counter` database; Postgres needs to be
  reachable, not pre-migrated.
- Redis fixtures flush a dedicated per-worker DB around every test, so runs
  are isolated from the dev `sync` container.
- `frontend` and `gateway` compose files work too (`docker compose up` builds
  and serves the site via the gateway on :80); they're not needed for the
  tests. Postgres/Redis must stay published for this host-side suite.

# E2E tests

Playwright tests in `e2e/tests/` run against the gateway on :80 under the
local hostname http://counterdev.test; the SPA calls the API on
http://api.counterdev.test with CORS (both are same-site under the
two-label `.counterdev.test` base, so the session cookie flows over plain
HTTP). Only the gateway publishes a host port;
the frontend, backend and tracker are reachable only through it, routed by
Host header (see [getting-started.md](getting-started.md)). The tests map
the hostnames to 127.0.0.1 via Chromium host-resolver rules and an explicit
Host header for the tracker requests, so `/etc/hosts` entries are not
required. The `webServer` config in `e2e/playwright.config.ts` starts the
stack (`docker compose up --wait gateway sync`, including the `build`
container that generates the blog/help pages and the backend that serves
the API) when nothing is listening, and reuses a running one otherwise.

```sh
docker compose up -d      # from the repo root (or let the config start it)
cd e2e
npm install               # first run only; also run `npx playwright install chromium`
npm test                  # add --headed / --debug to watch the browser
docker compose down       # when done
```

The tests cover the landing page, the app pages' redirect behavior, the full
sign-up / log-in flow (plus account recovery and deletion), and the
dashboard (see `e2e/tests/`).

The dashboard tests ingest real tracking data by sending HTTP requests to
the tracker via the gateway as `t.counterdev` (`POST /track` and
`/trackpage`, like the external tracking script does) and then assert what
the dashboard renders.
This requires the `tracker` and `sync` compose services to be running (the
`webServer` config starts them); the browser runs pinned to UTC so the
"today" bucket matches between tracker and dashboard. `tests/fixes.spec.ts`
additionally covers the regression fixes from `docs/design-issues.md`: an
empty dashboard rendering without errors, the username-keyed tracking code
ingesting end-to-end, and the `?demo=1` live demo working without a session.

Failures leave a trace in `e2e/test-results/` (`npx playwright show-trace
<path-to-trace.zip>`).