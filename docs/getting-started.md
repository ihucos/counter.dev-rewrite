# Getting started

## One-time setup

The stack is hostname-driven, with parity between local development and
production: the same service is `counterdev` locally and `counter.dev` in
production. Requests to any other hostname (including `localhost`) are
rejected with a pointer page.

Add the local hostnames to `/etc/hosts`:

```
127.0.0.1 counterdev.test t.counterdev.test api.counterdev.test
```

The local names sit under a two-label base (`.counterdev.test`) rather than a
bare apex: a bare "counterdev" is not a real TLD, so the browser treats
`api.counterdev` as a separate site and drops the session cookie. Under
`counterdev.test`, `api.counterdev.test` is same-site and the SameSite=Lax
cookie works over plain HTTP.

## Running

```sh
docker compose up       # from the repo root; the gateway on :80 is the
                        # only published port
```

| Service | Local | Production |
|---|---|---|
| Frontend (site + dashboard) | http://counterdev.test | https://counter.dev |
| Tracker (ingest) | http://t.counterdev.test | https://t.counter.dev |
| Backend (API/admin) | http://api.counterdev.test | https://api.counter.dev |

`localhost:80` shows the rejection page listing the hostnames, so a wrong
URL tells you how to fix itself. Testing and further details:
[testing.md](testing.md), [architecture.md](architecture.md).

## Management commands

The backend container runs `manage.py migrate`, `manage.py createdemodata`
and `manage.py runserver` on start; sync runs
`manage.py sync --forever --sleep 1`. Locally you can invoke them with
`uv run python manage.py <command>` from `services/backend`.

- `createdemodata` — seeds the read-only demo account behind the landing
  page's "Live demo" link (`dashboard.html?demo=1`): a `demo` user with a
  `counter.dev` site and ~60 days of plausible counts (login password:
  `demo-demo-demo`). Idempotent — it does nothing if data is already
  present, and reseeds from scratch if the seed predates a category.
- `sync [--forever] [--sleep N]` — drains visit buckets from Redis into
  Postgres (see [architecture.md](architecture.md)).