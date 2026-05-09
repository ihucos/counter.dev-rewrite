package config

import (
	"log"
	"os"
	"strings"
)

type Config struct {
	DatabaseURL    string
	Port           string
	SessionSecret  string
	IngestSecret   string
	CookieDomain   string
	CookieSecure   bool
	AllowedOrigins []string
}

func Load() *Config {
	cfg := &Config{
		DatabaseURL:    must("DATABASE_URL"),
		Port:           getenv("PORT", "8080"),
		SessionSecret:  must("SESSION_SECRET"),
		IngestSecret:   must("INGEST_SECRET"),
		CookieDomain:   getenv("COOKIE_DOMAIN", ""),
		CookieSecure:   getenv("COOKIE_SECURE", "true") == "true",
		AllowedOrigins: splitCSV(getenv("ALLOWED_ORIGINS", "https://counter.dev")),
	}
	return cfg
}

func getenv(key, fallback string) string {
	if v, ok := os.LookupEnv(key); ok {
		return v
	}
	return fallback
}

func must(key string) string {
	v, ok := os.LookupEnv(key)
	if !ok || v == "" {
		log.Fatalf("missing required env var %s", key)
	}
	return v
}

func splitCSV(s string) []string {
	parts := strings.Split(s, ",")
	out := make([]string, 0, len(parts))
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p != "" {
			out = append(out, p)
		}
	}
	return out
}
