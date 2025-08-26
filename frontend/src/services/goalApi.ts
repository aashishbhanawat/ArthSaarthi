import apiClient from './api';
import { Goal, GoalCreate, GoalUpdate } from '../types/goal';
import { Msg } from '../types/msg';

export const getGoals = async (): Promise<Goal[]> => {
    const response = await apiClient.get<Goal[]>('/api/v1/goals/');
    return response.data;
};

export const createGoal = async (goal: GoalCreate): Promise<Goal> => {
    const response = await apiClient.post<Goal>('/api/v1/goals/', goal);
    return response.data;
};

export const updateGoal = async (id: string, goal: GoalUpdate): Promise<Goal> => {
    const response = await apiClient.put<Goal>(`/api/v1/goals/${id}`, goal);
    return response.data;
};

export const deleteGoal = async (id: string): Promise<Msg> => {
    const response = await apiClient.delete<Msg>(`/api/v1/goals/${id}`);
    return response.data;
};
