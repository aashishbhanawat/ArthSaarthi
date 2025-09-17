import apiClient from './api';
import { User, UserCreate, UserUpdate } from '../types/user';
import { HistoricalInterestRate, HistoricalInterestRateCreate, HistoricalInterestRateUpdate } from '../types/interestRate';

export const getUsers = async (): Promise<User[]> => {
  const response = await apiClient.get('/api/v1/users/');
  return response.data;
};

export const createUser = async (userData: UserCreate): Promise<User> => {
  const response = await apiClient.post('/api/v1/users/', userData);
  return response.data;
};

export const updateUser = async (
  userId: string,
  userData: UserUpdate
): Promise<User> => {
  const response = await apiClient.put(`/api/v1/users/${userId}`, userData);
  return response.data;
};

export const deleteUser = async (userId: string): Promise<User> => {
  const response = await apiClient.delete(`/api/v1/users/${userId}`);
  return response.data;
};

// --- Interest Rate Management (Admin) ---
export const getInterestRates = async (): Promise<HistoricalInterestRate[]> => {
  const response = await apiClient.get('/api/v1/admin/interest-rates/');
  return response.data;
};

export const createInterestRate = async (rateData: HistoricalInterestRateCreate): Promise<HistoricalInterestRate> => {
  const response = await apiClient.post('/api/v1/admin/interest-rates/', rateData);
  return response.data;
};

export const updateInterestRate = async (
  rateId: string,
  rateData: HistoricalInterestRateUpdate
): Promise<HistoricalInterestRate> => {
  const response = await apiClient.put(`/api/v1/admin/interest-rates/${rateId}`, rateData);
  return response.data;
};

export const deleteInterestRate = async (rateId: string): Promise<{ msg: string }> => {
  const response = await apiClient.delete(`/api/v1/admin/interest-rates/${rateId}`);
  return response.data;
};