import apiClient from './api';
import { User, UserUpdateMe, UserPasswordChange } from '../types/user';
import { Msg } from '../types/msg';

export const updateProfile = async (data: UserUpdateMe): Promise<User> => {
  const response = await apiClient.put<User>('/api/v1/users/me', data);
  return response.data;
};

export const changePassword = async (data: UserPasswordChange): Promise<Msg> => {
  const response = await apiClient.post<Msg>('/api/v1/auth/me/change-password', data);
  return response.data;
};
