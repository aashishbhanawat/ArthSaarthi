import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as goalApi from '../services/goalApi';
import { GoalCreate, GoalUpdate } from '../types/goal';

export const useGoals = () => {
  return useQuery({
    queryKey: ['goals'],
    queryFn: goalApi.getGoals,
  });
};

export const useGoal = (id: string | undefined) => {
  return useQuery({
    queryKey: ['goal', id],
    queryFn: () => goalApi.getGoal(id!),
    enabled: !!id,
  });
};

export const useCreateGoal = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: GoalCreate) => goalApi.createGoal(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['goals'] });
    },
  });
};

export const useUpdateGoal = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: GoalUpdate }) =>
      goalApi.updateGoal(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['goals'] });
      queryClient.invalidateQueries({ queryKey: ['goal', variables.id] });
    },
  });
};

export const useDeleteGoal = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => goalApi.deleteGoal(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['goals'] });
    },
  });
};
