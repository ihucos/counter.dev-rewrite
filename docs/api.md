# API

All endpoints are served by the backend behind `api.counter.dev` (locally
`api.counterdev`). The SPA resolves the API host at runtime via `apiBase()` in
`static/js/utils.js`, and the backend's `CorsMiddleware` grants the SPA origins
cross-origin access with credentials. Authentication is a session cookie managed
by the server. Guest/share access to a dashboard uses
`?user=<id>&token=<token>` query parameters instead of a session.

All names are lowercase snake_case.

## Authentication & account

### POST /login

Sign in.

| Field | Type | Required | Description |
|---|---|---|---|
| `user` | string | yes | Username |
| `password` | string | yes | Password |

On success the session cookie is set.

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

### GET /dump (Server-Sent Events)

Streams the full account state: sites, user record, preferences, and visit data.
Query parameters:

| Parameter | Type | Description |
|---|---|---|
| `utcoffset` | integer | Client UTC offset in minutes, used to bucket visits by local time |
| (any) | — | Custom range requests additionally pass `from` and `to` dates |

Each message is a JSON object:

```json
{ "type": "<event type>", "payload": { ... } }
```

Event types include `dump` (full state), `nouser` (no signed-in user), and
`signedin`.

### GET /?from=\<date\>&to=\<date\>

Dashboard view restricted to a custom date range (`from`/`to` dates).

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

Failed requests return the error message in the response body as plain text.
