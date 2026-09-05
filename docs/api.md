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

### PUT /account

Update account settings. Every field is optional; absent fields keep their
current value, so the SPA's site/range selectors PUT those alone.

| Field | Type | Required | Description |
|---|---|---|---|
| `utcoffset` | integer | no | Client UTC offset in minutes |
| `usesites` | boolean | no | Whether the multi-site selector is shown |
| `sites` | string | no | Newline-separated list of site domains |
| `mail` | string | no | Email address |
| `site` | string | no | Selected site name (dashboard prefs) |
| `range` | string | no | Selected time range: `day`, `yesterday`, `last7`, `last30`, `month`, `year`, `all` |

### DELETE /account

Delete the account and all its data. Requires no body.

### GET /account/share_token

The account's current share token (`{ "token": "..." }`).

### PUT /account/share_token

Rotate the share token (invalidates previously issued URLs). Returns the
token used for guest access (`?user=<id>&token=<token>`).

### DELETE /account/share_token

Revoke the share token. Requires no body.

### POST /feedback

Send product feedback.

| Field | Type | Required | Description |
|---|---|---|---|
| `feedback` | string | yes | Message |
| `contact` | string | no | Reply email address |

## Sites

`GET /sites` and `GET /sites/<name>` expose the sites resource (`Host`
model) in name order. The list is the source of truth for which sites an
account has (setup-vs-dashboard routing and the site selector).

```json
[ { "name": "example.com", "hide": true }, ... ]
```

### DELETE /sites/\<name\>

Delete a site by name and all its data (explicit, unlike the old
`delete_site` which deleted whatever was selected). Requires no body.

## Dashboard data

All three endpoints serve a signed-in session, guest/share access via
`?user=<uuid>&token=<token>`, or read-only demo access via `?demo=1`. A
missing or invalid account answers **401** ("not signed in"); the SPA
redirects to the welcome page accordingly.

### GET /account

The signed-in user's state: session bootstrap, share-account panel, and
demo/guest flags. `site` and `range` are dashboard prefs surfaced inside
`prefs`.

```json
{
  "user": { "id": "...", "uuid": "...", "token": "...", "prefs": {}, "timezone": 0 },
  "meta": { "utcoffset": 0, "sessionless": false, "demo": false }
}
```

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
