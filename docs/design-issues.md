# Design issues & known gaps

Found while building the e2e suite; each needs a decision or deliberate
follow-up, not a quick fix.

## Tracking id: uuid vs. username

The tracking code sends `data-id` = **uuid**, but the backend keys on
**username** (`sync.py` user lookup, visit log key), so uuid-keyed visits are
silently dropped. Pick one identifier and align tracking code, `sync.py` and
the log key; the e2e tests ingest with the username.

## Backend doesn't send what the dashboard expects

The frontend still expects the old counter.dev protocol: the `push-archive`
event (never sent — crashed every dump, now patched to fall back to the
backend's `last7`/`last30`), plus `meta.sessionless`, `meta.demo` and
`user.token`, which are read by components but never included in `/dump`.

## Crashes on empty ranges

Sites without data in a range return `{}` buckets; `dynamics.js`,
`screens.js`, `base/pwyw.js` and the navbar assume all categories exist and
throw, aborting the whole `redraw` loop. `_base.js` `normalizeVisits` shows
the fix pattern; until fixed, new accounts render incompletely and the full
dashboard-rendering e2e test stays removed.

## utcoffset unit mismatch

The frontend and tracker treat utcoffset as **hours**, the backend
(`_local_date`, `User.timezone`) as **minutes**. Around midnight this can
bucket visits into the wrong day away from UTC.