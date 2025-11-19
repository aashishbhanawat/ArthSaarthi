import { APIRequestContext, Page } from '@playwright/test';

export async function login(page: Page) {
  const adminUser = {
    email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
    password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
  };

  await page.goto('/');
  await page.getByLabel('Email address').fill(adminUser.email);
  await page.getByLabel('Password').fill(adminUser.password);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.waitForURL('/dashboard');
}

export async function createUser(request: APIRequestContext, { email, password, fullName }) {
  const response = await request.post('/api/v1/users/', {
    data: {
      email,
      password,
      full_name: fullName,
      is_admin: false,
    },
  });
  return response;
}
