-- name: ListSitesByUser :many
SELECT * FROM sites WHERE user_id = $1 ORDER BY domain;

-- name: GetSiteByID :one
SELECT * FROM sites WHERE id = $1;

-- name: GetSiteByDomain :one
SELECT * FROM sites WHERE user_id = $1 AND domain = $2;

-- name: CreateSite :one
INSERT INTO sites (user_id, domain)
VALUES ($1, $2)
ON CONFLICT (user_id, domain) DO UPDATE SET domain = EXCLUDED.domain
RETURNING *;

-- name: UpdateSiteAllowedDomains :exec
UPDATE sites
SET allowed_domains = $2, filter_allowed_domains = $3
WHERE id = $1 AND user_id = $4;

-- name: DeleteSite :exec
DELETE FROM sites WHERE id = $1 AND user_id = $2;
