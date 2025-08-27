import apiClient from './api';
import { User, UserPasswordChange } from '../types/user';

interface UserUpdateMePayload {
  full_name: string;
}

export const updateMe = async (userData: UserUpdateMePayload): Promise<User> => {
  const response = await apiClient.put('/api/v1/users/me', userData);
  return response.data;
};

export const updatePassword = async (passwordData: UserPasswordChange): Promise<void> => {
  await apiClient.post('/api/v1/auth/me/change-password', passwordData);
};
