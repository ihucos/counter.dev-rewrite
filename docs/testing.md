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
`webServer` config in `e2e/playwright.config.ts` starts the stack
(`docker compose up --wait frontend`, including the `build` container that
generates the blog/help pages) when nothing is listening, and reuses a
running one otherwise.

```sh
docker compose up -d      # from the repo root (or let the config start it)
cd e2e
npm install               # first run only; also run `npx playwright install chromium`
npm test                  # add --headed / --debug to watch the browser
docker compose down       # when done
```

What the tests check (frontend-only, no backend assertions — API calls like
`/dump` simply 404 against the static nginx):

- The landing page renders with its title and headline.
- Static files (css/js/img) all resolve — no 404s from the served pages.
- `dashboard.html`, `setup.html`, and `welcome.html` serve with their titles.
- Unknown paths return 404.

Failures leave a trace in `e2e/test-results/` (`npx playwright show-trace
<path-to-trace.zip>`).