# counter.dev rewrite

A rewrite of [counter.dev](https://counter.dev) — simple, privacy-friendly web analytics. Monorepo of six services that all run on one machine.

## Run it

```sh
# one-time: add local hostnames to /etc/hosts
127.0.0.1 counterdev t.counterdev api.counterdev

docker compose up   # from the repo root; gateway on :80 is the only published port
```

| Service | URL |
|---|---|
| Frontend (site + dashboard) | http://counterdev |
| Tracker (ingest) | http://t.counterdev |
| Backend (API/admin) | http://api.counterdev |

Local and production hostnames mirror each other (`counterdev` ↔ `counter.dev`); anything else (including `localhost`) gets a rejection page pointing at the right names.

## What's inside

| Service | Tech | Role |
|---|---|---|
| gateway | nginx | Edge proxy, routes by Host header — only published port |
| frontend | nginx + pelican | Static site + dashboard SPA |
| tracker | Go | Hot-path beacon ingest → Redis, never touches Postgres |
| backend | Django 5 | Auth, dashboard API, admin |
| sync | Django command | Drains Redis into Postgres |
| redis / postgres | | Ingest buffer + cache / aggregated counts + users |

Tracking: sites embed `script.js` with a `data-id`; the script beacons to the tracker, which buckets visits in Redis; sync persists aggregates to Postgres; the dashboard reads a single SSE endpoint (`/dump`).

## Architecture goals

Performance and development speed, achieved through: dev/prod parity, infra as code coupled to app code, monorepo, vanilla stacks (AI-friendly), no premature scaling (one machine), and homegrown capabilities over off-the-shelf.

## Docs

- [docs/getting-started.md](docs/getting-started.md) — setup and running
- [docs/architecture.md](docs/architecture.md) — services, data flow, gotchas
- [docs/api.md](docs/api.md) — API endpoints
- [docs/testing.md](docs/testing.md) — backend tests and Playwright e2e suite
- [docs/design-issues.md](docs/design-issues.md) — known gaps and open decisions