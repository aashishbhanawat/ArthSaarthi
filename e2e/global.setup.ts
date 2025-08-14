import { request, expect } from '@playwright/test';

const adminUser = {
  email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
  password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

async function globalSetup() {
  const baseURL = process.env.E2E_BASE_URL || 'http://frontend:3000';
  console.log(`Using base URL: ${baseURL}`);

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
  const adminSetupResponse = await requestContext.post('/api/v1/auth/setup', {
    data: {
      full_name: 'Admin User',
      email: adminUser.email,
      password: adminUser.password,
    },
  });
  expect(adminSetupResponse.ok()).toBeTruthy();
  console.log('Global setup complete: Admin user created.');

  await requestContext.dispose();
}

export default globalSetup;