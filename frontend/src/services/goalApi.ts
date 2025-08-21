import apiClient from "./api";
import { Goal, GoalCreate, GoalUpdate, GoalLink, GoalLinkCreate } from "../types/goal";

export const getGoals = async (): Promise<Goal[]> => {
  const response = await apiClient.get<Goal[]>("/api/v1/goals/");
  return response.data;
};

export const createGoal = async (data: GoalCreate): Promise<Goal> => {
  const response = await apiClient.post<Goal>("/api/v1/goals/", data);
  return response.data;
};

export const updateGoal = async (
  id: string,
  data: GoalUpdate
): Promise<Goal> => {
  const response = await apiClient.put<Goal>(`/api/v1/goals/${id}`, data);
  return response.data;
};

export const deleteGoal = async (id: string): Promise<void> => {
  await apiClient.delete(`/api/v1/goals/${id}`);
};

export const createGoalLink = async (
  goalId: string,
  data: GoalLinkCreate
): Promise<GoalLink> => {
  const response = await apiClient.post<GoalLink>(
    `/api/v1/goals/${goalId}/links`,
    data
  );
  return response.data;
};

export const deleteGoalLink = async (
  goalId: string,
  linkId: string
): Promise<void> => {
  await apiClient.delete(`/api/v1/goals/${goalId}/links/${linkId}`);
};
