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
  and serves the site on :8080); they're not needed for the tests.

# E2E tests

Playwright tests in `e2e/tests/` run against the site served by
`docker compose up` — the frontend nginx on http://localhost:8080. The
frontend nginx proxies the backend API endpoints (`/login`, `/register`,
`/dump`, …) to the Django backend, so the full user flows work there. The
`webServer` config in `e2e/playwright.config.ts` starts the stack
(`docker compose up --wait frontend`, including the `build` container that
generates the blog/help pages and the backend that serves the API) when
nothing is listening, and reuses a running one otherwise.

```sh
docker compose up -d      # from the repo root (or let the config start it)
cd e2e
npm install               # first run only; also run `npx playwright install chromium`
npm test                  # add --headed / --debug to watch the browser
docker compose down       # when done
```

The tests cover the landing page, the app pages' redirect behavior, and the
full sign-up / log-in flow (see `e2e/tests/`).

Failures leave a trace in `e2e/test-results/` (`npx playwright show-trace
<path-to-trace.zip>`).