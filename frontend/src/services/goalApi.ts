import apiClient from './api';
import { Goal, GoalCreate, GoalUpdate } from '../types/goal';

export const getGoals = async (): Promise<Goal[]> => {
  const response = await apiClient.get<Goal[]>('/api/v1/goals/');
  return response.data;
};

export const getGoal = async (id: string): Promise<Goal> => {
  const response = await apiClient.get<Goal>(`/api/v1/goals/${id}`);
  return response.data;
};

export const createGoal = async (data: GoalCreate): Promise<Goal> => {
  const response = await apiClient.post<Goal>('/api/v1/goals/', data);
  return response.data;
};

export const updateGoal = async (id: string, data: GoalUpdate): Promise<Goal> => {
  const response = await apiClient.put<Goal>(`/api/v1/goals/${id}`, data);
  return response.data;
};

export const deleteGoal = async (id: string): Promise<void> => {
  await apiClient.delete(`/api/v1/goals/${id}`);
};
