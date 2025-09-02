import { request, expect } from '@playwright/test';

const adminUser = {
  email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
  password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

async function globalSetup() {
  // For API requests made in this global setup, we need to target the backend directly.
  const baseURL = process.env.E2E_BACKEND_URL || 'http://backend:8000';
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
  const adminSetupResponse = await requestContext.post('/api/v1/auth/setup', {
    data: {
      full_name: 'Admin User',
      email: adminUser.email,
      password: adminUser.password,
    },
  });
  expect(adminSetupResponse.ok()).toBeTruthy();
  console.log('Global setup complete: Admin user created.');

  // 3. Login as admin to get a token for seeding
  const loginResponse = await requestContext.post('/api/v1/auth/login', {
    form: {
      username: adminUser.email,
      password: adminUser.password,
    },
  });
  expect(loginResponse.ok()).toBeTruthy();
  const { access_token } = await loginResponse.json();

  // 4. Seed some assets
  const assetsToSeed = [
    { ticker_symbol: 'AAPL', name: 'Apple Inc.', asset_type: 'Stock', currency: 'USD', exchange: 'NASDAQ' },
    { ticker_symbol: 'GOOGL', name: 'Alphabet Inc.', asset_type: 'Stock', currency: 'USD', exchange: 'NASDAQ' },
    { ticker_symbol: 'MSFT', name: 'Microsoft Corporation', asset_type: 'Stock', currency: 'USD', exchange: 'NASDAQ' },
  ];
  for (const asset of assetsToSeed) {
    const createAssetResponse = await requestContext.post('/api/v1/assets/', {
      headers: {
        Authorization: `Bearer ${access_token}`,
      },
      // Send the full, correct payload
      data: asset,
    });
    // It might fail if the asset already exists, which is fine for setup
    if (!createAssetResponse.ok()) {
      console.log(`Could not create asset ${asset.ticker_symbol}, it might already exist.`);
    }
  }
  console.log(`Global setup complete: Attempted to seed ${assetsToSeed.length} assets.`);

  await requestContext.dispose();
}

export default globalSetup;