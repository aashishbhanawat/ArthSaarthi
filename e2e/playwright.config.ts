import { defineConfig } from '@playwright/test';

export default defineConfig({
  // Look for test files in the "tests" directory, relative to this configuration file.
  testDir: './tests',
  // A global setup file to run before all tests.
  globalSetup: require.resolve('./global.setup.ts'),
  /* Run tests in files in parallel */
  fullyParallel: false, // Tests within a file can run in parallel, but files will not.
  workers: 1, // Opt out of parallel execution by setting workers to 1
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://frontend:3000',
    trace: 'on-first-retry',
  },
  timeout: 30 * 1000, // 30 seconds
});