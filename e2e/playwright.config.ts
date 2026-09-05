import { defineConfig } from "@playwright/test";

// Tests run against the gateway on :80 under the local hostname
// `counterdev` (frontend), with `t.counterdev` used to ingest tracking data
// and `sync` moving the data from Redis into Postgres. The host-resolver
// rules map the hostnames to 127.0.0.1, so /etc/hosts entries are not
// required to run the suite. If nothing is listening, the config starts the
// compose stack itself and tears it down after; it reuses a running one
// otherwise.
export default defineConfig({
  testDir: "./tests",
  timeout: 60_000,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 2 : undefined,
  use: {
    baseURL: "http://counterdev",
    launchOptions: {
      args: ["--host-resolver-rules=MAP counterdev 127.0.0.1,MAP t.counterdev 127.0.0.1,MAP api.counterdev 127.0.0.1"],
    },
    // Deterministic dates: the browser reports UTC, the tracker records
    // visits with utcoffset=0, so both agree on "today".
    timezoneId: "UTC",
    trace: "retain-on-failure",
  },
  webServer: {
    command: "docker compose up --wait gateway sync",
    url: "http://counterdev",
    reuseExistingServer: true,
    timeout: 300_000,
    stdout: "ignore",
    stderr: "pipe",
  },
});