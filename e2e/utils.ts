import { APIRequestContext } from '@playwright/test';

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
