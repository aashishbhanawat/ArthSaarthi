import { chromium, request, expect } from '@playwright/test';

async function globalSetup() {
  // For API requests made in this global setup, we need to target the backend directly.
  const baseURL = process.env.E2E_BACKEND_URL || 'http://localhost:8008';
  console.log(`Global setup using backend URL: ${baseURL}`);

  const requestContext = await request.newContext({
    baseURL: baseURL,
  });

  // 1. Wait for the backend to be ready by retrying the reset-db call
  let retries = 5;
  while (retries > 0) {
    try {
      const resetResponse = await requestContext.post('/api/v1/testing/reset-db');
      if (resetResponse.ok()) {
        console.log('Database reset successfully.');
        break; // Success
      }
    } catch (error) {
      console.log(`Waiting for backend... Retries left: ${retries - 1}`);
      retries--;
      if (retries === 0) {
        throw new Error('Backend did not become available in time.');
      }
      await new Promise(res => setTimeout(res, 2000)); // Wait 2 seconds before retrying
    }
  }

  // 2. Create the initial admin user
  const adminUser = {
    email: process.env.VITE_TEST_ADMIN_EMAIL,
    password: process.env.VITE_TEST_ADMIN_PASSWORD,
    is_admin: true,
  };
  const adminSetupResponse = await requestContext.post('/api/v1/users/', {
    data: adminUser,
  });
  expect(adminSetupResponse.ok()).toBeTruthy();
  console.log('Global setup complete: Admin user created.');

  await requestContext.dispose();
}

export default globalSetup;