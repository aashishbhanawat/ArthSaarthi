import { defineConfig } from '@playwright/test';

const baseURL = process.env.E2E_BASE_URL || 'http://frontend:3000';

export default defineConfig({
  // Look for test files in the "tests" directory, relative to this configuration file.
  testDir: './tests',
  // A global setup file to run before all tests.
  globalSetup: require.resolve('./global.setup.ts'),
  /* Run tests in files in parallel */
  fullyParallel: false, // Tests within a file can run in parallel, but files will not.
  workers: 1, // Opt out of parallel execution by setting workers to 1
  expect: {
    timeout: 10 * 1000, // 10 seconds for assertions
  },
  use: {
    baseURL,
    trace: 'on',
    storageState: {
      cookies: [],
      origins: [
        {
          origin: new URL(baseURL).origin,
          localStorage: [
            {
              name: 'skip_risk_redirect',
              value: 'true',
            },
          ],
        },
      ],
    },
  },
  timeout: 30 * 1000, // 30 seconds per test
});