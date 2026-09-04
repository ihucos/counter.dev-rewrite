import { defineConfig } from "@playwright/test";

// Tests run against the site served by `docker compose up` (the frontend
// nginx on :8080). The dashboard tests additionally ingest tracking data via
// the tracker service on :8001, so it and the `sync` service (which moves
// the data from Redis into Postgres) must run as well. If nothing is
// listening, the config starts the compose stack itself and tears it down
// after; it reuses a running one otherwise.
export default defineConfig({
  testDir: "./tests",
  timeout: 60_000,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 2 : undefined,
  use: {
    baseURL: "http://localhost:8080",
    // Deterministic dates: the browser reports UTC, the tracker records
    // visits with utcoffset=0, so both agree on "today".
    timezoneId: "UTC",
    trace: "retain-on-failure",
  },
  webServer: {
    command: "docker compose up --wait frontend tracker sync",
    url: "http://localhost:8080",
    reuseExistingServer: true,
    timeout: 300_000,
    stdout: "ignore",
    stderr: "pipe",
  },
});