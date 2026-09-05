# Getting started

## One-time setup

The stack is hostname-driven, with parity between local development and
production: the same service is `counterdev` locally and `counter.dev` in
production. Requests to any other hostname (including `localhost`) are
rejected with a pointer page.

Add the local hostnames to `/etc/hosts`:

```
127.0.0.1 counterdev t.counterdev api.counterdev
```

## Running

```sh
docker compose up       # from the repo root; the gateway on :80 is the
                        # only published port
```

| Service | Local | Production |
|---|---|---|
| Frontend (site + dashboard) | http://counterdev | https://counter.dev |
| Tracker (ingest) | http://t.counterdev | https://t.counter.dev |
| Backend (API/admin) | http://api.counterdev | https://api.counter.dev |

`localhost:80` shows the rejection page listing the hostnames, so a wrong
URL tells you how to fix itself. Testing, e2e suite and further details:
[testing.md](testing.md), [architecture.md](architecture.md).