import apiClient from './api';
import { UserPasswordChange, UserUpdateMe } from '../types/user';

export const updateProfile = async (userData: UserUpdateMe) => {
  const response = await apiClient.put('/api/v1/users/me', userData);
  return response.data;
};

export const changePassword = async (passwordData: UserPasswordChange) => {
  const response = await apiClient.post('/api/v1/auth/me/change-password', passwordData);
  return response.data;
};
