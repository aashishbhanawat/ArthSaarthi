import apiClient from './api';
import { User, UserCreate, UserUpdate } from '../types/user';

export const getUsers = async (): Promise<User[]> => {
  const response = await apiClient.get('/api/v1/users/');
  return response.data;
};

export const createUser = async (userData: UserCreate): Promise<User> => {
  const response = await apiClient.post('/api/v1/users/', userData);
  return response.data;
};

export const updateUser = async (
  userId: number,
  userData: UserUpdate
): Promise<User> => {
  const response = await apiClient.put(`/api/v1/users/${userId}`, userData);
  return response.data;
};

export const deleteUser = async (userId: number): Promise<User> => {
  const response = await apiClient.delete(`/api/v1/users/${userId}`);
  return response.data;
};