import { defineConfig } from "@playwright/test";

// Dùng Chromium cài sẵn của môi trường (không chạy `playwright install`).
const executablePath = process.env.PW_CHROMIUM ?? "/opt/pw-browsers/chromium";

export default defineConfig({
  testDir: "e2e",
  timeout: 120_000,
  expect: { timeout: 60_000 },
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://127.0.0.1:8000",
    launchOptions: { executablePath },
    viewport: { width: 1366, height: 900 },
  },
  webServer: process.env.E2E_BASE_URL
    ? undefined
    : {
        command: "npm run build && cd ../backend && .venv/bin/uvicorn curriculum_planner.api.app:app --port 8000",
        url: "http://127.0.0.1:8000/api/health",
        reuseExistingServer: true,
        timeout: 120_000,
      },
});
