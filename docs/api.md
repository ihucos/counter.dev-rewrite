# API

All endpoints are served by the backend behind `api.counter.dev` (locally
`api.counterdev`). The SPA resolves the API host at runtime via `apiBase()` in
`static/js/utils.js`, and the backend's `CorsMiddleware` grants the SPA origins
cross-origin access with credentials. Authentication is a session cookie managed
by the server. Guest/share access to a dashboard uses
`?user=<id>&token=<token>` query parameters instead of a session.

The API is implemented with Django REST Framework. All endpoints return JSON
(bodies are validated by serializers and accept both form-encoded and JSON
input); a successful mutation answers `{ "ok": true }`.

## Authentication & account

### POST /login

Sign in.

| Field | Type | Required | Description |
|---|---|---|---|
| `user` | string | yes | Username |
| `password` | string | yes | Password |

On success the session cookie is set (body `{ "ok": true }`).

### GET /logout

Sign out. Ends the session and redirects the browser to `/welcome.html` on
the origin it came from (the navbar links here directly), defaulting to
`https://counter.dev/welcome.html` when no referer is present.

### POST /register

Create an account.

| Field | Type | Required | Description |
|---|---|---|---|
| `user` | string | yes | Username |
| `mail` | string | no | Email address |
| `password` | string | yes | Password |
| `utcoffset` | integer | yes | Client UTC offset in minutes |

### POST /recover

Request account recovery.

| Field | Type | Required | Description |
|---|---|---|---|
| `mail` | string | yes | Email address on the account |
| `user` | string | yes | Username |

### POST /account_edit

Update account settings.

| Field | Type | Required | Description |
|---|---|---|---|
| `utcoffset` | integer | yes | Client UTC offset in minutes |
| `usesites` | boolean | yes | Whether the multi-site selector is shown |
| `sites` | string | yes | Newline-separated list of site domains |
| `mail` | string | yes | Email address |

### POST /delete_user

Delete the account and all its data. Requires no body.

### POST /feedback

Send product feedback.

| Field | Type | Required | Description |
|---|---|---|---|
| `feedback` | string | yes | Message |
| `contact` | string | no | Reply email address |

## Sites

### POST /delete_site

Delete the currently selected site and its data. Requires no body.

## Guest / share access

### POST /reset_token

Create a share token for the account. Returns the token used for guest access
(`?user=<id>&token=<token>`).

### POST /delete_token

Revoke the share token. Requires no body.

## Dashboard preferences

### GET /set_pref_site?\<site\>

Persist the selected site. The site name is the URL-encoded query string.

### GET /set_pref_range?\<range\>

Persist the selected time range. Value is one of `day`, `yesterday`, `last7`,
`last30`, `month`, `year`, `all`.

## Dashboard data

All three endpoints serve a signed-in session, guest/share access via
`?user=<uuid>&token=<token>`, or read-only demo access via `?demo=1`. A
missing or invalid account answers **401** ("not signed in"); the SPA
redirects to the welcome page accordingly.

### GET /me

The signed-in user's state: session bootstrap, share-account panel, and
demo/guest flags.

```json
{
  "user": { "id": "...", "uuid": "...", "token": "...", "prefs": {}, "timezone": 0 },
  "meta": { "utcoffset": 0, "sessionless": false, "demo": false }
}
```

### GET /sites

Readonly DRF API (list and retrieve only) exposing the sites resource
(`Host` model) in name order. The list is the source of truth for which
sites an account has (setup-vs-dashboard routing and the site selector).

```json
[ { "name": "example.com", "hide": true }, ... ]
```

`GET /sites/<name>` retrieves a single site.

### GET /query

Analytics data for one site, drawn from the aggregated `Count` model.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `site` | string | yes | Site name (must belong to the account) |
| `start` | date (ISO) | no | Range start; omitted means unbounded past |
| `end` | date (ISO) | no | Range end; omitted means unbounded future |

The range is open-ended: either or both dates may be omitted. Fixed presets
(today, yesterday, last 7/30 days, month, year, all time) are computed
client-side as `start`/`end` values.

```json
{
  "site": "example.com",
  "start": "2026-01-01",
  "end": "2026-09-05",
  "visits": { "lang": {"en": 3}, "ref": {...}, "page": {...}, "date": {...}, "weekday": {...}, "platform": {...}, "browser": {...}, "device": {...}, "country": {...}, "screen": {...}, "hour": {...} },
  "logs": [ { "date": "2026-09-05", "time": "12:00:00", "country": "de", "referrer": "...", "device": "...", "platform": "..." } ]
}
```

Every category is present (empty where there is no data); `logs` holds the
recent visits from the Redis zset.

## Misc
## Misc

### GET /lang

Returns the viewer's language/country code as plain text (e.g. `RU`).

### POST /newsletter_register

Subscribe to the newsletter.

| Field | Type | Required | Description |
|---|---|---|---|
| `mail` | string | yes | Email address |

### POST /subscribed

Record a PayPal subscription ID after payment approval (pay-what-you-want flow).
Sent as JSON or form field:

| Field | Type | Required | Description |
|---|---|---|---|
| `subscription_id` | string | yes | PayPal subscription ID |

## Errors

Failed requests return JSON errors: `{ "detail": "..." }` for a single
message (e.g. `"no such user"`, `"wrong password"`, `"user already exists"`)
or `{ "<field>": ["..."] }` for serializer validation errors. Unauthenticated
requests answer 401.
