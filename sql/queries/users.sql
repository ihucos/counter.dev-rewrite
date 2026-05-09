-- name: CreateUser :one
INSERT INTO users (id, username, email, password_hash, timezone, prefs)
VALUES ($1, $2, $3, $4, $5, $6)
RETURNING *;

-- name: GetUserByID :one
SELECT * FROM users WHERE id = $1;

-- name: GetUserByUsername :one
SELECT * FROM users WHERE username = $1;

-- name: GetUserByEmail :one
SELECT * FROM users WHERE email = $1;

-- name: UpdatePassword :exec
UPDATE users SET password_hash = $2 WHERE id = $1;

-- name: UpdateEmail :exec
UPDATE users SET email = $2 WHERE id = $1;

-- name: UpdateTimezone :exec
UPDATE users SET timezone = $2 WHERE id = $1;

-- name: UpdatePrefs :exec
UPDATE users SET prefs = $2 WHERE id = $1;

-- name: SetRecoveryToken :exec
UPDATE users SET recovery_token = $2, recovery_token_expires_at = $3 WHERE id = $1;

-- name: GetUserByRecoveryToken :one
SELECT * FROM users
WHERE recovery_token = $1 AND recovery_token_expires_at > NOW();

-- name: ClearRecoveryToken :exec
UPDATE users
SET recovery_token = NULL, recovery_token_expires_at = NULL
WHERE id = $1;

-- name: DeleteUser :exec
DELETE FROM users WHERE id = $1;
