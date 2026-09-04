import { defineConfig } from "@playwright/test";

// Tests run against the site served by `docker compose up` (the frontend
// nginx on :8080). If nothing is listening, the config starts the compose
// stack itself (frontend incl. its build service) and tears it down after.
export default defineConfig({
  testDir: "./tests",
  timeout: 30_000,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 2 : undefined,
  use: {
    baseURL: "http://localhost:8080",
    trace: "retain-on-failure",
  },
  webServer: {
    command: "docker compose up --wait frontend",
    url: "http://localhost:8080",
    reuseExistingServer: true,
    timeout: 300_000,
    stdout: "ignore",
    stderr: "pipe",
  },
});