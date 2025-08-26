import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as goalApi from '../services/goalApi';
import { GoalCreate, GoalUpdate } from '../types/goal';

export const useGoals = () => {
    return useQuery({
        queryKey: ['goals'],
        queryFn: goalApi.getGoals,
    });
};

export const useCreateGoal = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (goal: GoalCreate) => goalApi.createGoal(goal),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['goals'] });
        },
    });
};

export const useUpdateGoal = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ id, goal }: { id: string; goal: GoalUpdate }) =>
            goalApi.updateGoal(id, goal),
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
