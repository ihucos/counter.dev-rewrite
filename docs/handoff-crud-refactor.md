# Handoff: consolidate the backend API into resource CRUD

You are working in the repo at the repo root (`counter.dev-rewrite`), branch
`drf-rewrite`. The full design rationale lives in `docs/proposal-crud.html`
— read it first. Your task is to implement that proposal. Summary of the
decisions already made (do not relitigate them):

## Target API

Replace 8 flat `@api_view` endpoints in `services/backend/core/api.py` with
two DRF ViewSets registered on one `SimpleRouter` (all trailing-slashless,
matching the existing router config):

- **`AccountViewSet`** — singleton resource for the signed-in account, no pk:
  - `GET /account` — current account. Replaces `/me`; keep the 401-means-not-signed-in contract.
  - `PUT /account` — updates email, timezone, selected site, date range, and the sites list (the `account_edit` behavior).
  - `DELETE /account` — deletes the account (replaces `POST /delete_user`).
- **`/account/share_token`** — nested subresource of the account (replaces `POST /reset_token` and `POST /delete_token`):
  - `GET` — current token; `PUT` — rotate; `DELETE` — revoke.
- **`SiteViewSet`** — extend the existing read-only ViewSet to full CRUD:
  - `DELETE /sites/{name}` replaces `POST /delete_site`. Deleting by name is
    explicit (today `delete_site` deletes whatever is selected in prefs);
    the SPA then updates the selection via `PUT /account`.

Model change: promote the dashboard prefs out of `User.prefs` (JSONField)
into real, constrained columns on the `counter.User` model:

- `date_range` — choice field over the existing `RANGES` values
  (`day yesterday last7 last30 month year all`), with a default.
- `selected_site` — plain field (optionally an FK to `Host`; a name string is
  acceptable — pick one and justify briefly in the commit message).
- Migration must backfill from existing `prefs["range"]` / `prefs["site"]`.
- The rest of `prefs` (`usesites`, `subscription_id`) stays as a JSON blob.

Deleted endpoints (SPA callsites need updating):
`me`, `account_edit`, `delete_user`, `reset_token`, `delete_token`,
`set_pref_site`, `set_pref_range`, `delete_site`.

Kept as-is (do not convert): `/login /logout /register /recover` (session
lifecycle, and `/logout` redirects to the referer), `/query` (computed
analytics read), `/feedback /newsletter_register /subscribed /lang`.

## Conventions to follow

- Response payloads are serialized through the same serializers referenced by
  `@extend_schema(responses=...)` (no hand-built dicts) — see `me_view` /
  `query_view` in `core/api.py` for the pattern.
- Keep the existing authentication flow (`core/authentication.py`:
  `AccountAuthentication`, session cookie + guest/share `?user&token` +
  `?demo=1`) untouched. Its drf-spectacular extension lives in
  `core/authentication.py`.
- Swagger docs are already wired (`/api/docs/`); keep the schema
  error-free (`manage.py spectacular` must emit no errors).
- Style: match the existing comment density; comments only for constraints
  the code can't show.

## Verification

- `uv run pytest services/backend` from the repo root (or
  `uv run --project services/backend pytest services/backend`) — all tests
  must pass; update `core/tests/views/` and `counter/tests/test_auth.py`
  for the new URLs/methods.
- `uv run --project services/backend python services/backend/manage.py spectacular`
  must generate the schema with zero errors.
- Frontend SPA: update fetch URLs/methods in `services/frontend` wherever the
  deleted endpoints were called (navbar sign-out, setup page, share panel,
  dashboard prefs). Grep for the endpoint names.
- Do not commit until asked.