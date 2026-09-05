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
URL tells you how to fix itself. Testing, e2e suite and further details:
[testing.md](testing.md), [architecture.md](architecture.md).