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