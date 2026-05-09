CREATE TABLE users (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    timezone INTEGER NOT NULL DEFAULT 0,
    prefs JSONB NOT NULL DEFAULT '{}'::jsonb,
    recovery_token TEXT,
    recovery_token_expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_recovery_token ON users(recovery_token) WHERE recovery_token IS NOT NULL;

CREATE TABLE sites (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    domain TEXT NOT NULL,
    allowed_domains TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    filter_allowed_domains BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, domain)
);

CREATE INDEX idx_sites_user_id ON sites(user_id);

CREATE TABLE counts (
    site_id BIGINT NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    metric TEXT NOT NULL,
    value TEXT NOT NULL,
    count BIGINT NOT NULL DEFAULT 0,
    PRIMARY KEY (site_id, date, metric, value)
);

CREATE INDEX idx_counts_site_date ON counts(site_id, date);

---- create above / drop below ----

DROP TABLE IF EXISTS counts;
DROP TABLE IF EXISTS sites;
DROP TABLE IF EXISTS users;
