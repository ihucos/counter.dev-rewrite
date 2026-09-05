# Architecture

Six services, one machine, root [compose.yaml](../compose.yaml) includes each service's own compose file.

## Services

| Service | Tech | Role |
|---|---|---|
| **gateway** | nginx | Edge proxy on :80 — the only published port. Routing is by Host header, with parity between local and production names: `counter.dev`/`counterdev.test` → frontend, `t.counter.dev`/`t.counterdev.test` → tracker, `api.counter.dev`/`api.counterdev.test` → backend; any other hostname (e.g. `localhost`) is rejected with a static page promoting the hostnames. |
| **frontend** | nginx + pelican | Static site on :8080 (internal only); sidecar container regenerates the blog/help output on every `up`. |
| **tracker** | Go | Hot-path ingest on :8001 (internal only): parse beacons, write Redis. Never touches Postgres. |
| **backend** | Django 5 | Auth, dashboard API, admin on :8000 (internal only). |
| **sync** | Django command | `manage.py sync --forever --sleep 1` — drains Redis into Postgres. |
| **redis** | Redis | Ingest buffer + Django cache/session backend. |
| **postgres** | Postgres | Aggregated counts, users, auth. |

## Flow

1. A site embeds `<script src="https://cdn.counter.dev/script.js" data-id="<uuid>">`. This repo's frontend self-tracks via `script-testing.js` with a `data-server` override.
2. The script POSTs to `/track` (first page of a visit) or `/trackpage` (later pages).
3. The tracker (`services/tracker/handler.go`) takes the site id from the `Origin` header minus `www.`, drops bots/localhost, and derives browser/device/platform, language, country (`country` param or `CF-IPCountry`), screen size, referrer, and local date/hour from `utcoffset`.
4. For each field (`lang`, `ref`, `page`, `browser`, `country`, `hour`, …) it pipelines `HINCRBY v:<origin>,<user>,<field>,<date> <value> 1` with a ~2-day `EXPIREAT` safety TTL, plus `ZADD log:<origin>:<user>` trimmed to 30 entries. No queue — these day buckets are the buffer.
5. The sync worker scans `v:*,*,*,*-*-*`, `HGETALL` + deletes each key, and upserts into Postgres `Count(host, date, category, item, total)` rows under `Host(user, name)`; unresolvable users are dropped.
6. The dashboard SPA reads a single SSE endpoint, `GET /dump` (behind the API hostname `api.counter.dev` locally `api.counterdev.test`; the SPA resolves it at runtime and the backend's `CorsMiddleware` grants the SPA origins): per-site `Sum(total)` by category/item over `day / yesterday / last7 / last30 / month / year / all` + custom range, plus the recent-visits log from the Redis zset. Rebuilt every 15 s. Guests read the same endpoint via `?user=<uuid>&token=<token>`.

## Gotchas

- Postgres is fed solely by sync, which deletes keys as it drains them — if sync is down past the TTL, today's data is lost.
- `/dump` reads Postgres, so ingest lags the dashboard by up to ~1 s plus the 15 s refresh.
- No rate limiting on ingest; auth is session-cookie only, API is CSRF-exempt (see [api.md](api.md)).