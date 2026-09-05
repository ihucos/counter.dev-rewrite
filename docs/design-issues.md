# Design issues & known gaps

Found while building the e2e suite and clicking through the UI. Items marked
**fixed** are kept as a record of what changed; the rest need a decision or
deliberate follow-up, not a quick fix.

## Tracking id: uuid vs. username — fixed

The tracking code now embeds `data-id` = **username** (the tracking-code
component reads `dump.user.id`), matching `sync.py`'s username lookup and the
`log:<host>:<username>` log key. The uuid stays as the account identifier for
guest/share links (`?user=<uuid>&token=...`). e2e tests ingest with the
data-id parsed from the tracking code itself.

## Backend doesn't send what the dashboard expects — fixed

The dashboard's data endpoints (`/query`, `/me`, `/sites`) now include:

- every tracker category in every query result (`ref`, `date`, `hour`,
  `device`, `platform`, `browser`, `country`, `lang`, `screen`, `page`,
  `weekday`), empty where there is no data;
- `meta.sessionless` (guest access) and `meta.demo` (`?demo=1`) on `/me`;
- `user.token` (the account's share token) on `/me`.

The frontend normalizes buckets and isolates redraw errors per component, so
a missing dimension can no longer blank the whole dashboard.

## Demo mode — fixed

`dashboard.html?demo=1` (the landing page's "Live demo" link) resolves to the
seeded `demo` account without a session. The backend seeds it on start via
`manage.py createdemodata` (idempotent, see `services/backend/compose.yaml`).

## utcoffset unit mismatch — fixed

The backend interpreted utcoffset as minutes while the tracker and frontend
use hours; `_local_date` now applies hours and clamps to -12..14 like the
tracker.

## sync crash-loop on startup — fixed

`settings.py` used a DNS probe with a `localhost` fallback that resolved
before Docker DNS was ready and pointed sync at its own loopback. Hostnames
now come from `POSTGRES_HOST`/`REDIS_HOST` (set to the service names in
compose, defaulting to localhost for host-side runs), and the sync loop
retries instead of dying when Redis is briefly unreachable.

## Still open

- `push-archive` is never sent by the backend (frontend has a fallback).
- The frontend `utils.js` self-tracking snippet points at
  `simple-web-analytics.com` and `cdn.counter.dev/script-testing.js`;
  decide what counter.dev should use to track its own traffic.
- `services/backend/static/` is a stale duplicate of the frontend static
  files (served by Django for its own pages only) and has drifted.