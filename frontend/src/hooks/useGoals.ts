import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as goalApi from '../services/goalApi';
import { GoalCreate, GoalUpdate, GoalLinkCreate } from '../types/goal';

export const useGoals = () => {
    return useQuery({
        queryKey: ['goals'],
        queryFn: goalApi.getGoals,
    });
};

export const useGoal = (id: string | null) => {
    return useQuery({
        queryKey: ['goal', id],
        queryFn: () => goalApi.getGoal(id!),
        enabled: !!id,
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

export const useCreateGoalLink = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ goalId, link }: { goalId: string; link: GoalLinkCreate }) =>
            goalApi.createGoalLink(goalId, link),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['goal', variables.goalId] });
        },
    });
};

export const useDeleteGoalLink = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ goalId, linkId }: { goalId: string; linkId: string }) =>
            goalApi.deleteGoalLink(goalId, linkId),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['goal', variables.goalId] });
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
